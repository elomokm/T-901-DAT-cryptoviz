"""
Crypto Producer - Collecte les données crypto et les envoie vers Kafka
"""
import json
import os
import time
import random
from datetime import datetime, timezone

import requests

# Workaround: map built-in 'six' to kafka.vendor.six to avoid ModuleNotFoundError on Python 3.12
# Some kafka-python builds fail to load kafka.vendor.six.moves; this shim fixes the import path.
try:
    import sys as _sys
    import six as _six  # type: ignore
    _sys.modules.setdefault("kafka.vendor.six", _six)
    _sys.modules.setdefault("kafka.vendor.six.moves", _six.moves)
except Exception:
    pass

from kafka import KafkaProducer

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'crypto-prices')
API_URL = 'https://api.coingecko.com/api/v3/simple/price'

# Latency tuning via env vars
ACKS = os.getenv('PRODUCER_ACKS', '1')  # '0' fastest, '1' default, 'all' safest
LINGER_MS = int(os.getenv('PRODUCER_LINGER_MS', '0'))  # 0 = send immediately
BATCH_SIZE = int(os.getenv('PRODUCER_BATCH_SIZE', '16384'))  # bytes; smaller can reduce latency
COMPRESSION = os.getenv('PRODUCER_COMPRESSION', '') or None  # '', 'snappy', 'lz4', 'gzip'
POLL_INTERVAL_SEC = float(os.getenv('POLL_INTERVAL_SEC', '10'))  # API poll interval
RATE_LIMIT_FALLBACK_SEC = int(os.getenv('RATE_LIMIT_FALLBACK_SEC', '15'))  # backoff si pas de Retry-After
SEND_EVERY_POLL = os.getenv('SEND_EVERY_POLL', '0') in ('1', 'true', 'True')



# Cryptos à surveiller
CRYPTOS = ['bitcoin', 'ethereum', 'cardano', 'solana', 'polkadot']

# Reuse HTTP connection to lower TLS/connect overhead
HTTP = requests.Session()
HTTP.headers.update({
    'User-Agent': 'CryptoProducer/1.0 (+https://github.com/elomokm/T-901-DAT-cryptoviz)',
    'Accept': 'application/json',
    'Connection': 'keep-alive',
})


class RateLimitError(Exception):
    """Erreur spécifique quand l'API retourne 429 Too Many Requests."""
    def __init__(self, retry_after: float):
        super().__init__(f"Rate limited, retry after {retry_after}s")
        self.retry_after = float(retry_after)

def create_producer():
    """Crée et retourne un producer Kafka"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks=ACKS,
            linger_ms=LINGER_MS,
            batch_size=BATCH_SIZE,
            compression_type=COMPRESSION,
            retries=0,
            max_in_flight_requests_per_connection=5,
            request_timeout_ms=10000,
        )
        print(" Producer Kafka connecté avec succès!")
        return producer
    except Exception as e:
        print(f" Erreur de connexion à Kafka: {e}")
        return None

def fetch_crypto_prices():
    """Récupère les prix des cryptos depuis l'API CoinGecko"""
    try:
        params = {
            'ids': ','.join(CRYPTOS),
            'vs_currencies': 'usd,eur',
            'include_24hr_change': 'true',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true'
        }
        response = HTTP.get(API_URL, params=params, timeout=10)
        # Gère explicitement le cas 429 pour appliquer un backoff adapté
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            try:
                backoff = float(retry_after) if retry_after is not None else RATE_LIMIT_FALLBACK_SEC
            except ValueError:
                backoff = RATE_LIMIT_FALLBACK_SEC
            raise RateLimitError(backoff)
        response.raise_for_status()

        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f" Erreur API: {e}")
        return None

def enrich_data(crypto_data):
    """Enrichit les données avec timestamp et métadonnées"""
    enriched_data = []
    # Use timezone-aware UTC timestamp to avoid deprecation warnings
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for crypto, prices in crypto_data.items():
        record = {
            'timestamp': timestamp,
            'crypto': crypto,
            'price_usd': prices.get('usd', 0),
            'price_eur': prices.get('eur', 0),
            'change_24h': prices.get('usd_24h_change', 0),
            'market_cap': prices.get('usd_market_cap', 0),
            'volume_24h': prices.get('usd_24h_vol', 0)
        }
        enriched_data.append(record)
    
    return enriched_data


def main():
    """Fonction principale"""
    print(" Démarrage du Crypto Producer...")
    print(f" Surveillance de: {', '.join(CRYPTOS)}")
    print(f" Topic Kafka: {KAFKA_TOPIC}")
    print("-" * 60)
    print(f" Broker Kafka: {KAFKA_BROKER}")
    print(f" Intervalle polling API: {POLL_INTERVAL_SEC}s")
    print(f" acks={ACKS}, linger_ms={LINGER_MS}, batch_size={BATCH_SIZE}, compression={COMPRESSION or 'none'}")
    print("-" * 60)

    producer = create_producer()
    if not producer:
        return

    message_count = 0
    last_snapshot = None  # pour savoir si le prix a changé

    try:
        while True:
            # 1. Récupère les données
            try:
                crypto_data = fetch_crypto_prices()
            except RateLimitError as rl:
                base = max(POLL_INTERVAL_SEC, rl.retry_after)
                jitter_factor = random.uniform(1.0, 1.3)  # jamais moins que 1x
                sleep_s = base * jitter_factor
                print(f" Rate limit atteint, pause {sleep_s:.1f}s (Retry-After={rl.retry_after}s)")
                time.sleep(sleep_s)
                continue

            if crypto_data:
                # 2. Enrichit les données (timestamp, market_cap etc.)
                enriched_records = enrich_data(crypto_data)

                # 3. Snapshot minimal pour dédup
                current_snapshot = {
                    rec['crypto']: {
                        'price_usd': rec['price_usd'],
                        'price_eur': rec['price_eur'],
                        'change_24h': rec['change_24h']
                    }
                    for rec in enriched_records
                }

                # 4. Vérifie si changement par rapport au dernier envoi
                if not SEND_EVERY_POLL and current_snapshot == last_snapshot:
                    ts = enriched_records[0]['timestamp'] if enriched_records else datetime.now(timezone.utc).isoformat()
                    print(f" [{ts}] Aucun changement de prix détecté, pas d'envoi Kafka.")
                    print("-" * 60)
                    time.sleep(POLL_INTERVAL_SEC)
                    continue

                # 5. Il y a du nouveau -> on publie dans Kafka
                last_snapshot = current_snapshot

                for record in enriched_records:
                    producer.send(KAFKA_TOPIC, value=record)
                    message_count += 1

                    print(
                        f" [{record['timestamp']}] {record['crypto'].upper()}: "
                        f"${record['price_usd']:.2f} "
                        f"({record['change_24h']:+.2f}%)"
                    )

                print(f" {len(enriched_records)} messages envoyés (Total: {message_count})")

            else:
                print("  Aucune donnée récupérée, nouvelle tentative...")

            print("-" * 60)

            # 6. Pause normale entre deux tours
            time.sleep(POLL_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n\n Arrêt du producer...")
        print(f" Total de messages envoyés: {message_count}")

    except Exception as e:
        print(f" Erreur inattendue: {e}")

    finally:
        if producer:
            producer.close()
            print(" Producer fermé proprement")


if __name__ == "__main__":
    main()


    