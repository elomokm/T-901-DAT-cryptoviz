import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

import redis
import psycopg2
from psycopg2.extras import Json
from dateutil import parser as dtparse
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, DetectorFactory

# ---------- Config ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
STREAM_KEY = os.getenv("STREAM_KEY", "news:raw")
GROUP = os.getenv("GROUP", "analytics")
CONSUMER = os.getenv("CONSUMER", "worker-1")
READ_COUNT = int(os.getenv("READ_COUNT", "100"))
READ_BLOCK_MS = int(os.getenv("READ_BLOCK_MS", "5000"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/cryptoviz"
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("analytics")

# Langdetect déterministe
DetectorFactory.seed = 0

# ---------- Helpers ----------
analyzer = SentimentIntensityAnalyzer()

# mapping simple noms -> tickers
NAME_TO_SYMBOL = {
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "eth": "ETH",
    "solana": "SOL", "sol": "SOL",
    "ripple": "XRP", "xrp": "XRP",
    "cardano": "ADA", "ada": "ADA",
    "binance": "BNB", "bnb": "BNB",
    "dogecoin": "DOGE", "doge": "DOGE",
    "polygon": "MATIC", "matic": "MATIC",
    "polkadot": "DOT", "dot": "DOT",
}

def detect_lang(text: str) -> Optional[str]:
    try:
        t = (text or "").strip()
        if not t:
            return None
        return detect(t)
    except Exception:
        return None

def extract_symbols(text: str) -> List[str]:
    t = (text or "").lower()
    found = set()
    for name, sym in NAME_TO_SYMBOL.items():
        if f" {name} " in f" {t} " or f"${sym.lower()}" in t:
            found.add(sym)
    return sorted(found)

def parse_ts(ts_str: str) -> datetime:
    try:
        dt = dtparse.parse(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

# ---------- Main ----------
def ensure_group(r: redis.Redis):
    try:
        r.xgroup_create(STREAM_KEY, GROUP, id="0-0", mkstream=True)
        log.info(f"Created consumer group '{GROUP}' on stream '{STREAM_KEY}'")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            log.info(f"Consumer group '{GROUP}' already exists")
        else:
            raise

def insert_article(cur, payload, lang, symbols, sentiment):
    cur.execute(
        """
        INSERT INTO news_articles
        (ts, source, url, title, summary, content, lang, symbols, sentiment, raw)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (ts, url) DO NOTHING
        """,
        (
            parse_ts(payload.get("ts")),
            payload.get("source"),
            payload.get("url"),
            payload.get("title"),
            payload.get("summary"),
            payload.get("content"),
            lang,
            symbols,
            float(sentiment) if sentiment is not None else None,
            Json(payload),
        )
    )


def run():
    # Connect Redis
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    ensure_group(r)

    # Connect Postgres
    pg = psycopg2.connect(DATABASE_URL)
    pg.autocommit = False  # on gère les commits

    log.info("Analytics consumer started.")

    while True:
        # Lecture du groupe (prend d'abord les messages non ack du consumer)
        resp = r.xreadgroup(GROUP, CONSUMER, {STREAM_KEY: ">"}, count=READ_COUNT, block=READ_BLOCK_MS)
        if not resp:
            continue

        for _stream, messages in resp:
            with pg.cursor() as cur:
                for msg_id, fields in messages:
                    try:
                        data = fields.get("data")
                        if not data:
                            r.xack(STREAM_KEY, GROUP, msg_id)
                            continue
                        payload = json.loads(data)

                        # Construire texte pour NLP
                        text = " ".join([
                            payload.get("title") or "",
                            payload.get("summary") or "",
                            payload.get("content") or "",
                        ])[:100000]

                        lang = detect_lang(text)
                        symbols = extract_symbols(text)
                        sentiment = analyzer.polarity_scores(text).get("compound")

                        insert_article(cur, payload, lang, symbols, sentiment)
                        r.xack(STREAM_KEY, GROUP, msg_id)
                    except Exception as e:
                        log.warning(f"error on {msg_id}: {e}")
                        pg.rollback()          # <-- important : annule la transaction en erreur
                        r.xack(STREAM_KEY, GROUP, msg_id) 
                pg.commit()

if __name__ == "__main__":
    run()
