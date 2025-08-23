#!/usr/bin/env python3
import os
import time
import json
from typing import Optional, Dict, List, Set
from datetime import datetime, timezone

import httpx
import psycopg
import redis

# -----------------------------
# Configuration (via variables d'environnement)
# -----------------------------
DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@postgres:5432/cryptoviz")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Ex: "BTCUSDT,ETHUSDT,SOLUSDT,ADAUSDT,AVAXUSDT"
SYMBOLS = [s.strip().upper() for s in os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT").split(",") if s.strip()]

# Périodicité des bougies Coinbase (1 minute)
GRANULARITY_SECONDS = int(os.getenv("GRANULARITY_SECONDS", "60"))

# Délai entre deux symboles (éviter le rate limit)
SLEEP_BETWEEN_SYMBOLS = float(os.getenv("SLEEP_BETWEEN_SYMBOLS", "0.25"))

# Délai entre deux boucles complètes (boucle = 1 passage sur tous les symboles)
LOOP_SLEEP = float(os.getenv("LOOP_SLEEP", "5"))

# Rafraîchir la liste des produits Coinbase toutes les N boucles
REFRESH_PRODUCTS_EVERY = int(os.getenv("REFRESH_PRODUCTS_EVERY", "60"))

# -----------------------------
# Constantes Coinbase
# -----------------------------
CB_BASE = "https://api.exchange.coinbase.com"
CB_PRODUCTS = f"{CB_BASE}/products"                                 # GET -> liste des paires
CB_CANDLES  = f"{CB_BASE}/products/{{pair}}/candles"                # GET candles [time, low, high, open, close, volume]
CB_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "cryptoviz/0.1 (+local)"
}

