#!/usr/bin/env python3
"""
Consumer Spark - Validation Croisée CoinGecko vs CoinMarketCap
================================================================

Mission:
- Joindre les données CoinGecko et CoinMarketCap par symbol + fenêtre temporelle
- Calculer la divergence de prix entre les 2 sources
- Écrire les métriques de validation dans InfluxDB
- Envoyer les anomalies (divergence > 5%) dans le topic DLQ

Architecture:
    Kafka (crypto-prices) 
        → Spark Structured Streaming
        → Jointure CG ↔ CMC (fenêtre 2 min)
        → Calcul divergence
        → InfluxDB (crypto_validation) + Kafka DLQ (anomalies)
"""

import os
import json
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, abs as spark_abs, 
    expr, current_timestamp, lit
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DoubleType, TimestampType, BooleanType
)
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from kafka import KafkaProducer

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# CONFIGURATION
# ============================================================================

# InfluxDB Configuration
INFLUX_URL = os.getenv('INFLUX_URL', 'http://localhost:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'crypto-org')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'crypto-data')

# Kafka Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
INPUT_TOPIC = 'crypto-prices'
DLQ_TOPIC = 'crypto-dlq'  # Dead Letter Queue pour anomalies

# Validation Thresholds
DIVERGENCE_WARNING_THRESHOLD = 5.0   # 5% → Flag as anomaly
DIVERGENCE_CRITICAL_THRESHOLD = 10.0 # 10% → Critical alert

# Validation des variables critiques
if not INFLUX_TOKEN:
    raise ValueError("❌ INFLUX_TOKEN non défini dans .env")

print("="*70)
print("🔍 SPARK CONSUMER : VALIDATION CROISÉE")
print("="*70)
print(f"✅ InfluxDB configuré: {INFLUX_URL}")
print(f"📊 Bucket: {INFLUX_BUCKET} | Org: {INFLUX_ORG}")
print(f"📡 Kafka Input Topic: {INPUT_TOPIC}")
print(f"🚨 Kafka DLQ Topic: {DLQ_TOPIC}")
print(f"⚠️  Seuil anomalie: {DIVERGENCE_WARNING_THRESHOLD}%")
print(f"🔴 Seuil critique: {DIVERGENCE_CRITICAL_THRESHOLD}%")
print("="*70)
print()

# ============================================================================
# SCHÉMA KAFKA MESSAGE
# ============================================================================

schema = StructType([
    StructField("source", StringType(), False),
    StructField("crypto_id", StringType(), False),
    StructField("symbol", StringType(), False),
    StructField("name", StringType(), True),
    StructField("price_usd", DoubleType(), False),
    StructField("market_cap", DoubleType(), True),
    StructField("volume_24h", DoubleType(), True),
    StructField("percent_change_24h", DoubleType(), True),
    StructField("timestamp", StringType(), False),
    StructField("anomaly_detected", BooleanType(), True),
])

# ============================================================================
# INFLUXDB CLIENT
# ============================================================================

influx_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# ============================================================================
# KAFKA PRODUCER (pour DLQ)
# ============================================================================

dlq_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=1
)

print("✅ InfluxDB client initialisé")
print("✅ Kafka DLQ producer initialisé")
print()

# ============================================================================
# FONCTION DE VALIDATION
# ============================================================================

