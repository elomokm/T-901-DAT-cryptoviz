#!/usr/bin/env python3
"""
Multi-Source Price Aggregator Agent
Fetches prices from multiple sources (CoinGecko, CoinMarketCap) and calculates consensus price.
"""
import os
import json
import time
import requests
from datetime import datetime
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = 'crypto-prices'
COINGECKO_API = 'https://api.coingecko.com/api/v3'
CMC_API = 'https://pro-api.coinmarketcap.com/v1'
CMC_API_KEY = os.getenv('CMC_API_KEY', '')  # Optionnel, peut marcher sans

# Top cryptos à tracker
TOP_CRYPTOS = [
    'bitcoin', 'ethereum', 'binancecoin', 'ripple', 'cardano',
    'solana', 'polkadot', 'dogecoin', 'avalanche-2', 'chainlink',
    'tron', 'polygon', 'litecoin', 'uniswap', 'bitcoin-cash'
]

# Mapping CoinGecko ID → CoinMarketCap symbol
CRYPTO_MAPPING = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'binancecoin': 'BNB',
    'ripple': 'XRP',
    'cardano': 'ADA',
    'solana': 'SOL',
    'polkadot': 'DOT',
    'dogecoin': 'DOGE',
    'avalanche-2': 'AVAX',
    'chainlink': 'LINK',
    'tron': 'TRX',
    'polygon': 'MATIC',
    'litecoin': 'LTC',
    'uniswap': 'UNI',
    'bitcoin-cash': 'BCH'
}


def fetch_coingecko_prices(crypto_ids):
    """Fetch prices from CoinGecko API"""
    try:
        url = f"{COINGECKO_API}/simple/price"
        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  CoinGecko API error: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ CoinGecko fetch error: {e}")
        return {}


def fetch_coinmarketcap_prices(symbols):
    """Fetch prices from CoinMarketCap API (fallback to free endpoint if no key)"""
    try:
        # Si pas de clé API, on skip CMC
        if not CMC_API_KEY:
            print("ℹ️  No CMC API key, skipping CoinMarketCap")
            return {}
        
        url = f"{CMC_API}/cryptocurrency/quotes/latest"
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        params = {
            'symbol': ','.join(symbols),
            'convert': 'USD'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = {}
            for symbol, info in data.get('data', {}).items():
                quote = info.get('quote', {}).get('USD', {})
                prices[symbol.lower()] = {
                    'price': quote.get('price', 0),
                    'market_cap': quote.get('market_cap', 0),
                    'volume_24h': quote.get('volume_24h', 0),
                    'percent_change_24h': quote.get('percent_change_24h', 0)
                }
            return prices
        else:
            print(f"⚠️  CoinMarketCap API error: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"❌ CoinMarketCap fetch error: {e}")
        return {}


def calculate_consensus_price(coingecko_data, cmc_data, crypto_id, symbol):
    """Calculate consensus price from multiple sources"""
    prices = []
    sources = []
    
    # Prix CoinGecko
    if crypto_id in coingecko_data:
        cg_price = coingecko_data[crypto_id].get('usd', 0)
        if cg_price > 0:
            prices.append(cg_price)
            sources.append('coingecko')
    
    # Prix CoinMarketCap
    if symbol.lower() in cmc_data:
        cmc_price = cmc_data[symbol.lower()].get('price', 0)
        if cmc_price > 0:
            prices.append(cmc_price)
            sources.append('coinmarketcap')
    
    # Calculer le prix moyen (consensus)
    if prices:
        consensus_price = sum(prices) / len(prices)
        
        # Calculer l'écart (pour détecter les anomalies)
        if len(prices) > 1:
            price_spread = (max(prices) - min(prices)) / consensus_price * 100
        else:
            price_spread = 0
        
        return {
            'consensus_price': consensus_price,
            'sources': sources,
            'source_count': len(sources),
            'price_spread_pct': price_spread,
            'individual_prices': dict(zip(sources, prices))
        }
    
    return None


def aggregate_and_publish():
    """Main aggregation logic"""
    print("=" * 80)
    print("🔄 MULTI-SOURCE PRICE AGGREGATOR")
    print("=" * 80)
    print(f"📡 Kafka Broker: {KAFKA_BROKER}")
    print(f"📊 Sources: CoinGecko + CoinMarketCap")
    print(f"🎯 Strategy: Average Consensus Price")
    print(f"💰 Tracking: {len(TOP_CRYPTOS)} cryptocurrencies")
    print("=" * 80)
    
    # Initialiser Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        compression_type='gzip'
    )
    
    batch_count = 0
    
    try:
        while True:
            batch_count += 1
            timestamp = datetime.utcnow().isoformat()
            
            print(f"\n📦 Batch #{batch_count} - {timestamp}")
            
            # Fetch from both sources
            print("  🌐 Fetching CoinGecko...")
            coingecko_data = fetch_coingecko_prices(TOP_CRYPTOS)
            
            print("  💎 Fetching CoinMarketCap...")
            symbols = [CRYPTO_MAPPING.get(cid, cid.upper()) for cid in TOP_CRYPTOS]
            cmc_data = fetch_coinmarketcap_prices(symbols)
            
            success_count = 0
            
            # Process each crypto
            for crypto_id in TOP_CRYPTOS:
                symbol = CRYPTO_MAPPING.get(crypto_id, crypto_id.upper())
                
                # Get data from CoinGecko (primary source)
                cg_data = coingecko_data.get(crypto_id, {})
                if not cg_data:
                    continue
                
                # Calculate consensus price
                consensus = calculate_consensus_price(coingecko_data, cmc_data, crypto_id, symbol)
                
                if consensus:
                    # Prepare message with consensus price
                    message = {
                        'crypto_id': crypto_id,
                        'symbol': symbol,
                        'name': crypto_id.replace('-', ' ').title(),
                        'price_usd': consensus['consensus_price'],
                        'market_cap': cg_data.get('usd_market_cap', 0),
                        'volume_24h': cg_data.get('usd_24h_vol', 0),
                        'change_24h': cg_data.get('usd_24h_change', 0),
                        'timestamp': timestamp,
                        'source': 'multi-source-aggregator',
                        'aggregation': {
                            'sources': consensus['sources'],
                            'source_count': consensus['source_count'],
                            'price_spread_pct': round(consensus['price_spread_pct'], 2),
                            'individual_prices': consensus['individual_prices']
                        }
                    }
                    
                    # Send to Kafka
                    producer.send(TOPIC, value=message)
                    success_count += 1
                    
                    # Log avec spread
                    spread_indicator = "✅" if consensus['price_spread_pct'] < 1 else "⚠️"
                    print(f"  {spread_indicator} {symbol:6s} ${consensus['consensus_price']:>12,.2f} "
                          f"({consensus['source_count']} sources, spread: {consensus['price_spread_pct']:.2f}%)")
            
            producer.flush()
            print(f"  ✅ Batch #{batch_count}: {success_count}/{len(TOP_CRYPTOS)} cryptos published")
            
            # Wait before next batch (30 seconds)
            print(f"  ⏳ Waiting 30s before next batch...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopping aggregator...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        producer.close()
        print("✅ Producer closed")


if __name__ == "__main__":
    aggregate_and_publish()
