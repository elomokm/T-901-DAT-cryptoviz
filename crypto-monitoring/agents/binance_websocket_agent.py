"""Agent Binance WebSocket - Données temps réel via WebSocket"""
import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List
import logging
import websocket
from .base_agent import BaseAgent
from .config import TOPICS

# Logger
logger = logging.getLogger(__name__)

class BinanceWebSocketAgent(BaseAgent):
    """
    Agent WebSocket pour Binance - Données temps réel (< 1s de latence).
    
    Features:
    - Streaming continu des prix (trades en temps réel)
    - Top 5 cryptos : BTC, ETH, SOL, BNB, ADA
    - Reconnexion automatique en cas de déconnexion
    - Buffer pour batch sending
    
    Architecture:
    - Thread principal : Gère le WebSocket (async)
    - Thread secondaire : Envoie les batches à Kafka périodiquement
    """
    
    # URL WebSocket Binance (streams combinés)
    WS_BASE = "wss://stream.binance.com:9443/stream"
    
    # Top 5 cryptos en notation Binance (paires vs USDT)
    TRADING_PAIRS = [
        'btcusdt',   # Bitcoin
        'ethusdt',   # Ethereum
        'solusdt',   # Solana
        'bnbusdt',   # Binance Coin
        'adausdt'    # Cardano
    ]
    
    # Mapping symbol → crypto_id (pour compatibilité avec CoinGecko)
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'BNB': 'binancecoin',
        'ADA': 'cardano'
    }
    
    def __init__(self, batch_interval: int = 5, enable_deduplication: bool = True):
        """
        Args:
            batch_interval: Intervalle en secondes pour envoyer les batches à Kafka (défaut: 5s)
            enable_deduplication: Activer le cache anti-duplications (défaut: True)
        """
        super().__init__(
            name="BinanceWebSocketAgent",
            topic=TOPICS['realtime'],  # crypto-realtime (topic séparé)
            poll_interval=batch_interval,
            schema_file=None  # Pas de validation Avro pour temps réel (performance)
        )
        
        self.batch_interval = batch_interval
        self.enable_deduplication = enable_deduplication
        self.ws = None
        self.is_running = False
        
        # Buffer pour accumuler les trades avant envoi batch
        self.trade_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Cache pour déduplication (dernier prix par crypto)
        # Format: {'bitcoin': {'price': 102250.5, 'timestamp': 1234567890}}
        self.price_cache = {}
        self.cache_lock = threading.Lock()
        
        # Métriques temps réel
        self.metrics = {
            'total_trades': 0,          # Total trades reçus
            'deduplicated_trades': 0,   # Trades filtrés (duplications)
            'sent_trades': 0,           # Trades envoyés à Kafka
            'reconnections': 0,         # Nombre de reconnexions
            'errors': 0,                # Erreurs
            'start_time': None          # Temps de démarrage
        }
        self.metrics_lock = threading.Lock()
        
        # Threads
        self.batch_thread = None
        self.heartbeat_thread = None
        self.last_message_time = time.time()
    
    def _build_subscribe_message(self) -> str:
        """
        Construit le message de souscription aux streams Binance.
        On s'abonne aux "trade streams" pour chaque paire.
        
        Returns:
            str: Message JSON à envoyer au WebSocket
        """
        streams = [f"{pair}@trade" for pair in self.TRADING_PAIRS]
        
        message = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": 1
        }
        
        return json.dumps(message)
    
    def _should_send_trade(self, crypto_id: str, price: float, threshold: float = 0.0001) -> bool:
        """
        Vérifie si le trade doit être envoyé (cache anti-duplication).
        Ignore les variations < 0.01% pour réduire le bruit.
        
        Args:
            crypto_id: ID de la crypto (ex: 'bitcoin')
            price: Prix actuel
            threshold: Seuil de variation minimal (0.0001 = 0.01%)
            
        Returns:
            bool: True si le trade doit être envoyé
        """
        if not self.enable_deduplication:
            return True
        
        with self.cache_lock:
            # Pas de cache → envoyer
            if crypto_id not in self.price_cache:
                self.price_cache[crypto_id] = {'price': price, 'timestamp': time.time()}
                return True
            
            # Calculer variation
            last_price = self.price_cache[crypto_id]['price']
            variation = abs(price - last_price) / last_price
            
            # Variation > seuil → envoyer et mettre à jour cache
            if variation >= threshold:
                self.price_cache[crypto_id] = {'price': price, 'timestamp': time.time()}
                return True
            
            # Variation trop faible → skip
            return False
    
    def _parse_trade(self, trade_data: Dict) -> Optional[Dict]:
        """
        Parse un événement trade Binance et le transforme en format compatible.
        
        Args:
            trade_data: Données brutes du trade Binance
            
        Returns:
            dict: Trade formaté ou None si erreur/duplication
        """
        try:
            # Mettre à jour métriques
            with self.metrics_lock:
                self.metrics['total_trades'] += 1
            
            # Extraire le symbol (ex: BTCUSDT → BTC)
            symbol = trade_data['s'].replace('USDT', '')
            
            # Vérifier que c'est une paire qu'on suit
            if symbol not in self.SYMBOL_TO_ID:
                return None
            
            crypto_id = self.SYMBOL_TO_ID[symbol]
            price = float(trade_data['p'])
            
            # Vérifier déduplication (ignore variations < 0.01%)
            if not self._should_send_trade(crypto_id, price):
                with self.metrics_lock:
                    self.metrics['deduplicated_trades'] += 1
                return None
            
            # Formatter les données
            formatted = {
                'source': 'binance_websocket',
                'crypto_id': crypto_id,
                'symbol': symbol,
                'name': crypto_id.capitalize(),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                
                # Prix du trade
                'price_usd': price,
                
                # Métadonnées du trade
                'quantity': float(trade_data['q']),  # Quantité tradée
                'trade_time': trade_data['T'],        # Timestamp du trade (ms)
                'is_buyer_maker': trade_data['m'],    # True = vente, False = achat
                
                # Pas de market cap/volume (données temps réel seulement)
                'market_cap': None,
                'volume_24h': None,
                'percent_change_24h': None,
            }
            
            return formatted
            
        except Exception as e:
            logger.error(f"[{self.name}] Erreur parsing trade: {e}")
            with self.metrics_lock:
                self.metrics['errors'] += 1
            return None
    
    def _on_message(self, ws, message):
        """
        Callback appelé quand un message WebSocket arrive.
        
        Args:
            ws: Instance WebSocket
            message: Message brut (JSON string)
        """
        try:
            # Mettre à jour timestamp (pour heartbeat)
            self.last_message_time = time.time()
            
            data = json.loads(message)
            
            # Ignorer les messages de confirmation d'abonnement
            if 'result' in data or 'id' in data:
                return
            
            # Extraire les données du trade
            if 'data' in data:
                trade_data = data['data']
                
                # Parser et ajouter au buffer
                formatted_trade = self._parse_trade(trade_data)
                if formatted_trade:
                    with self.buffer_lock:
                        self.trade_buffer.append(formatted_trade)
                        
        except Exception as e:
            logger.error(f"[{self.name}] Erreur dans on_message: {e}")
            with self.metrics_lock:
                self.metrics['errors'] += 1
    
    def _on_error(self, ws, error):
        """Callback erreur WebSocket"""
        logger.error(f"❌ [{self.name}] WebSocket error: {error}")
        with self.metrics_lock:
            self.metrics['errors'] += 1
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Callback fermeture WebSocket"""
        logger.warning(f"🔌 [{self.name}] WebSocket fermé: {close_status_code} - {close_msg}")
        
        # Réessayer si on est encore en mode running
        if self.is_running:
            with self.metrics_lock:
                self.metrics['reconnections'] += 1
            logger.info(f"🔄 [{self.name}] Reconnexion #{self.metrics['reconnections']} dans 5s...")
            time.sleep(5)
            self._connect_websocket()
    
    def _heartbeat_loop(self):
        """
        Thread qui vérifie la santé de la connexion WebSocket.
        Vérifie toutes les 30s si on a reçu des messages récemment.
        """
        logger.info(f" [{self.name}] Thread heartbeat démarré (check toutes les 30s)")
        
        while self.is_running:
            try:
                time.sleep(30)
                
                # Vérifier si on a reçu un message récemment
                time_since_last_msg = time.time() - self.last_message_time
                
                if time_since_last_msg > 60:
                    # Pas de message depuis 60s → connexion probablement morte
                    logger.warning(f"⚠️  [{self.name}] Pas de message depuis {time_since_last_msg:.0f}s "
                                  f"→ Reconnexion...")
                    if self.ws:
                        self.ws.close()
                else:
                    logger.debug(f"💓 [{self.name}] Heartbeat OK (dernier message: {time_since_last_msg:.1f}s)")
                    
            except Exception as e:
                logger.error(f"⚠️  [{self.name}] Erreur heartbeat: {e}")
    
    def _on_open(self, ws):
        """Callback ouverture WebSocket"""
        print(f"✅ [{self.name}] WebSocket connecté à Binance")
        
        # S'abonner aux streams
        subscribe_msg = self._build_subscribe_message()
        ws.send(subscribe_msg)
        print(f"📡 [{self.name}] Abonné à {len(self.TRADING_PAIRS)} paires: {', '.join(self.TRADING_PAIRS)}")
    
    def _connect_websocket(self):
        """Crée et démarre la connexion WebSocket"""
        try:
            # Créer l'instance WebSocket
            self.ws = websocket.WebSocketApp(
                self.WS_BASE,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Lancer dans un thread dédié (bloquant)
            self.ws.run_forever()
            
        except Exception as e:
            logger.error(f"❌ [{self.name}] Erreur connexion WebSocket: {e}")
            if self.is_running:
                time.sleep(5)
                self._connect_websocket()
    
    def fetch_data(self) -> List[Dict]:
        """
        Méthode abstraite requise par BaseAgent.
        Non utilisée car on stream en continu (pas de polling).
        
        Returns:
            list: Liste vide (pas de polling, WebSocket stream)
        """
        return []
    
    def _batch_sender_loop(self):
        """
        Thread qui envoie périodiquement les trades accumulés à Kafka.
        Tourne en boucle tant que is_running = True.
        """
        print(f"🔄 [{self.name}] Thread batch sender démarré (intervalle: {self.batch_interval}s)")
        
        while self.is_running:
            try:
                time.sleep(self.batch_interval)
                
                # Copier et vider le buffer (thread-safe)
                with self.buffer_lock:
                    if not self.trade_buffer:
                        continue  # Rien à envoyer
                    
                    trades_to_send = self.trade_buffer.copy()
                    self.trade_buffer.clear()
                
                # Envoyer en batch à Kafka
                if trades_to_send:
                    stats = self.send_batch_to_kafka(trades_to_send, debug=False, validate=False)
                    
                    # Mettre à jour métriques
                    with self.metrics_lock:
                        self.metrics['sent_trades'] += stats['success']
                    
                    # Calculer taux de déduplication
                    dedup_rate = (self.metrics['deduplicated_trades'] / 
                                 max(self.metrics['total_trades'], 1)) * 100
                    
                    # Calculer trades/s
                    uptime = time.time() - self.metrics['start_time']
                    trades_per_sec = self.metrics['sent_trades'] / uptime
                    
                    print(f"📦 [{self.name}] Envoyé {stats['success']}/{len(trades_to_send)} trades "
                          f"({stats['duration_ms']:.1f}ms) | "
                          f"Dédup: {dedup_rate:.1f}% | "
                          f"Rate: {trades_per_sec:.1f} trades/s")
                    
            except Exception as e:
                logger.error(f"⚠️  [{self.name}] Erreur batch sender: {e}")
                with self.metrics_lock:
                    self.metrics['errors'] += 1
    
    def run(self):
        """
        Démarre l'agent WebSocket.
        Lance 3 threads :
        - Thread 1 : Connexion WebSocket (reçoit les trades)
        - Thread 2 : Envoi périodique des batches à Kafka
        - Thread 3 : Heartbeat (vérifie santé connexion)
        """
        self.is_running = True
        
        # Initialiser métriques
        with self.metrics_lock:
            self.metrics['start_time'] = time.time()
        
        print(f"🚀 [{self.name}] Démarrage (batch: {self.batch_interval}s, dedup: {self.enable_deduplication})")
        
        # Connecter à Kafka
        self.connect_kafka()
        
        # Démarrer le thread d'envoi batch
        self.batch_thread = threading.Thread(target=self._batch_sender_loop, daemon=True)
        self.batch_thread.start()
        
        # Démarrer le thread heartbeat
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        # Démarrer le WebSocket (bloquant)
        try:
            self._connect_websocket()
        except KeyboardInterrupt:
            print(f"\n⏹️  [{self.name}] Arrêt demandé")
            self.stop()
    
    def stop(self):
        """Arrête proprement l'agent"""
        print(f"🛑 [{self.name}] Arrêt en cours...")
        self.is_running = False
        
        # Afficher statistiques finales
        uptime = time.time() - self.metrics['start_time']
        print(f"\n📊 Statistiques finales:")
        print(f"   Uptime: {uptime:.1f}s")
        print(f"   Total trades reçus: {self.metrics['total_trades']}")
        print(f"   Trades dédupliqués: {self.metrics['deduplicated_trades']} "
              f"({self.metrics['deduplicated_trades']/max(self.metrics['total_trades'],1)*100:.1f}%)")
        print(f"   Trades envoyés: {self.metrics['sent_trades']}")
        print(f"   Rate moyen: {self.metrics['sent_trades']/uptime:.1f} trades/s")
        print(f"   Reconnexions: {self.metrics['reconnections']}")
        print(f"   Erreurs: {self.metrics['errors']}")
        
        # Fermer le WebSocket
        if self.ws:
            self.ws.close()
        
        # Envoyer les derniers trades dans le buffer
        with self.buffer_lock:
            if self.trade_buffer:
                print(f"📤 [{self.name}] Envoi des derniers {len(self.trade_buffer)} trades...")
                self.send_batch_to_kafka(self.trade_buffer, debug=False, validate=False)
                self.trade_buffer.clear()
        
        # Fermer Kafka
        if self.producer:
            self.producer.flush()
            self.producer.close()
        
        print(f"✅ [{self.name}] Arrêté proprement")


# Point d'entrée
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    agent = BinanceWebSocketAgent(batch_interval=5)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
