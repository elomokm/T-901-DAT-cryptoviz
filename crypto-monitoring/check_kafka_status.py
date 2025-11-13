#!/usr/bin/env python3
"""
Script rapide pour vérifier l'état de Kafka:
- Liste des topics
- Nombre de messages par topic
- Derniers offsets
"""
import os
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

def main():
    print("=" * 70)
    print(" VÉRIFICATION KAFKA")
    print("=" * 70)
    print(f"Broker: {KAFKA_BROKER}\n")
    
    try:
        # Créer un admin client
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
        
        # Lister les topics
        topics = admin.list_topics()
        print(f"📋 Topics disponibles: {len(topics)}")
        for topic in sorted(topics):
            if not topic.startswith('__'):  # Ignorer les topics internes
                print(f"  - {topic}")
        
        print()
        
        # Pour chaque topic, compter les messages
        for topic in sorted(topics):
            if topic.startswith('__'):
                continue
            
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=KAFKA_BROKER,
                    auto_offset_reset='earliest',
                    enable_auto_commit=False,
                    consumer_timeout_ms=100
                )
                
                # Récupérer les partitions
                partitions = consumer.partitions_for_topic(topic)
                if not partitions:
                    print(f"📊 Topic '{topic}': Aucune partition")
                    continue
                
                # Compter les messages
                total = 0
                for partition in partitions:
                    tp = consumer._client.cluster.leader_for_partition(consumer._client.cluster.topics()[topic][partition])
                    # Position de début et fin
                    consumer.seek_to_beginning()
                    beginning = consumer.position(consumer.partitions_for_topic(topic))
                    consumer.seek_to_end()
                    end = consumer.position(consumer.partitions_for_topic(topic))
                    # Pas fiable, utilisons une autre méthode
                
                # Méthode simple: lire depuis le début et compter
                consumer.seek_to_beginning()
                count = 0
                for _ in consumer:
                    count += 1
                    if count >= 10000:  # Limite pour éviter de bloquer
                        break
                
                consumer.close()
                
                if count > 0:
                    print(f"📊 Topic '{topic}': ~{count}+ messages")
                else:
                    print(f"📊 Topic '{topic}': Vide (0 messages)")
            
            except Exception as e:
                print(f"📊 Topic '{topic}': Erreur - {e}")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erreur de connexion à Kafka: {e}")
        print("\nVérifiez que:")
        print("  1. Kafka tourne (docker ps)")
        print("  2. Le port 9092 est accessible")
        print(f"  3. KAFKA_BROKER={KAFKA_BROKER} est correct")

if __name__ == "__main__":
    main()
