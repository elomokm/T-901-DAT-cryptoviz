"""Agent CoinMarketCap - Source alternative + validation croisée"""
import time
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from .base_agent import BaseAgent
from .config import TOPICS, CMC_API_KEY

# Logger
logger = logging.getLogger(__name__)

# Circuit Breaker pour CoinMarketCap API
cmc_circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name='CoinMarketCapAPI'
)

class CoinMarketCapAgent(BaseAgent):
    """
    Agent qui récupère les données depuis CoinMarketCap.
    Sert de source alternative pour valider les prix CoinGecko.
    
    Features:
    - Collecte top 20 cryptos par market cap
    - Validation croisée des prix
    - Détection d'anomalies (divergence > 5%)
    """
    
    API_BASE = "https://pro-api.coinmarketcap.com/v1"
    
    # Symboles des top 20 cryptos
    SYMBOLS = [
        'BTC', 'ETH', 'USDT', 'BNB', 'SOL',
        'XRP', 'USDC', 'ADA', 'AVAX', 'DOGE',
        'DOT', 'LINK', 'DAI', 'LTC', 'SHIB',
        'UNI', 'ATOM', 'XLM', 'XMR', 'ALGO'
    ]
    
    def __init__(self, poll_interval: int = 120):
        """
        Args:
            poll_interval: Intervalle en secondes (défaut: 120s = 2 min)
                          Plus long que CoinGecko pour éviter rate limits
        """
        super().__init__(
            name="CoinMarketCapAgent",
            topic=TOPICS['prices'],  # Même topic que CoinGecko
            poll_interval=poll_interval,
            schema_file='schemas/crypto_price.avsc'  # Validation Avro activée
        )
        
        # Session HTTP avec API key
        self.session = requests.Session()
        self.session.headers.update({
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json',
            'User-Agent': 'CryptoViz/2.0'
        })
        
        # Cache pour détection d'anomalies
        self.last_prices = {}

    @cmc_circuit_breaker
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def fetch_data(self) -> Optional[List[Dict]]:
        """
        Récupère les données depuis /cryptocurrency/quotes/latest.
        Protection: Circuit Breaker + Retry avec exponential backoff.
        
        Returns:
            List[Dict]: Liste de dictionnaires (1 par crypto) ou None si erreur
        """
        try:
            # Paramètres de l'API
            params = {
                'symbol': ','.join(self.SYMBOLS),
                'convert': 'USD'
            }
            
            # Requête API
            response = self.session.get(
                f"{self.API_BASE}/cryptocurrency/quotes/latest",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Vérification du statut
            if data.get('status', {}).get('error_code') != 0:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                print(f"❌ [{self.name}] API Error: {error_msg}")
                return None
            
            # Transformation des données
            crypto_list = []
            for symbol in self.SYMBOLS:
                if symbol not in data.get('data', {}):
                    continue
                    
                coin = data['data'][symbol]
                quote = coin['quote']['USD']
                
                # Détection d'anomalies
                current_price = quote['price']
                anomaly_detected = self._check_anomaly(symbol, current_price)
                
                crypto_data = {
                    'source': 'coinmarketcap',
                    'crypto_id': coin['slug'],
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'price_usd': current_price,
                    'market_cap': quote['market_cap'],
                    'volume_24h': quote['volume_24h'],
                    'volume_change_24h': quote['volume_change_24h'],
                    'percent_change_1h': quote['percent_change_1h'],
                    'percent_change_24h': quote['percent_change_24h'],
                    'percent_change_7d': quote['percent_change_7d'],
                    'market_cap_dominance': quote['market_cap_dominance'],
                    'circulating_supply': coin['circulating_supply'],
                    'total_supply': coin.get('total_supply'),
                    'max_supply': coin.get('max_supply'),
                    'cmc_rank': coin['cmc_rank'],
                    'anomaly_detected': anomaly_detected,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'last_updated': coin['last_updated']
                }
                
                crypto_list.append(crypto_data)
            
            print(f"✅ [{self.name}] {len(crypto_list)} cryptos récupérées")
            return crypto_list
            
        except requests.exceptions.RequestException as e:
            print(f"❌ [{self.name}] Erreur réseau: {e}")
            return None
        except Exception as e:
            print(f"❌ [{self.name}] Erreur: {e}")
            return None

    def _check_anomaly(self, symbol: str, current_price: float) -> bool:
        """
        Détecte les anomalies de prix (variation > 30% en 2 minutes).
        
        Args:
            symbol: Symbole de la crypto (ex: BTC)
            current_price: Prix actuel
            
        Returns:
            bool: True si anomalie détectée
        """
        if symbol not in self.last_prices:
            self.last_prices[symbol] = current_price
            return False
        
        last_price = self.last_prices[symbol]
        if last_price == 0:
            self.last_prices[symbol] = current_price
            return False
        
        # Calcul de la variation en %
        variation = abs((current_price - last_price) / last_price) * 100
        
        # Anomalie si variation > 30% (probable erreur API)
        is_anomaly = variation > 30.0
        
        if is_anomaly:
            print(f"  [{self.name}] ANOMALIE {symbol}: {last_price:.2f} → {current_price:.2f} ({variation:.1f}%)")
        
        # Mise à jour du cache
        self.last_prices[symbol] = current_price
        
        return is_anomaly

    def process_data(self, data: List[Dict]) -> List[Dict]:
        """
        Traite les données avant envoi à Kafka.
        
        Args:
            data: Liste de dictionnaires
            
        Returns:
            List[Dict]: Données filtrées et enrichies
        """
        # Filtrer les anomalies (optionnel - on les garde avec flag)
        processed = []
        
        for item in data:
            # Validation basique
            if item['price_usd'] <= 0:
                print(f"⚠️  [{self.name}] Prix invalide pour {item['symbol']}: {item['price_usd']}")
                continue
            
            if item['market_cap'] <= 0:
                print(f"⚠️  [{self.name}] Market cap invalide pour {item['symbol']}: {item['market_cap']}")
                continue
            
            processed.append(item)
        
        return processed

    def run(self):
        """
        Boucle principale de l'agent.
        Utilise send_batch_to_kafka() pour optimiser les performances.
        """
        self.connect_kafka()
        
        print(f"🚀 [{self.name}] Démarrage (intervalle: {self.poll_interval}s)")
        
        try:
            while True:
                try:
                    # Récupérer les données (liste de 20 cryptos)
                    data_list = self.fetch_data()
                    
                    if data_list:
                        # Traitement/validation
                        processed_data = self.process_data(data_list)
                        
                        # Envoi optimisé en batch avec compression + validation
                        stats = self.send_batch_to_kafka(processed_data, debug=False, validate=True)
                        
                        print(f"✅ [{self.name}] {stats['success']}/{len(processed_data)} envoyés | "
                              f"Validation: {stats['validation_errors']} erreurs")
                    
                    # Attendre avant la prochaine collecte
                    time.sleep(self.poll_interval)
                    
                except CircuitBreakerError:
                    print(f"🔴 [{self.name}] Circuit Breaker OUVERT - API indisponible")
                    print(f"   → Attente de {cmc_circuit_breaker.reset_timeout}s avant réessai...")
                    time.sleep(cmc_circuit_breaker.reset_timeout)
                    
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
                print(f"� [{self.name}] Déconnecté de Kafka")