def write_validation_to_influxdb(batch_df, batch_id):
    """
    Fonction appelée pour chaque micro-batch.
    
    Traitement:
    1. Sépare CoinGecko et CoinMarketCap
    2. Join sur symbol + fenêtre temporelle (2 minutes)
    3. Calcule divergence
    4. Écrit dans InfluxDB (measurement: crypto_validation)
    5. Envoie anomalies vers DLQ
    """
    
    if batch_df.isEmpty():
        print(f"⏭️  Batch #{batch_id} vide, skip")
        return
    
    try:
        print(f"\n{'='*70}")
        print(f"🔍 BATCH #{batch_id} - Validation Croisée")
        print(f"{'='*70}")
        
        # Comptage initial
        total_count = batch_df.count()
        print(f"📊 Messages reçus: {total_count}")
        
        # ====================================================================
        # ÉTAPE 1 : Séparer par source
        # ====================================================================
        
        coingecko_df = batch_df.filter(col("source") == "coingecko")
        coinmarketcap_df = batch_df.filter(col("source") == "coinmarketcap")
        
        cg_count = coingecko_df.count()
        cmc_count = coinmarketcap_df.count()
        
        print(f"   └─ CoinGecko: {cg_count} | CoinMarketCap: {cmc_count}")
        
        if cg_count == 0 or cmc_count == 0:
            print(f"⚠️  Une source manquante, skip validation")
            return
        
        # ====================================================================
        # ÉTAPE 2 : Jointure sur symbol + fenêtre temporelle
        # ====================================================================
        
        # Convertir timestamp string → timestamp type
        cg_with_ts = coingecko_df.withColumn(
            "event_time", 
            col("timestamp").cast(TimestampType())
        )
        
        cmc_with_ts = coinmarketcap_df.withColumn(
            "event_time",
            col("timestamp").cast(TimestampType())
        )
        
        # Fenêtre de 2 minutes pour regrouper
        cg_windowed = cg_with_ts.withColumn(
            "time_window",
            window(col("event_time"), "2 minutes")
        )
        
        cmc_windowed = cmc_with_ts.withColumn(
            "time_window",
            window(col("event_time"), "2 minutes")
        )
        
        # Jointure INNER (seulement les cryptos présentes dans les 2 sources)
        joined = cg_windowed.alias("cg").join(
            cmc_windowed.alias("cmc"),
            on=[
                col("cg.symbol") == col("cmc.symbol"),
                col("cg.time_window") == col("cmc.time_window")
            ],
            how="inner"
        )
        
        joined_count = joined.count()
        print(f"✅ Jointure réussie: {joined_count} cryptos validées")
        
        if joined_count == 0:
            print(f"⚠️  Aucune crypto commune, skip validation")
            return
        
        # ====================================================================
        # ÉTAPE 3 : Calculer divergence
        # ====================================================================
        
        with_divergence = joined.withColumn(
            "divergence_pct",
            (spark_abs(col("cg.price_usd") - col("cmc.price_usd")) / col("cg.price_usd")) * 100
        ).withColumn(
            "price_consensus",
            (col("cg.price_usd") + col("cmc.price_usd")) / 2
        ).withColumn(
            "status",
            expr(f"""
                CASE
                    WHEN divergence_pct < {DIVERGENCE_WARNING_THRESHOLD} THEN 'ok'
                    WHEN divergence_pct < {DIVERGENCE_CRITICAL_THRESHOLD} THEN 'warning'
                    ELSE 'critical'
                END
            """)
        )
        
        # ====================================================================
        # ÉTAPE 4 : Statistiques
        # ====================================================================
        
        status_counts = with_divergence.groupBy("status").count().collect()
        
        stats = {row['status']: row['count'] for row in status_counts}
        ok_count = stats.get('ok', 0)
        warning_count = stats.get('warning', 0)
        critical_count = stats.get('critical', 0)
        
        print(f"\n📈 Résultats de Validation:")
        print(f"   ✅ OK (< {DIVERGENCE_WARNING_THRESHOLD}%): {ok_count}")
        print(f"   ⚠️  Warning ({DIVERGENCE_WARNING_THRESHOLD}-{DIVERGENCE_CRITICAL_THRESHOLD}%): {warning_count}")
        print(f"   🔴 Critical (> {DIVERGENCE_CRITICAL_THRESHOLD}%): {critical_count}")
        
        # ====================================================================
        # ÉTAPE 5 : Écrire dans InfluxDB + DLQ
        # ====================================================================
        
        points = []
        dlq_messages = []
        
        for row in with_divergence.collect():
            symbol = row['cg.symbol']
            divergence = row['divergence_pct']
            status = row['status']
            
            # Point InfluxDB
            point = Point("crypto_validation") \
                .tag("symbol", symbol) \
                .tag("status", status) \
                .field("price_coingecko", float(row['cg.price_usd'])) \
                .field("price_coinmarketcap", float(row['cmc.price_usd'])) \
                .field("price_consensus", float(row['price_consensus'])) \
                .field("divergence_pct", float(divergence)) \
                .field("market_cap_cg", float(row['cg.market_cap']) if row['cg.market_cap'] else 0.0) \
                .field("market_cap_cmc", float(row['cmc.market_cap']) if row['cmc.market_cap'] else 0.0) \
                .field("sources_count", 2)
            
            points.append(point)
            
            # Si anomalie, envoyer dans DLQ
            if status in ['warning', 'critical']:
                dlq_message = {
                    "symbol": symbol,
                    "status": status,
                    "divergence_pct": float(divergence),
                    "coingecko_price": float(row['cg.price_usd']),
                    "coinmarketcap_price": float(row['cmc.price_usd']),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "batch_id": batch_id
                }
                dlq_messages.append(dlq_message)
        
        # Écriture batch InfluxDB
        if points:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
            print(f" {len(points)} métriques écrites dans InfluxDB (crypto_validation)")
        
        # Envoi DLQ
        if dlq_messages:
            for msg in dlq_messages:
                dlq_producer.send(DLQ_TOPIC, value=msg)
            dlq_producer.flush()
            print(f" {len(dlq_messages)} anomalies envoyées dans DLQ ({DLQ_TOPIC})")
        
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Erreur dans batch #{batch_id}: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# SPARK SESSION
# ============================================================================

spark = SparkSession.builder \
    .appName("CryptoValidationConsumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints-validation") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("✅ Spark Session créée")
print()

# ============================================================================
# STREAMING KAFKA → VALIDATION
# ============================================================================

print("🔄 Démarrage du streaming Kafka...")
print()

# Lire depuis Kafka
kafka_stream = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", INPUT_TOPIC) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Parser JSON
parsed_stream = kafka_stream.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*")

# Écrire via foreachBatch
query = parsed_stream \
    .writeStream \
    .foreachBatch(write_validation_to_influxdb) \
    .outputMode("append") \
    .start()

print(" Consumer de validation démarré !")
print(" Écoute du topic:", INPUT_TOPIC)
print(" Validation en cours...\n")

# Attendre l'arrêt
query.awaitTermination()
