"""
Market Sentiment Data Feed Collector
Scrapes the Crypto Fear & Greed Index for market sentiment analysis
"""
import requests
from datetime import datetime, timezone
try:
    # When the project root is on sys.path (typical when running from repo root)
    from agents.base_agent import BaseAgent
    from agents.config import TOPICS
except ImportError:
    # When running the file directly (python agents/coingecko_agent.py)
    # the package context may be missing; add the parent directory to sys.path
    import os
    import sys

    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    from agents.base_agent import BaseAgent
    from agents.config import KAFKA_BROKER, TOPICS

class FearGreedAgent(BaseAgent):
    """
    Market Sentiment Data Feed Collector - Fear & Greed Index

    Continuously scrapes cryptocurrency market sentiment data.
    Implements producer/consumer paradigm by sending data to Kafka.

    Features:
    - Collects Fear & Greed Index (0-100 scale)
    - Provides sentiment classification (Extreme Fear → Extreme Greed)
    - Essential for market psychology analytics
    - Source: Alternative.me API
    """
    
    API_URL = "https://api.alternative.me/fng/"
    
    def __init__(self, poll_interval: int = 300):
        """
        Args:
            poll_interval: Intervalle en secondes (défaut: 300s = 5 min)
        """
        super().__init__(
            name="FearGreedAgent",
            topic=TOPICS['sentiment'],  # crypto-market-sentiment
            poll_interval=poll_interval
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoViz/1.0',
            'Accept': 'application/json',
        })
    
    def fetch_data(self):
        """
        Récupère le Fear & Greed Index depuis l'API.
        
        Returns:
            dict: {'value': 27, 'classification': 'Fear', 'timestamp': '...'}
        """
        try:
            response = self.session.get(self.API_URL, timeout=10)
            response.raise_for_status()  # Lève une erreur si status != 200
            
            data = response.json()
            
            # Extraire les données pertinentes
            fg_data = data['data'][0]
            
            # Structurer pour Kafka/InfluxDB
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'value': int(fg_data['value']),
                'classification': fg_data['value_classification'],
                'time_until_update': int(fg_data.get('time_until_update', 0))
            }
            
        except requests.RequestException as e:
            print(f"⚠️  [{self.name}] Erreur API: {e}")
            return None  # Si erreur, on retourne None (pas d'envoi à Kafka)


# Point d'entrée si exécuté directement
if __name__ == "__main__":
    agent = FearGreedAgent(poll_interval=300)  # 5 minutes
    agent.run()