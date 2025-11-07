"""Configuration commune pour tous les agents"""
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv non installé, utiliser env système

# Kafka Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

# Topics Kafka (un par type de données)
TOPICS = {
    'prices': 'crypto-prices',              # CoinGecko, CoinMarketCap
    'sentiment': 'crypto-market-sentiment',  # Fear & Greed
    'realtime': 'crypto-realtime',          # Binance WebSocket
    'news': 'crypto-news',                  # News scraper
}

# Producer Kafka settings
PRODUCER_CONFIG = {
    'acks': 1,
    'retries': 3,
    'max_in_flight_requests_per_connection': 1,
}

# API Keys
CMC_API_KEY = os.getenv('CMC_API_KEY', '')  # CoinMarketCap API Key

# Agent-specific settings (polling intervals en secondes)
COINGECKO_POLL_INTERVAL = int(os.getenv('COINGECKO_POLL_INTERVAL', '60'))
COINMARKETCAP_POLL_INTERVAL = int(os.getenv('COINMARKETCAP_POLL_INTERVAL', '120'))
FEAR_GREED_POLL_INTERVAL = int(os.getenv('FEAR_GREED_POLL_INTERVAL', '300'))