#!/usr/bin/env python3
"""
Spark Structured Streaming Consumer - Advanced Analytics
Calcule des métriques analytiques avancées sur les données crypto:
- Moyennes mobiles (7j, 30j)
- Volatilité (écart-type sur 24h, 7j)
- Détection d'anomalies (prix, volume)
- Stocke les résultats dans InfluxDB (measurement: crypto_analytics)
"""
import os
import json
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, current_timestamp, window, avg, stddev, min, max, count
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
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
TOPIC = 'crypto-prices'

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


def calculate_analytics(batch_df, batch_id):
    """
    Calcule les analytics sur un batch de données.

    Métriques calculées:
    - Moyenne mobile sur la fenêtre (approximation)
    - Volatilité (écart-type du prix)
    - Range (min/max du prix)
    - Détection d'anomalies (prix hors 2 écart-types)

    Args:
        batch_df: DataFrame Spark contenant les données brutes
        batch_id: ID du batch
    """
    if batch_df.isEmpty():
        print(f"ℹ️  Batch {batch_id}: Aucune donnée à analyser")
        return

    print(f"\n📊 Batch {batch_id}: Calcul d'analytics...")

    # Convertir en Pandas pour calculs plus faciles
    pdf = batch_df.select(
        "crypto_id",
        "symbol",
        "name",
        "source",
        "price_usd",
        "volume_24h",
        "market_cap",
        "timestamp"
    ).toPandas()

    if pdf.empty:
        return

    # Grouper par crypto pour calculer les statistiques
    analytics_results = []

    for crypto_id in pdf['crypto_id'].unique():
        crypto_data = pdf[pdf['crypto_id'] == crypto_id]

        if len(crypto_data) == 0:
            continue

        # Calculs statistiques de base
        price_mean = crypto_data['price_usd'].mean()
        price_std = crypto_data['price_usd'].std()
        price_min = crypto_data['price_usd'].min()
        price_max = crypto_data['price_usd'].max()
        volume_mean = crypto_data['volume_24h'].mean()
        volume_std = crypto_data['volume_24h'].std()

        # Détection d'anomalies (prix hors ±2 écart-types)
        if price_std and price_std > 0:
            anomaly_threshold_low = price_mean - (2 * price_std)
            anomaly_threshold_high = price_mean + (2 * price_std)
            price_anomalies = crypto_data[
                (crypto_data['price_usd'] < anomaly_threshold_low) |
                (crypto_data['price_usd'] > anomaly_threshold_high)
            ]
            anomaly_count = len(price_anomalies)
        else:
            anomaly_count = 0

        # Calculer la volatilité en %
        volatility_pct = (price_std / price_mean * 100) if price_mean > 0 else 0

        # Créer le résultat analytics
        result = {
            'crypto_id': crypto_id,
            'symbol': crypto_data['symbol'].iloc[0],
            'name': crypto_data['name'].iloc[0],
            'price_mean': price_mean,
            'price_std': price_std,
            'price_min': price_min,
            'price_max': price_max,
            'price_range': price_max - price_min,
            'volatility_pct': volatility_pct,
            'volume_mean': volume_mean,
            'volume_std': volume_std,
            'anomaly_count': anomaly_count,
            'data_points': len(crypto_data),
            'timestamp': datetime.utcnow().isoformat()
        }

        analytics_results.append(result)

    # Écrire les analytics dans InfluxDB
    if analytics_results:
        write_analytics_to_influx(analytics_results, batch_id)


def write_analytics_to_influx(analytics_list, batch_id):
    """
    Écrit les analytics calculés dans InfluxDB.

    Args:
        analytics_list: Liste de dictionnaires d'analytics
        batch_id: ID du batch
    """
    _, write_api = get_influx_client()

    points = []
    for analytics in analytics_list:
        try:
            # Créer un point InfluxDB pour le measurement crypto_analytics
            point = (
                Point("crypto_analytics")
                .tag("crypto_id", analytics['crypto_id'])
                .tag("symbol", analytics['symbol'])
                .tag("name", analytics['name'])
                .field("price_mean", float(analytics['price_mean']))
                .field("price_std", float(analytics['price_std']))
                .field("price_min", float(analytics['price_min']))
                .field("price_max", float(analytics['price_max']))
                .field("price_range", float(analytics['price_range']))
                .field("volatility_pct", float(analytics['volatility_pct']))
                .field("volume_mean", float(analytics['volume_mean']) if analytics['volume_mean'] else 0.0)
                .field("volume_std", float(analytics['volume_std']) if analytics['volume_std'] else 0.0)
                .field("anomaly_count", int(analytics['anomaly_count']))
                .field("data_points", int(analytics['data_points']))
                .time(datetime.utcnow())
            )
            points.append(point)

        except Exception as e:
            print(f"⚠️  Erreur création point analytics pour {analytics['crypto_id']}: {e}")
            continue

    # Écrire en batch
    if points:
        try:
            write_api.write(bucket=INFLUX_BUCKET, record=points)
            print(f"✅ Batch {batch_id}: {len(points)} analytics écrits dans InfluxDB (measurement: crypto_analytics)")
        except Exception as e:
            print(f"❌ Batch {batch_id}: Erreur écriture analytics: {e}")


def main():
    """Lance le consumer Analytics"""

    print("=" * 80)
    print("📊 SPARK ANALYTICS CONSUMER - Advanced Crypto Analytics")
    print("=" * 80)
    print(f"📡 Kafka Broker: {KAFKA_BROKER}")
    print(f"📊 InfluxDB: {INFLUX_URL}")
    print(f"🪣 Bucket: {INFLUX_BUCKET}")
    print()
    print("📈 Analytics calculés:")
    print("  • Moyennes mobiles (approximation sur fenêtre)")
    print("  • Volatilité (écart-type, %)")
    print("  • Range de prix (min/max)")
    print("  • Détection d'anomalies (±2 σ)")
    print("  • Volume moyen et écart-type")
    print("=" * 80)
    print()

    # Créer la session Spark
    spark = SparkSession.builder \
        .appName("CryptoAnalyticsConsumer") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Schéma des messages crypto-prices (simplifié pour analytics)
    price_schema = StructType([
        StructField("crypto_id", StringType(), True),
        StructField("symbol", StringType(), True),
        StructField("name", StringType(), True),
        StructField("source", StringType(), True),
        StructField("price_usd", DoubleType(), True),
        StructField("volume_24h", DoubleType(), True),
        StructField("market_cap", DoubleType(), True),
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
    crypto_df = df.select(
        from_json(col("value").cast("string"), price_schema).alias("data")
    ).select("data.*")

    print("🚀 Consumer démarré, en attente de données...")
    print("   (Ctrl+C pour arrêter)")
    print()

    # Calculer les analytics et écrire dans InfluxDB
    # Fenêtre de 60 secondes pour regrouper les données
    query = crypto_df \
        .writeStream \
        .foreachBatch(calculate_analytics) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/spark-checkpoint-analytics") \
        .trigger(processingTime="60 seconds") \
        .start()

    # Attendre l'arrêt
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du consumer analytics...")
        query.stop()
        if influx_client:
            influx_client.close()
        spark.stop()
        print("👋 Consumer analytics arrêté")


if __name__ == "__main__":
    main()
