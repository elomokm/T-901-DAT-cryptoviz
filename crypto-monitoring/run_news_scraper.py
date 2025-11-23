#!/usr/bin/env python3
"""
Runner pour le News Scraper Agent
Collecte les actualités crypto depuis RSS feeds et les envoie à Kafka
"""
import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.news_scraper_agent import NewsScraperAgent


def main():
    """Lance le News Scraper Agent"""

    print("=" * 70)
    print("🗞️  NEWS SCRAPER AGENT - Real-time Crypto News Feed Collector")
    print("=" * 70)
    print()
    print("📡 Sources:")
    print("  • CoinDesk (https://www.coindesk.com)")
    print("  • CoinTelegraph (https://cointelegraph.com)")
    print()
    print("📤 Destination:")
    print(f"  • Kafka Topic: crypto-news")
    print(f"  • Broker: {os.getenv('KAFKA_BROKER', 'localhost:9092')}")
    print()

    # Lire l'intervalle depuis l'environnement (default: 300s = 5min)
    poll_interval = int(os.getenv('NEWS_POLL_INTERVAL', 300))
    print(f"⏱️  Intervalle de scraping: {poll_interval}s ({poll_interval//60}min)")
    print()
    print("=" * 70)
    print()

    # Créer et lancer l'agent
    agent = NewsScraperAgent(poll_interval=poll_interval)

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt du News Scraper Agent")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
