#!/usr/bin/env python3
"""
Spark Structured Streaming Consumer - Anomaly Detection
Détecte les anomalies dans les données crypto en temps réel:
- Pics de volume anormaux (>3σ de la moyenne)
- Variations de prix extrêmes (>5% en <1min)
- Écarts entre sources (CoinGecko vs CoinMarketCap)
- Stocke les alertes dans InfluxDB (measurement: crypto_anomalies)
"""
import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
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

# Seuils d'anomalies
VOLUME_SIGMA_THRESHOLD = 3.0  # Volume >3σ = anomalie
PRICE_CHANGE_THRESHOLD = 5.0  # Variation >5% = anomalie

# Client InfluxDB global
influx_client = None
write_api = None

# Cache pour stocker les dernières valeurs (détection de variations rapides)
price_cache = {}  # {crypto_id: {'price': float, 'timestamp': datetime}}


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


def detect_anomalies(batch_df, batch_id):
    """
    Détecte les anomalies dans un batch de données.

    Anomalies détectées:
    1. Volume anormal (>3σ de la moyenne historique)
    2. Variation de prix rapide (>5% en moins d'1 minute)
    3. Prix très différent entre sources

    Args:
        batch_df: DataFrame Spark
        batch_id: ID du batch
    """
    if batch_df.isEmpty():
        print(f"ℹ️  Batch {batch_id}: Aucune donnée à analyser")
        return

    print(f"\n🔍 Batch {batch_id}: Détection d'anomalies...")

    # Convertir en Pandas pour analyse
    pdf = batch_df.select(
        "crypto_id",
        "symbol",
        "name",
        "source",
        "price_usd",
        "volume_24h",
        "change_1h",
        "timestamp"
    ).toPandas()

    if pdf.empty:
        return

    anomalies = []

    # Analyser par crypto
    for crypto_id in pdf['crypto_id'].unique():
        crypto_data = pdf[pdf['crypto_id'] == crypto_id]

        if len(crypto_data) == 0:
            continue

        symbol = crypto_data['symbol'].iloc[0]
        name = crypto_data['name'].iloc[0]

        # 1. Détection de volume anormal
        volume_mean = crypto_data['volume_24h'].mean()
        volume_std = crypto_data['volume_24h'].std()

        if volume_std and volume_std > 0:
            for _, row in crypto_data.iterrows():
                volume_z_score = (row['volume_24h'] - volume_mean) / volume_std

                if abs(volume_z_score) > VOLUME_SIGMA_THRESHOLD:
                    anomalies.append({
                        'crypto_id': crypto_id,
                        'symbol': symbol,
                        'name': name,
                        'anomaly_type': 'volume_spike',
                        'severity': 'high' if abs(volume_z_score) > 4 else 'medium',
                        'value': row['volume_24h'],
                        'expected': volume_mean,
                        'z_score': volume_z_score,
                        'message': f"Volume anormal: {row['volume_24h']:,.0f} (moyenne: {volume_mean:,.0f}, z-score: {volume_z_score:.2f})",
                        'source': row['source'],
                        'timestamp': datetime.utcnow().isoformat()
                    })

        # 2. Détection de variation rapide de prix
        current_price = crypto_data['price_usd'].iloc[-1]

        if crypto_id in price_cache:
            last_price = price_cache[crypto_id]['price']
            price_change_pct = abs((current_price - last_price) / last_price * 100)

            if price_change_pct > PRICE_CHANGE_THRESHOLD:
                anomalies.append({
                    'crypto_id': crypto_id,
                    'symbol': symbol,
                    'name': name,
                    'anomaly_type': 'price_spike',
                    'severity': 'critical' if price_change_pct > 10 else 'high',
                    'value': current_price,
                    'expected': last_price,
                    'change_pct': price_change_pct,
                    'message': f"Variation rapide: {price_change_pct:.2f}% (${last_price:.2f} → ${current_price:.2f})",
                    'source': crypto_data['source'].iloc[-1],
                    'timestamp': datetime.utcnow().isoformat()
                })

        # Mettre à jour le cache
        price_cache[crypto_id] = {
            'price': current_price,
            'timestamp': datetime.utcnow()
        }

        # 3. Détection d'écart entre sources
        sources = crypto_data['source'].unique()
        if len(sources) > 1:
            prices_by_source = {}
            for source in sources:
                source_data = crypto_data[crypto_data['source'] == source]
                if not source_data.empty:
                    prices_by_source[source] = source_data['price_usd'].mean()

            if len(prices_by_source) >= 2:
                price_values = list(prices_by_source.values())
                price_diff_pct = abs((max(price_values) - min(price_values)) / min(price_values) * 100)

                if price_diff_pct > 1.0:  # Écart >1% entre sources
                    sources_str = ', '.join([f"{s}: ${p:.2f}" for s, p in prices_by_source.items()])
                    anomalies.append({
                        'crypto_id': crypto_id,
                        'symbol': symbol,
                        'name': name,
                        'anomaly_type': 'source_divergence',
                        'severity': 'medium' if price_diff_pct < 3 else 'high',
                        'value': max(price_values),
                        'expected': min(price_values),
                        'divergence_pct': price_diff_pct,
                        'message': f"Écart entre sources: {price_diff_pct:.2f}% ({sources_str})",
                        'source': 'multi-source',
                        'timestamp': datetime.utcnow().isoformat()
                    })

    # Écrire les anomalies détectées
    if anomalies:
        print(f"🚨 Batch {batch_id}: {len(anomalies)} anomalies détectées!")
        write_anomalies_to_influx(anomalies, batch_id)
    else:
        print(f"✅ Batch {batch_id}: Aucune anomalie détectée")


