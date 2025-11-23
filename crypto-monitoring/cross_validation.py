#!/usr/bin/env python3
"""Script pour analyser la validation croisée CoinGecko vs CoinMarketCap"""
import json
import sys
from kafka import KafkaConsumer
from collections import defaultdict
from datetime import datetime

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'crypto-prices'

def analyze_cross_validation(duration_seconds=60):
    """
    Écoute le topic crypto-prices et compare les prix des deux sources.
    
    Args:
        duration_seconds: Durée d'analyse en secondes
    """
    print("="*70)
    print("📊 VALIDATION CROISÉE : CoinGecko vs CoinMarketCap")
    print("="*70)
    print(f"⏱️  Durée d'analyse: {duration_seconds}s")
    print(f"📡 Topic Kafka: {TOPIC}")
    print()
    
    # Consumer Kafka
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',  # Seulement les nouveaux messages
        enable_auto_commit=True,
        group_id='cross-validation-analyzer'
    )
    
    # Stockage des prix par crypto et source
    prices = defaultdict(dict)  # {symbol: {source: price}}
    
    print("🔍 Écoute en cours...")
    print("-" * 70)
    
    start_time = datetime.now()
    message_count = 0
    
    try:
        for message in consumer:
            data = message.value
            
            # Extraire les infos
            source = data.get('source', 'unknown')
            symbol = data.get('symbol', 'N/A')
            price = data.get('price_usd', 0)
            
            message_count += 1
            
            # Stocker le prix
            prices[symbol][source] = price
            
            print(f"[{source:15}] {symbol:6} = ${price:>12,.2f}")
            
            # Vérifier si on a les deux sources pour cette crypto
            if len(prices[symbol]) == 2:
                compare_prices(symbol, prices[symbol])
            
            # Vérifier la durée
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= duration_seconds:
                break
        
        # Résumé final
        print("\n" + "="*70)
        print("📈 RÉSUMÉ DE LA VALIDATION CROISÉE")
        print("="*70)
        print(f"✅ Messages analysés: {message_count}")
        print(f"🔢 Cryptos uniques: {len(prices)}")
        print()
        
        # Afficher les comparaisons
        for symbol, sources in prices.items():
            if len(sources) == 2:
                compare_prices(symbol, sources, detailed=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Analyse interrompue")
    finally:
        consumer.close()
        print("\n👋 Consumer fermé")

def compare_prices(symbol: str, sources: dict, detailed: bool = False):
    """
    Compare les prix de deux sources.
    
    Args:
        symbol: Symbole de la crypto
        sources: Dict {source: price}
        detailed: Afficher les détails
    """
    if 'coingecko' not in sources or 'coinmarketcap' not in sources:
        return
    
    cg_price = sources['coingecko']
    cmc_price = sources['coinmarketcap']
    
    if cg_price == 0 or cmc_price == 0:
        return
    
    # Calculer la divergence en %
    divergence = abs((cmc_price - cg_price) / cg_price) * 100
    
    # Seuil d'alerte : 5%
    status = "✅" if divergence < 5.0 else "⚠️"
    
    if detailed or divergence >= 5.0:
        print(f"\n{status} {symbol} - Divergence: {divergence:.2f}%")
        print(f"   CoinGecko     : ${cg_price:,.2f}")
        print(f"   CoinMarketCap : ${cmc_price:,.2f}")
        print(f"   Différence    : ${abs(cmc_price - cg_price):,.2f}")

def main():
    """Point d'entrée"""
    duration = 60  # Par défaut 60 secondes
    
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("❌ Usage: python cross_validation.py [durée_en_secondes]")
            sys.exit(1)
    
    analyze_cross_validation(duration)

if __name__ == "__main__":
    main()
