#!/usr/bin/env python3
"""
Script de monitoring du Dead Letter Queue (DLQ)
================================================

Écoute le topic crypto-dlq et affiche les anomalies en temps réel.
Utile pour surveiller les divergences critiques entre CoinGecko et CoinMarketCap.

Usage:
    python monitor_dlq.py
"""

import json
from kafka import KafkaConsumer
from datetime import datetime

KAFKA_BROKER = 'localhost:9092'
DLQ_TOPIC = 'crypto-dlq'

def format_anomaly(data):
    """Formate l'affichage d'une anomalie"""
    symbol = data.get('symbol', 'N/A')
    status = data.get('status', 'unknown')
    divergence = data.get('divergence_pct', 0)
    cg_price = data.get('coingecko_price', 0)
    cmc_price = data.get('coinmarketcap_price', 0)
    timestamp = data.get('timestamp', 'N/A')
    
    # Emoji selon sévérité
    emoji = "⚠️ " if status == "warning" else "🔴"
    
    print(f"\n{emoji} ANOMALIE DÉTECTÉE - {symbol}")
    print(f"   Divergence     : {divergence:.2f}%")
    print(f"   Statut         : {status.upper()}")
    print(f"   CoinGecko      : ${cg_price:,.2f}")
    print(f"   CoinMarketCap  : ${cmc_price:,.2f}")
    print(f"   Différence     : ${abs(cg_price - cmc_price):,.2f}")
    print(f"   Timestamp      : {timestamp}")
    print("-" * 60)

def main():
    """Point d'entrée"""
    print("="*70)
    print("🚨 MONITORING DLQ - Anomalies de Validation Croisée")
    print("="*70)
    print(f"📡 Topic Kafka: {DLQ_TOPIC}")
    print(f"🔍 Écoute en cours...\n")
    
    # Consumer Kafka
    consumer = KafkaConsumer(
        DLQ_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='dlq-monitor'
    )
    
    anomaly_count = 0
    
    try:
        for message in consumer:
            data = message.value
            anomaly_count += 1
            
            print(f"\n[#{anomaly_count}] Anomalie reçue à {datetime.now().strftime('%H:%M:%S')}")
            format_anomaly(data)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring arrêté")
        print(f"📊 Total anomalies détectées: {anomaly_count}")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
