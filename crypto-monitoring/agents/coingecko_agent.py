"""Agent CoinGecko - Collecte prix et métadonnées de 20 cryptos"""
import time 
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .base_agent import BaseAgent
from .config import TOPICS

class CoinGeckoAgent(BaseAgent):
    """
    Agent qui récupère les données de 20 cryptos depuis CoinGecko.
    Endpoint : /coins/markets (plus riche que /simple/price)
    """
    
    API_BASE = "https://api.coingecko.com/api/v3"
    
    # IDs CoinGecko (différents des symboles !)
    CRYPTO_IDS = [
        'bitcoin', 'ethereum', 'tether', 'binancecoin', 'solana',
        'ripple', 'usd-coin', 'cardano', 'avalanche-2', 'dogecoin',
        'polkadot', 'chainlink', 'dai', 'litecoin', 'shiba-inu',
        'uniswap', 'cosmos', 'stellar', 'monero', 'algorand'
    ]
    
    def __init__(self, poll_interval: int = 60):
        """
        Args:
            poll_interval: Intervalle en secondes (défaut: 60s = 1 min)
        """
        super().__init__(
            name="CoinGeckoAgent",
            topic=TOPICS['prices'],  # crypto-prices
            poll_interval=poll_interval
        )
        
        # Session HTTP réutilisable (connexion persistante)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoViz/2.0 (+https://github.com/you/cryptoviz)',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
        })

    def fetch_data(self) -> Optional[List[Dict]]:
        """
        Récupère les données des 20 cryptos depuis /coins/markets.
        
        Returns:
            List[Dict]: Liste de dictionnaires (1 par crypto) ou None si erreur
        """
        try:
            url = f"{self.API_BASE}/coins/markets"
            
            params = {
                'vs_currency': 'usd',
                'ids': ','.join(self.CRYPTO_IDS),  # "bitcoin,ethereum,..."
                'order': 'market_cap_desc',
                'sparkline': 'false',
                'price_change_percentage': '1h,24h,7d',  # Variations
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            raw_data = response.json()  # Liste de 20 cryptos
            
            # Enrichir avec timestamp
            enriched_data = []
            timestamp = datetime.now(timezone.utc).isoformat()
            
            for coin in raw_data:
                record = {
                    # Métadonnées
                    'timestamp': timestamp,
                    'crypto_id': coin['id'],           # "bitcoin"
                    'symbol': coin['symbol'].upper(),  # "BTC"
                    'name': coin['name'],              # "Bitcoin"
                    
                    # Prix & variations
                    'price_usd': coin.get('current_price', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'market_cap_rank': coin.get('market_cap_rank', 0),
                    'volume_24h': coin.get('total_volume', 0),
                    
                    # Variations (%)
                    'change_1h': coin.get('price_change_percentage_1h_in_currency', 0),
                    'change_24h': coin.get('price_change_percentage_24h', 0),
                    'change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                    
                    # All-Time High/Low
                    'ath': coin.get('ath', 0),
                    'ath_date': coin.get('ath_date', None),
                    'ath_change_pct': coin.get('ath_change_percentage', 0),
                    'atl': coin.get('atl', 0),
                    'atl_date': coin.get('atl_date', None),
                    'atl_change_pct': coin.get('atl_change_percentage', 0),
                    
                    # Supply
                    'circulating_supply': coin.get('circulating_supply', 0),
                    'total_supply': coin.get('total_supply', 0),
                    'max_supply': coin.get('max_supply', 0),
                }
                
                enriched_data.append(record)
            
            print(f"✅ [{self.name}] Récupéré {len(enriched_data)} cryptos")
            return enriched_data
            
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                print(f"⚠️  [{self.name}] Rate limit ! Attendre...")
            else:
                print(f"❌ [{self.name}] Erreur HTTP {e.response.status_code}")
            return None
            
        except requests.RequestException as e:
            print(f"❌ [{self.name}] Erreur réseau: {e}")
            return None
        
        except Exception as e:
            print(f"❌ [{self.name}] Erreur inattendue: {e}")
            return None
        
    def run(self):
        """
        Override de BaseAgent.run() pour gérer la liste de cryptos.
        """
        self.connect_kafka()
        
        print(f"🚀 [{self.name}] Démarrage (20 cryptos, intervalle: {self.poll_interval}s)")
        
        try:
            while True:
                try:
                    # Récupérer les données (liste de 20 cryptos)
                    data_list = self.fetch_data()
                    
                    # Envoyer chaque crypto individuellement à Kafka
                    if data_list:
                        for crypto_data in data_list:
                            self.send_to_kafka(crypto_data)
                    
                    # Attendre avant la prochaine collecte
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    print(f"\n⏹️  [{self.name}] Arrêt demandé")
                    break
                except Exception as e:
                    print(f"⚠️  [{self.name}] Erreur: {e}")
                    time.sleep(30)  # Attendre 30s avant de réessayer
                    
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                print(f"🔌 [{self.name}] Déconnecté de Kafka")


# Point d'entrée
if __name__ == "__main__":
    import time
    agent = CoinGeckoAgent(poll_interval=60)
    agent.run()