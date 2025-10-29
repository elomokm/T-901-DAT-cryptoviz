#!/usr/bin/env python3
"""Test avec des données crypto réalistes (sans appel API)"""
from kafka import KafkaProducer
import json
import time
from datetime import datetime, timezone

print("🔌 Connexion au producer...")
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=1,
    retries=3,
    request_timeout_ms=60000,
    max_block_ms=60000,
    buffer_memory=33554432
)
print("✅ Producer connecté")

# Simule des données comme celles de l'API CoinGecko
print("\n📦 Création de 5 messages crypto...")
timestamp = datetime.now(timezone.utc).isoformat()
crypto_records = [
    {
        "timestamp": timestamp,
        "crypto": "bitcoin",
        "price_usd": 67891.23,
        "price_eur": 61234.56,
        "change_24h": 2.34,
        "market_cap": 1324567890123,
        "volume_24h": 23456789012
    },
    {
        "timestamp": timestamp,
        "crypto": "ethereum",
        "price_usd": 3456.78,
        "price_eur": 3121.45,
        "change_24h": -1.23,
        "market_cap": 415678901234,
        "volume_24h": 12345678901
    },
    {
        "timestamp": timestamp,
        "crypto": "cardano",
        "price_usd": 0.4567,
        "price_eur": 0.4123,
        "change_24h": 0.56,
        "market_cap": 15678901234,
        "volume_24h": 345678901
    },
    {
        "timestamp": timestamp,
        "crypto": "solana",
        "price_usd": 178.90,
        "price_eur": 161.45,
        "change_24h": 5.67,
        "market_cap": 78901234567,
        "volume_24h": 2345678901
    },
    {
        "timestamp": timestamp,
        "crypto": "polkadot",
        "price_usd": 5.67,
        "price_eur": 5.12,
        "change_24h": -0.89,
        "market_cap": 7890123456,
        "volume_24h": 234567890
    }
]

print(f"✅ {len(crypto_records)} messages préparés")

print("\n📤 Envoi des messages...")
futures = []
for i, record in enumerate(crypto_records):
    future = producer.send('crypto-prices', value=record)
    futures.append((record, future))
    print(f"  {record['crypto']} envoyé (non bloquant)")

print(f"\n🔄 Appel de flush(timeout=60) pour {len(futures)} messages...")
start = time.time()
try:
    producer.flush(timeout=60)
    elapsed = time.time() - start
    print(f"✅ Flush réussi en {elapsed:.2f}s")
    
    # Récupérer tous les résultats
    print("\n📊 Récupération des résultats...")
    for record, future in futures:
        metadata = future.get(timeout=1)
        print(f"  {record['crypto']}: partition={metadata.partition} offset={metadata.offset}")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ Erreur après {elapsed:.2f}s: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n🔚 Fermeture producer...")
producer.close()
print("✅ Terminé")
