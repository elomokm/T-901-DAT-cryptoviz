#!/usr/bin/env python3
"""
Test simple: envoie 5 messages à Kafka sans attendre de confirmation
"""
import json
from kafka import KafkaProducer
from datetime import datetime, timezone

print("Test producer simple...")

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=1,
    retries=3,
    request_timeout_ms=60000
)

print("✓ Producer connecté")

# Envoie 5 messages test
for i in range(5):
    msg = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'crypto': f'test_{i}',
        'price_usd': 100.0 + i,
        'price_eur': 90.0 + i,
        'change_24h': i * 0.5,
        'market_cap': 1000000.0,
        'volume_24h': 50000.0
    }
    
    future = producer.send('crypto-prices', value=msg)
    print(f"Message {i+1} envoyé (non bloquant)...")

# Force l'envoi de tout
print("Flush des messages...")
producer.flush(timeout=30)
print("✓ Tous les messages ont été envoyés avec succès!")

producer.close()
print("✓ Producer fermé")
