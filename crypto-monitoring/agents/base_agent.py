"""
Base Agent for Market Data Feed Collectors
Abstract class implementing the Producer pattern for cryptocurrency data collection
All data feed collectors inherit from this base class
"""
import json
import time
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path
from kafka import KafkaProducer
from .config import KAFKA_BROKER, PRODUCER_CONFIG

# Import Avro pour validation
try:
    import avro.schema
    import avro.io
    AVRO_AVAILABLE = True
except ImportError:
    AVRO_AVAILABLE = False
    print("  avro-python3 non installé - Validation désactivée")

class BaseAgent(ABC):
    """
    Base class for all Market Data Feed Collectors (Producer pattern).

    This abstract class provides the foundation for cryptocurrency data collection agents.
    Implements the Producer side of the Producer/Consumer paradigm by:
    - Continuously collecting data from external sources (APIs, RSS feeds, WebSockets)
    - Validating data against Avro schemas
    - Sending data to Kafka topics for stream processing

    All feed collectors must inherit from this class and implement fetch_data().
    """
    
    def __init__(self, name: str, topic: str, poll_interval: int = 300, schema_file: Optional[str] = None):
        """
        Args:
            name: Nom de l'agent (ex: "FearGreedAgent")
            topic: Topic Kafka où envoyer les données
            poll_interval: Intervalle en secondes entre chaque collecte
            schema_file: Chemin vers le schéma Avro (.avsc) pour validation (optionnel)
        """
        self.name = name
        self.topic = topic
        self.poll_interval = poll_interval
        self.producer = None
        self.schema = None
        
        # Charger le schéma Avro si fourni
        if schema_file and AVRO_AVAILABLE:
            self._load_schema(schema_file)
    
    def _load_schema(self, schema_file: str):
        """Charge un schéma Avro depuis un fichier .avsc"""
        try:
            schema_path = Path(__file__).parent.parent / schema_file
            with open(schema_path, 'r') as f:
                schema_dict = json.load(f)
                self.schema = avro.schema.parse(json.dumps(schema_dict))
                print(f" [{self.name}] Schéma Avro chargé: {schema_file}")
        except Exception as e:
            print(f"  [{self.name}] Impossible de charger le schéma {schema_file}: {e}")
            self.schema = None
    
    def validate_data(self, data: dict) -> tuple[bool, Optional[str]]:
        """
        Valide un dictionnaire contre le schéma Avro.
        
        Args:
            data: Dictionnaire à valider
            
        Returns:
            (is_valid, error_message): Tuple (bool, str ou None)
        """
        if not self.schema or not AVRO_AVAILABLE:
            return True, None  # Pas de validation si pas de schéma
        
        try:
            # Vérifier que toutes les clés obligatoires sont présentes
            # et que les types correspondent
            import io
            writer = avro.io.DatumWriter(self.schema)
            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)
            writer.write(data, encoder)
            return True, None
        except Exception as e:
            return False, str(e)
        
    def connect_kafka(self):
        """Crée la connexion au producer Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                **PRODUCER_CONFIG
            )
            print(f" [{self.name}] Connecté à Kafka ({KAFKA_BROKER})")
        except Exception as e:
            print(f" [{self.name}] Erreur Kafka: {e}")
            raise
    
    def send_to_kafka(self, data: dict):
        """
        Envoie des données à Kafka
        
        Args:
            data: Dictionnaire Python (sera converti en JSON)
        """
        if not self.producer:
            raise RuntimeError("Producer Kafka non initialisé. Appelez connect_kafka() d'abord.")
        
        try:
            future = self.producer.send(self.topic, value=data)
            future.get(timeout=10)  # Bloque jusqu'à confirmation
            print(f" [{self.name}] Envoyé vers {self.topic}: {data}")
        except Exception as e:
            print(f" [{self.name}] Erreur d'envoi: {e}")
            raise
    
    def send_batch_to_kafka(self, data_list: List[dict], debug: bool = False, validate: bool = True) -> Dict:
        """
        Envoie plusieurs messages en batch (async) pour optimiser les performances.
        
        Avantages:
        - Validation Avro avant envoi (optionnel)
        - Envoi asynchrone (pas d'attente entre chaque message)
        - Vérification des erreurs à la fin
        - Kafka batching automatique côté producer
        
        Args:
            data_list: Liste de dictionnaires à envoyer
            debug: Afficher les stats de performance (default: False)
            validate: Valider avec schéma Avro avant envoi (default: True)
        
        Returns:
            dict: Stats {'success': int, 'errors': int, 'validation_errors': int, 'duration_ms': float}
        """
        if not self.producer:
            raise RuntimeError("Producer Kafka non initialisé. Appelez connect_kafka() d'abord.")
        
        start_time = time.time()
        futures = []
        errors = []
        validation_errors = 0
        
        # Phase 1: Validation + Envoi asynchrone
        for data in data_list:
            # Validation Avro (si activée et schéma disponible)
            if validate and self.schema:
                is_valid, error_msg = self.validate_data(data)
                if not is_valid:
                    crypto_id = data.get('crypto_id', 'unknown')
                    print(f"  [{self.name}] Validation échouée pour {crypto_id}: {error_msg}")
                    validation_errors += 1
                    continue  # Skip ce message invalide
            
            # Envoi asynchrone
            try:
                future = self.producer.send(self.topic, value=data)
                futures.append((future, data))
            except Exception as e:
                errors.append((data, str(e)))
        
        # Phase 2: Vérifier les résultats de chaque envoi
        for future, data in futures:
            try:
                # Attendre la confirmation (avec timeout)
                future.get(timeout=10)
            except Exception as e:
                errors.append((data, str(e)))
        
        duration_ms = (time.time() - start_time) * 1000
        success_count = len(data_list) - len(errors) - validation_errors
        
        # Stats de debugging (optionnel)
        if debug:
            print(f" [{self.name}] Batch envoyé: {success_count}/{len(data_list)} succès en {duration_ms:.1f}ms")
            if validation_errors > 0:
                print(f"  [{self.name}] {validation_errors} erreurs de validation")
            if errors:
                print(f"  [{self.name}] {len(errors)} erreurs d'envoi")
        
        # Logger les erreurs d'envoi (toujours, même sans debug)
        for failed_data, error in errors:
            crypto_id = failed_data.get('crypto_id', 'unknown')
            print(f" [{self.name}] Échec envoi {crypto_id}: {error}")
        
        return {
            'success': success_count,
            'errors': len(errors),
            'validation_errors': validation_errors,
            'duration_ms': round(duration_ms, 2)
        }
    
    @abstractmethod
    def fetch_data(self):
        """
        Méthode abstraite : chaque agent doit implémenter sa logique de collecte.
        
        Returns:
            dict: Données collectées
        """
        pass
    
    def run(self):
        """
        Boucle principale de l'agent.
        Collecte les données et les envoie à Kafka en continu.
        """
        self.connect_kafka()
        
        print(f" [{self.name}] Démarrage (intervalle: {self.poll_interval}s)")
        
        try:
            while True:
                try:
                    # Collecter les données (implémenté par chaque agent)
                    data = self.fetch_data()
                    
                    # Envoyer à Kafka
                    if data:
                        self.send_to_kafka(data)
                    
                    # Attendre avant la prochaine collecte
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    print(f"\n  [{self.name}] Arrêt demandé")
                    break
                except Exception as e:
                    print(f"  [{self.name}] Erreur: {e}")
                    time.sleep(10)  # Attendre 10s avant de réessayer
                    
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                print(f" [{self.name}] Déconnecté de Kafka")