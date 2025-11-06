"""Configuration commune pour tous les agents"""
import os

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