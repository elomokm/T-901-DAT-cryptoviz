#!/usr/bin/env python3
"""Test avec 5 messages (comme crypto_producer)"""
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
    max_block_ms=60000,
    buffer_memory=33554432
)
print("✅ Producer connecté")

print("\n📤 Envoi de 5 messages...")
futures = []
for i in range(5):
    record = {"test": f"message_{i}", "timestamp": time.time()}
    future = producer.send('crypto-prices', value=record)
    futures.append(future)
    print(f"  Message {i+1} envoyé (non bloquant)")

print("\n🔄 Appel de flush(timeout=60)...")
start = time.time()
try:
    producer.flush(timeout=60)
    elapsed = time.time() - start
    print(f"✅ Flush réussi en {elapsed:.2f}s")
    
    # Récupérer tous les résultats
    print("\n📊 Récupération des résultats...")
    for i, future in enumerate(futures):
        metadata = future.get(timeout=1)
        print(f"  Message {i+1}: partition={metadata.partition} offset={metadata.offset}")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ Erreur après {elapsed:.2f}s: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n🔚 Fermeture producer...")
producer.close()
print("✅ Terminé")
