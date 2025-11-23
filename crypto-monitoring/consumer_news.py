#!/usr/bin/env python3
"""
Spark Structured Streaming Consumer - Crypto News
Consomme le topic 'crypto-news' et stocke dans InfluxDB
"""
import os
import json
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration InfluxDB
INFLUX_URL = os.getenv('INFLUX_URL', 'http://localhost:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'crypto-org')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'crypto-data')

# Configuration Kafka
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = 'crypto-news'

# Configuration Spark
BATCH_SIZE = int(os.getenv('INFLUX_BATCH_SIZE', 50))

# Client InfluxDB global
influx_client = None
write_api = None


def get_influx_client():
    """Initialise et retourne le client InfluxDB"""
    global influx_client, write_api

    if influx_client is None:
        influx_client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        print(f"✅ InfluxDB connecté: {INFLUX_URL}")

    return influx_client, write_api


def analyze_sentiment(text):
    """
    Analyse le sentiment d'un texte (titre + description).
    Retourne: 'positive', 'negative', ou 'neutral'
    Score: -1.0 (très négatif) à +1.0 (très positif)
    """
    if not text:
        return 'neutral', 0.0

    text_lower = text.lower()

    # Mots-clés positifs
    positive_keywords = [
        'surge', 'soar', 'rally', 'bullish', 'gain', 'rise', 'up', 'boom',
        'breakthrough', 'adoption', 'success', 'profit', 'growth', 'all-time high',
        'ath', 'record', 'moon', 'pump', 'institutional', 'mainstream'
    ]

    # Mots-clés négatifs
    negative_keywords = [
        'crash', 'plunge', 'drop', 'fall', 'bearish', 'decline', 'down', 'loss',
        'scam', 'hack', 'exploit', 'vulnerability', 'ban', 'regulation', 'crackdown',
        'collapse', 'panic', 'dump', 'risk', 'warning', 'lawsuit'
    ]

    # Compter les occurrences
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

    # Calculer le score
    total_keywords = positive_count + negative_count
    if total_keywords == 0:
        return 'neutral', 0.0

    score = (positive_count - negative_count) / max(total_keywords, 1)

    # Déterminer le sentiment
    if score > 0.2:
        sentiment = 'positive'
    elif score < -0.2:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    return sentiment, score


def write_news_to_influx(batch_df, batch_id):
    """
    Écrit un batch de news dans InfluxDB avec analyse de sentiment.

    Args:
        batch_df: DataFrame Spark contenant les news
        batch_id: ID du batch Spark
    """
    # Convertir le DataFrame en liste de dicts
    rows = batch_df.collect()

    if not rows:
        print(f"ℹ️  Batch {batch_id}: Aucune news à écrire")
        return

    print(f"\n📝 Batch {batch_id}: Écriture de {len(rows)} news dans InfluxDB...")

    # Obtenir le client InfluxDB
    _, write_api = get_influx_client()

    # Créer les points InfluxDB
    points = []
    sentiment_stats = {'positive': 0, 'negative': 0, 'neutral': 0}

    for row in rows:
        try:
            # Analyser le sentiment
            text = f"{row.title} {row.description if row.description else ''}"
            sentiment, sentiment_score = analyze_sentiment(text)
            sentiment_stats[sentiment] += 1

            # Créer un point InfluxDB
            point = (
                Point("crypto_news")
                .tag("source", row.source)
                .tag("sentiment", sentiment)
                .field("title", row.title)
                .field("link", row.link)
                .field("description", row.description if row.description else "")
                .field("image_url", row.image_url if row.image_url else "")
                .field("sentiment_score", float(sentiment_score))
                .time(row.published_date)
            )
            points.append(point)

        except Exception as e:
            print(f"⚠️  Erreur création point pour article '{row.title}': {e}")
            continue

    # Écrire en batch
    if points:
        try:
            write_api.write(bucket=INFLUX_BUCKET, record=points)
            print(f"✅ Batch {batch_id}: {len(points)} news écrites dans InfluxDB")
            print(f"   📊 Sentiment: {sentiment_stats['positive']} positive, {sentiment_stats['negative']} negative, {sentiment_stats['neutral']} neutral")
        except Exception as e:
            print(f"❌ Batch {batch_id}: Erreur écriture InfluxDB: {e}")


def main():
    """Lance le consumer Spark Streaming pour les news"""

    print("=" * 70)
    print("🗞️  SPARK CONSUMER - Crypto News (crypto-news topic)")
    print("=" * 70)
    print(f"📡 Kafka Broker: {KAFKA_BROKER}")
    print(f"📊 InfluxDB: {INFLUX_URL}")
    print(f"🪣 Bucket: {INFLUX_BUCKET}")
    print(f"📦 Batch Size: {BATCH_SIZE}")
    print("=" * 70)
    print()

    # Créer la session Spark
    spark = SparkSession.builder \
        .appName("CryptoNewsConsumer") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Schéma des messages news
    news_schema = StructType([
        StructField("title", StringType(), True),
        StructField("link", StringType(), True),
        StructField("published_date", StringType(), True),
        StructField("source", StringType(), True),
        StructField("description", StringType(), True),
        StructField("image_url", StringType(), True),
        StructField("timestamp", StringType(), True),
    ])

    # Lire depuis Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    # Parser le JSON
    news_df = df.select(
        from_json(col("value").cast("string"), news_schema).alias("data")
    ).select("data.*")

    print("🚀 Consumer démarré, en attente de news...")
    print("   (Ctrl+C pour arrêter)")
    print()

    # Écrire dans InfluxDB
    query = news_df \
        .writeStream \
        .foreachBatch(write_news_to_influx) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/spark-checkpoint-news") \
        .trigger(processingTime=f"{BATCH_SIZE} seconds") \
        .start()

    # Attendre l'arrêt
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du consumer...")
        query.stop()
        if influx_client:
            influx_client.close()
        spark.stop()
        print("👋 Consumer arrêté")


if __name__ == "__main__":
    main()
