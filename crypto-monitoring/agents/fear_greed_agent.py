"""Agent pour récupérer le Fear & Greed Index"""
import requests
from datetime import datetime, timezone
from .base_agent import BaseAgent
from .config import TOPICS

class FearGreedAgent(BaseAgent):
    """
    Agent qui récupère le Fear & Greed Index depuis alternative.me
    API: https://api.alternative.me/fng/
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