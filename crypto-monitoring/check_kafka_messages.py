#!/usr/bin/env python3
"""
Script simple pour consommer et afficher les messages Kafka du topic crypto-prices.
Utile pour vérifier que les producteurs envoient bien le champ 'source'.
"""
import json
import os
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = 'crypto-prices'

def main():
    print("=" * 70)
    print(f" LECTURE DU TOPIC KAFKA: {TOPIC}")
    print("=" * 70)
    print(f"Broker: {KAFKA_BROKER}")
    print("Mode: Lecture depuis le DÉBUT du topic (pour voir les messages existants)")
    print()
    
    # Consumer simple (pas de groupe, lit depuis le début)
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset='earliest',  # Lire depuis le DÉBUT
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=10000  # Timeout après 10s sans message
    )
    
    print("⏳ En attente de messages (Ctrl+C pour arrêter)...\n")
    
    count = 0
    sources_seen = set()
    
    try:
        for message in consumer:
            count += 1
            data = message.value
            
            # Afficher le message
            source = data.get('source', '❌ MANQUANT')
            symbol = data.get('symbol', 'N/A')
            price = data.get('price_usd', 0)
            timestamp = data.get('timestamp', 'N/A')
            
            sources_seen.add(source)
            
            print(f"Message #{count}")
            print(f"  Source: {source}")
            print(f"  Symbol: {symbol}")
            print(f"  Prix: ${price:,.2f}")
            print(f"  Timestamp: {timestamp}")
            print(f"  Clés présentes: {', '.join(sorted(data.keys()))}")
            print()
            
            if count >= 10:  # Limiter à 10 messages
                break
    
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt demandé")
    
    finally:
        consumer.close()
        
        print("\n" + "=" * 70)
        print(f" RÉSUMÉ: {count} messages lus")
        print(f" Sources détectées: {', '.join(sources_seen) if sources_seen else 'Aucune'}")
        
        if '❌ MANQUANT' in sources_seen:
            print("\n⚠️  ATTENTION: Certains messages n'ont pas le champ 'source'")
            print("   → Vérifiez que les producteurs envoient bien ce champ")
        
        print("=" * 70)

if __name__ == "__main__":
    main()
