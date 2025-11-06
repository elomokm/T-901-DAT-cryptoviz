"""Classe de base pour tous les agents de scraping"""
import json
import time
from abc import ABC, abstractmethod
from kafka import KafkaProducer
from .config import KAFKA_BROKER, PRODUCER_CONFIG

class BaseAgent(ABC):
    """
    Classe abstraite pour les agents de scraping.
    Tous les agents doivent hériter de cette classe et implémenter run().
    """
    
    def __init__(self, name: str, topic: str, poll_interval: int = 300):
        """
        Args:
            name: Nom de l'agent (ex: "FearGreedAgent")
            topic: Topic Kafka où envoyer les données
            poll_interval: Intervalle en secondes entre chaque collecte
        """
        self.name = name
        self.topic = topic
        self.poll_interval = poll_interval
        self.producer = None
        
    def connect_kafka(self):
        """Crée la connexion au producer Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                **PRODUCER_CONFIG
            )
            print(f"✅ [{self.name}] Connecté à Kafka ({KAFKA_BROKER})")
        except Exception as e:
            print(f"❌ [{self.name}] Erreur Kafka: {e}")
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
            print(f"📤 [{self.name}] Envoyé vers {self.topic}: {data}")
        except Exception as e:
            print(f"❌ [{self.name}] Erreur d'envoi: {e}")
            raise
    
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
                    print(f"\n⏹️  [{self.name}] Arrêt demandé")
                    break
                except Exception as e:
                    print(f"⚠️  [{self.name}] Erreur: {e}")
                    time.sleep(10)  # Attendre 10s avant de réessayer
                    
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                print(f" [{self.name}] Déconnecté de Kafka")