def write_anomalies_to_influx(anomalies_list, batch_id):
    """
    Écrit les anomalies détectées dans InfluxDB.

    Args:
        anomalies_list: Liste de dictionnaires d'anomalies
        batch_id: ID du batch
    """
    _, write_api = get_influx_client()

    points = []
    for anomaly in anomalies_list:
        try:
            # Créer un point InfluxDB
            point = (
                Point("crypto_anomalies")
                .tag("crypto_id", anomaly['crypto_id'])
                .tag("symbol", anomaly['symbol'])
                .tag("anomaly_type", anomaly['anomaly_type'])
                .tag("severity", anomaly['severity'])
                .tag("source", anomaly['source'])
                .field("value", float(anomaly['value']))
                .field("expected", float(anomaly['expected']))
                .field("message", anomaly['message'])
            )

            # Ajouter les champs spécifiques selon le type
            if 'z_score' in anomaly:
                point = point.field("z_score", float(anomaly['z_score']))
            if 'change_pct' in anomaly:
                point = point.field("change_pct", float(anomaly['change_pct']))
            if 'divergence_pct' in anomaly:
                point = point.field("divergence_pct", float(anomaly['divergence_pct']))

            point = point.time(datetime.utcnow())
            points.append(point)

            # Afficher l'anomalie
            print(f"  🚨 [{anomaly['severity'].upper()}] {anomaly['symbol']}: {anomaly['message']}")

        except Exception as e:
            print(f"⚠️  Erreur création point anomalie pour {anomaly.get('crypto_id')}: {e}")
            continue

    # Écrire en batch
    if points:
        try:
            write_api.write(bucket=INFLUX_BUCKET, record=points)
            print(f"✅ Batch {batch_id}: {len(points)} anomalies écrites dans InfluxDB (measurement: crypto_anomalies)")
        except Exception as e:
            print(f"❌ Batch {batch_id}: Erreur écriture anomalies: {e}")


def main():
    """Lance le consumer d'anomalies"""

    print("=" * 80)
    print("🔍 SPARK ANOMALY DETECTION CONSUMER - Real-time Crypto Anomaly Detection")
    print("=" * 80)
    print(f"📡 Kafka Broker: {KAFKA_BROKER}")
    print(f"📊 InfluxDB: {INFLUX_URL}")
    print(f"🪣 Bucket: {INFLUX_BUCKET}")
    print()
    print("🚨 Anomalies détectées:")
    print(f"  • Volume anormal (>±{VOLUME_SIGMA_THRESHOLD}σ)")
    print(f"  • Variation de prix rapide (>±{PRICE_CHANGE_THRESHOLD}%)")
    print(f"  • Divergence entre sources (>1%)")
    print("=" * 80)
    print()

    # Créer la session Spark
    spark = SparkSession.builder \
        .appName("CryptoAnomalyDetectionConsumer") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Schéma des messages
    price_schema = StructType([
        StructField("crypto_id", StringType(), True),
        StructField("symbol", StringType(), True),
        StructField("name", StringType(), True),
        StructField("source", StringType(), True),
        StructField("price_usd", DoubleType(), True),
        StructField("volume_24h", DoubleType(), True),
        StructField("change_1h", DoubleType(), True),
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

    print("🚀 Consumer démarré, surveillance active...")
    print("   (Ctrl+C pour arrêter)")
    print()

    # Détecter les anomalies
    query = crypto_df \
        .writeStream \
        .foreachBatch(detect_anomalies) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/spark-checkpoint-anomalies") \
        .trigger(processingTime="30 seconds") \
        .start()

    # Attendre l'arrêt
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du consumer d'anomalies...")
        query.stop()
        if influx_client:
            influx_client.close()
        spark.stop()
        print("👋 Consumer d'anomalies arrêté")


if __name__ == "__main__":
    main()
