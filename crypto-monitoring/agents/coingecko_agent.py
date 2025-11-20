"""
CoinGecko Market Data Feed Collector
Real-time cryptocurrency market data scraper using CoinGecko API
Collects price, volume, market cap, and metadata for top cryptocurrencies
"""
import time 
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

# Import helpers: prefer absolute package imports but fall back to
# local/package-relative imports when the module is executed as a script
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
    from agents.config import TOPICS

# Flag de debug pour mesures de performance (local only)
DEBUG_PERF = True  # Mettre à True pour debug local

# Logger pour tenacity
logger = logging.getLogger(__name__)

# Circuit Breaker : Protège l'agent contre des APIs down prolongées
# - fail_max=5 : Ouvre le circuit après 5 échecs consécutifs
# - reset_timeout=60 : Attend 60s avant de réessayer (état "semi-ouvert")
api_circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name='CoinGeckoAPI'
)

class CoinGeckoAgent(BaseAgent):
    """
    Market Data Feed Collector - CoinGecko Source

    Continuously scrapes cryptocurrency market data from CoinGecko API.
    Implements producer/consumer paradigm by sending data to Kafka.

    Features:
    - Collects data for 20 major cryptocurrencies
    - Uses /coins/markets endpoint for comprehensive market data
    - Implements circuit breaker pattern for API resilience
    - Validates data against Avro schema before sending
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
            poll_interval=poll_interval,
            schema_file='schemas/crypto_price.avsc'  # Validation Avro activée
        )
        
        # Session HTTP réutilisable (connexion persistante)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoViz/2.0 (+https://github.com/you/cryptoviz)',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
        })

    @api_circuit_breaker
    @retry(
        # Réessayer jusqu'à 5 fois
        stop=stop_after_attempt(5),
        # Attente exponentielle : 1s, 2s, 4s, 8s, 16s (max 60s)
        wait=wait_exponential(multiplier=1, min=1, max=60),
        # Retry uniquement sur erreurs réseau et rate limit
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError)),
        # Logger les tentatives
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def fetch_data(self) -> Optional[List[Dict]]:
        """
        Récupère les données des 20 cryptos depuis /coins/markets.
        
        Protection multi-niveaux:
        1. Circuit Breaker : Coupe si trop d'erreurs (évite surcharge)
        2. Retry avec exponential backoff : Réessaye intelligemment
        
        Returns:
            List[Dict]: Liste de dictionnaires (1 par crypto) ou None si erreur
        """
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
                # Source identifier (for cross-validation)
                'source': 'coingecko',
                
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
        
        print(f" [{self.name}] Récupéré {len(enriched_data)} cryptos")
        return enriched_data
        
    def run(self):
        """
        Override de BaseAgent.run() pour gérer la liste de cryptos.
        Utilise send_batch_to_kafka() pour optimiser les performances.
        """
        self.connect_kafka()
        
        print(f" [{self.name}] Démarrage (20 cryptos, intervalle: {self.poll_interval}s)")
        if DEBUG_PERF:
            print(f" [{self.name}] Mode DEBUG_PERF activé (mesures de performance)")
        
        try:
            while True:
                try:
                    # Récupérer les données (liste de 20 cryptos)
                    data_list = self.fetch_data()
                    
                    if data_list:
                        if DEBUG_PERF:
                            print(f"📦 [{self.name}] Envoi de {len(data_list)} cryptos en batch...")
                        
                        # Envoi optimisé en batch avec compression
                        stats = self.send_batch_to_kafka(data_list, debug=DEBUG_PERF)
                        
                        if DEBUG_PERF:
                            estimated_old = len(data_list) * 15
                            gain = estimated_old - stats['duration_ms']
                            gain_pct = (gain / estimated_old * 100) if estimated_old > 0 else 0
                            print(f"⚡ Gain: {gain:.0f}ms ({gain_pct:.1f}% plus rapide)")
                    
                    # Attendre avant la prochaine collecte
                    time.sleep(self.poll_interval)
                    
                except CircuitBreakerError:
                    print(f" [{self.name}] Circuit Breaker OUVERT - API indisponible")
                    print(f"   → Attente de {api_circuit_breaker.reset_timeout}s avant réessai...")
                    time.sleep(api_circuit_breaker.reset_timeout)
                    
                except KeyboardInterrupt:
                    print(f"\n  [{self.name}] Arrêt demandé")
                    break
                    
                except Exception as e:
                    print(f" [{self.name}] Erreur: {e}")
                    time.sleep(30)  # Attendre 30s avant de réessayer
                    
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                print(f"🔌 [{self.name}] Déconnecté de Kafka")


# Point d'entrée
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Run CoinGecko agent")
    parser.add_argument("--interval", "-i", type=int, help="Intervalle de polling en secondes")
    args = parser.parse_args()

    # Priorité: CLI > ENV > fallback (30s pour démo)
    interval = None
    if args.interval is not None:
        interval = max(5, args.interval)
    elif os.getenv("COINGECKO_POLL_INTERVAL") and os.getenv("COINGECKO_POLL_INTERVAL").isdigit():
        interval = max(5, int(os.getenv("COINGECKO_POLL_INTERVAL")))
    else:
        interval = 30

    print(f" [CoinGeckoAgent] Lancement avec intervalle: {interval}s")
    agent = CoinGeckoAgent(poll_interval=interval)
    agent.run()