# -----------------------------
# DB: créer la table/hypertable si besoin
# -----------------------------
def ensure_tables():
    with psycopg.connect(DSN, autocommit=True) as con, con.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS candles(
          symbol  TEXT NOT NULL,
          ts      TIMESTAMPTZ NOT NULL,
          open    NUMERIC NOT NULL,
          high    NUMERIC NOT NULL,
          low     NUMERIC NOT NULL,
          close   NUMERIC NOT NULL,
          volume  NUMERIC NOT NULL,
          PRIMARY KEY(symbol, ts)
        );
        """)
        # Timescale
        cur.execute("SELECT create_hypertable('candles','ts', if_not_exists=>TRUE);")

def upsert_candle(cur, internal_symbol: str, row: List[float]):
    """
    Coinbase renvoie des lignes: [time, low, high, open, close, volume]
    """
    ts = datetime.fromtimestamp(row[0], tz=timezone.utc)
    low, high, open_, close, vol = map(float, (row[1], row[2], row[3], row[4], row[5]))
    cur.execute("""
      INSERT INTO candles(symbol, ts, open, high, low, close, volume)
      VALUES (%s, %s, %s, %s, %s, %s, %s)
      ON CONFLICT (symbol, ts) DO UPDATE
      SET open=excluded.open, high=excluded.high, low=excluded.low,
          close=excluded.close, volume=excluded.volume
    """, (internal_symbol, ts, open_, high, low, close, vol))
    return ts, close

# -----------------------------
# Coinbase helpers
# -----------------------------
def fetch_products(client: httpx.Client) -> Set[str]:
    """
    Récupère la liste des produits disponibles sur Coinbase (ex: 'BTC-USD', 'SOL-USD', ...)
    Retourne un set des ids (strings).
    """
    r = client.get(CB_PRODUCTS)
    r.raise_for_status()
    data = r.json()
    ids = {p.get("id") for p in data if isinstance(p, dict) and p.get("id")}
    return ids

def internal_to_coinbase_pair(internal_sym: str, available_pairs: Set[str]) -> Optional[str]:
    """
    Mappe un symbole interne style 'BTCUSDT' -> 'BTC-USD' si disponible.
    Essaie plusieurs quote currencies dans l'ordre: USD, USDC, EUR.
    """
    base = None
    if internal_sym.endswith("USDT"):
        base = internal_sym[:-4]  # BTCUSDT -> BTC
    elif internal_sym.endswith("USD"):
        base = internal_sym[:-3]  # BTCUSD -> BTC
    elif internal_sym.endswith("USDC"):
        base = internal_sym[:-4]  # BTCUSDC -> BTC
    else:
        # Format non supporté -> on ignore
        return None

    candidates = [f"{base}-USD", f"{base}-USDC", f"{base}-EUR"]
    for c in candidates:
        if c in available_pairs:
            return c
    return None  # pas listé sur Coinbase

def fetch_latest_coinbase_candle(client: httpx.Client, pair: str, granularity: int) -> Optional[List[float]]:
    """
    Récupère les bougies Coinbase pour 'pair' avec la granularité demandée.
    Coinbase ne prend pas 'limit'; on récupère le lot par défaut et on prend la plus récente.
    """
    r = client.get(CB_CANDLES.format(pair=pair), params={"granularity": granularity})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    arr = r.json()
    if not arr:
        return None
    # Les bougies peuvent ne pas être triées -> on prend celle avec time max
    latest = max(arr, key=lambda x: x[0])
    return latest

# -----------------------------
# Main loop
# -----------------------------
def main():
    print(f"[init] DSN={DSN}")
    print(f"[init] REDIS_URL={REDIS_URL}")
    print(f"[init] symbols={SYMBOLS}")
    print(f"[init] granularity={GRANULARITY_SECONDS}s, loop_sleep={LOOP_SLEEP}s, between_symbols={SLEEP_BETWEEN_SYMBOLS}s")
    ensure_tables()

    r = redis.from_url(REDIS_URL, decode_responses=True)

    # Client HTTP réutilisé
    client = httpx.Client(timeout=15, headers=CB_HEADERS)

    # Cache mapping symbol interne -> pair coinbase
    mapping: Dict[str, Optional[str]] = {s: None for s in SYMBOLS}

    # Charger la liste des produits disponibles
    try:
        products = fetch_products(client)
        print(f"[init] coinbase products: {len(products)} disponibles")
    except Exception as e:
        print(f"[init] error fetching products: {e}")
        products = set()

    loops = 0
    while True:
        loops += 1

        # Rafraîchir périodiquement la liste des produits (nouvelles listings, etc.)
        if loops % REFRESH_PRODUCTS_EVERY == 0:
            try:
                products = fetch_products(client)
                print(f"[refresh] coinbase products: {len(products)}")
            except Exception as e:
                print(f"[refresh] error fetching products: {e}")

        with psycopg.connect(DSN, autocommit=True) as con, con.cursor() as cur:
            for internal_sym in SYMBOLS:
                try:
                    # Résoudre ou re-résoudre la pair coinbase si inconnue
                    pair = mapping.get(internal_sym)
                    if not pair:
                        pair = internal_to_coinbase_pair(internal_sym, products)
                        mapping[internal_sym] = pair
                        if not pair:
                            print(f"[{internal_sym}] not available on Coinbase (USD/USDC/EUR) -> skipping")
                            time.sleep(SLEEP_BETWEEN_SYMBOLS)
                            continue

                    latest = fetch_latest_coinbase_candle(client, pair, GRANULARITY_SECONDS)
                    if not latest:
                        print(f"[{internal_sym}] empty/404 for pair {pair} -> skip")
                        time.sleep(SLEEP_BETWEEN_SYMBOLS)
                        continue

                    ts, last = upsert_candle(cur, internal_sym, latest)

                    # Publier prix courant dans Redis
                    payload = {"symbol": internal_sym, "price": last, "ts": ts.isoformat()}
                    r.set(f"price:{internal_sym}", last)
                    r.publish("quotes", json.dumps(payload))

                    print(f"[{internal_sym}] {pair} upsert ts={ts.isoformat()} close={last}")
                    time.sleep(SLEEP_BETWEEN_SYMBOLS)

                except httpx.HTTPStatusError as e:
                    if e.response is not None and e.response.status_code == 429:
                        # Trop de requêtes -> backoff simple
                        print(f"[{internal_sym}] 429 rate limited, backoff…")
                        time.sleep(2.0)
                    else:
                        print(f"[{internal_sym}] HTTP error: {e}")
                        time.sleep(SLEEP_BETWEEN_SYMBOLS)
                except Exception as e:
                    print(f"[{internal_sym}] error: {e}")
                    time.sleep(SLEEP_BETWEEN_SYMBOLS)

        time.sleep(LOOP_SLEEP)

if __name__ == "__main__":
    main()
