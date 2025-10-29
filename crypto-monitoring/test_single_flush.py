#!/usr/bin/env python3
"""Test ultra minimal - 1 message avec flush"""
from kafka import KafkaProducer
import json
import time

print("🔌 Connexion au producer...")
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=1,
    retries=3,
    request_timeout_ms=60000,
    max_block_ms=60000
)
print("✅ Producer connecté")

print("\n📤 Envoi de 1 message...")
record = {"test": "single_flush", "timestamp": time.time()}
future = producer.send('crypto-prices', value=record)
print("✅ Message envoyé (non bloquant)")

print("\n🔄 Appel de flush(timeout=30)...")
start = time.time()
try:
    producer.flush(timeout=30)
    elapsed = time.time() - start
    print(f"✅ Flush réussi en {elapsed:.2f}s")
    
    # Maintenant récupérer le résultat
    print("\n📊 Récupération du résultat...")
    metadata = future.get(timeout=1)
    print(f"✅ Message confirmé: partition={metadata.partition} offset={metadata.offset}")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ Erreur après {elapsed:.2f}s: {type(e).__name__}: {e}")

print("\n🔚 Fermeture producer...")
producer.close()
print("✅ Terminé")
