"""Agent CoinMarketCap - Collecte prix et métadonnées"""
import os
import sys
import time
import logging
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
from pybreaker import CircuitBreaker

# Import helpers
try:
    from agents.base_agent import BaseAgent
    from agents.config import TOPICS, CMC_API_KEY
except ImportError:
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from agents.base_agent import BaseAgent
    from agents.config import TOPICS, CMC_API_KEY

logger = logging.getLogger(__name__)

api_circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name='CoinMarketCapAPI'
)

def _to_float(v) -> Optional[float]:
    """Convertit en float ou retourne None"""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _to_int(v) -> Optional[int]:
    """Convertit en int ou retourne None"""
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

class CoinMarketCapAgent(BaseAgent):
    """Agent qui récupère les données depuis CoinMarketCap"""
    
    API_BASE = "https://pro-api.coinmarketcap.com/v1"
    
    def __init__(self, poll_interval: int = 60):
        super().__init__(
            name="CoinMarketCapAgent",
            topic=TOPICS['prices'],
            poll_interval=poll_interval,
            schema_file='schemas/crypto_price.avsc'
        )
        
        self.api_key = CMC_API_KEY
        if not self.api_key:
            raise ValueError("CMC_API_KEY manquante dans config.py ou .env")
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        })
    
    @api_circuit_breaker
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _call_api(self) -> Dict:
        """Appel à l'API CoinMarketCap"""
        url = f"{self.API_BASE}/cryptocurrency/listings/latest"
        params = {
            'limit': 20,
            'convert': 'USD',
            'sort': 'market_cap'
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def fetch_data(self) -> List[Dict]:
        """
        Récupère et transforme les données CMC pour le schéma Avro unifié.
        Mappe tous les champs requis + optionnels du schéma crypto_price.avsc
        """
        try:
            api_response = self._call_api()
            data = api_response.get('data', [])
            
            if not data:
                print(f"⚠️ [{self.name}] Aucune donnée reçue de CoinMarketCap")
                return []
            
            timestamp = datetime.now(timezone.utc).isoformat()
            enriched = []
            
            for coin in data:
                # Quote USD (contient prix, market_cap, volume, variations)
                quote = (coin.get('quote') or {}).get('USD') or {}
                
                # Mapping vers le schéma unifié
                record = {
                    # ===== Champs obligatoires =====
                    "source": "coinmarketcap",
                    "crypto_id": (coin.get('slug') or '').lower(),  # ex: "bitcoin"
                    "symbol": (coin.get('symbol') or '').upper(),   # ex: "BTC"
                    "timestamp": timestamp,
                    "price_usd": _to_float(quote.get('price')) or 0.0,  # obligatoire, fallback 0
                    
                    # ===== Champs optionnels (avec default=null) =====
                    "name": coin.get('name'),  # ex: "Bitcoin"
                    "market_cap": _to_float(quote.get('market_cap')),
                    "volume_24h": _to_float(quote.get('volume_24h')),
                    "market_cap_rank": _to_int(coin.get('cmc_rank')),
                    
                    # Variations (CMC fournit 1h, 24h, 7d, 30d, 60d, 90d)
                    "change_1h": _to_float(quote.get('percent_change_1h')),
                    "change_24h": _to_float(quote.get('percent_change_24h')),
                    "percent_change_24h": _to_float(quote.get('percent_change_24h')),  # alias
                    "change_7d": _to_float(quote.get('percent_change_7d')),
                    
                    # Supply
                    "circulating_supply": _to_float(coin.get('circulating_supply')),
                    "total_supply": _to_float(coin.get('total_supply')),
                    "max_supply": _to_float(coin.get('max_supply')),
                    
                    # ATH/ATL: CMC ne fournit pas via /listings/latest → None
                    # (nécessiterait un appel séparé à /quotes/historical)
                    "ath": None,
                    "ath_date": None,
                    "ath_change_pct": None,
                    "atl": None,
                    "atl_date": None,
                    "atl_change_pct": None,
                    
                    # Anomalies (sera calculé par un agent de validation)
                    "anomaly_detected": None,
                }
                
                enriched.append(record)
            
            print(f" [{self.name}] Récupéré {len(enriched)} cryptos")
            return enriched
            
        except Exception as e:
            print(f" [{self.name}] Erreur fetch_data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def run(self):
        """Boucle principale"""
        self.connect_kafka()
        
        print(f" [{self.name}] Démarrage (intervalle: {self.poll_interval}s)")
        
        try:
            while True:
                try:
                    data_list = self.fetch_data()
                    if data_list:
                        stats = self.send_batch_to_kafka(data_list, debug=True, validate=True)
                        print(f"✅ [{self.name}] {stats['success']}/{len(data_list)} envoyés | "
                              f"Validation: {stats['validation_errors']} erreurs")
                    
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    print(f"\n[{self.name}] Arrêt demandé")
                    break
                    
                except Exception as e:
                    print(f"❌ [{self.name}] Erreur: {e}")
                    time.sleep(30)
                    
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                print(f" [{self.name}] Déconnecté de Kafka")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run CoinMarketCap agent")
    parser.add_argument("--interval", "-i", type=int, help="Intervalle de polling en secondes")
    args = parser.parse_args()
    
    # Priorité: CLI > ENV > fallback
    interval = None
    if args.interval is not None:
        interval = max(5, args.interval)
    elif os.getenv("COINMARKETCAP_POLL_INTERVAL") and os.getenv("COINMARKETCAP_POLL_INTERVAL").isdigit():
        interval = max(5, int(os.getenv("COINMARKETCAP_POLL_INTERVAL")))
    else:
        interval = 30  # fallback démo
    
    print(f"🚀 [CoinMarketCapAgent] Lancement avec intervalle: {interval}s")
    agent = CoinMarketCapAgent(poll_interval=interval)
    agent.run()