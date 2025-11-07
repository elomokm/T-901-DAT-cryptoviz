"""
Consumer Spark Streaming - Pipeline crypto-prices → InfluxDB

Rôle:
  1. Lit le topic Kafka 'crypto-prices' en temps réel
  2. Parse les messages JSON (schema 20 champs)
  3. Écrit dans InfluxDB (measurement: crypto_market)

Architecture:
  CoinGeckoAgent → Kafka (crypto-prices) → Ce Consumer → InfluxDB
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv non installé. Variables d'environnement système utilisées.")

# ============================================================
# CONFIGURATION
# ============================================================

# Kafka
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = 'crypto-prices'

# InfluxDB
INFLUX_URL = os.getenv('INFLUX_URL')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET')
INFLUX_MEASUREMENT = 'crypto_market'
INFLUX_BATCH_SIZE = int(os.getenv('INFLUX_BATCH_SIZE', '100'))

# Validation des variables critiques
if not all([INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET]):
    print("❌ ERREUR : Variables d'environnement manquantes !")
    print("   Assurez-vous que .env contient :")
    print("   - INFLUX_URL")
    print("   - INFLUX_TOKEN")
    print("   - INFLUX_ORG")
    print("   - INFLUX_BUCKET")
    sys.exit(1)


# ============================================================
# SCHEMA SPARK (doit correspondre au JSON de CoinGeckoAgent)
# ============================================================

schema = StructType([
    # Métadonnées (identifiants)
    StructField("timestamp", StringType(), True),      # ISO 8601 timestamp
    StructField("crypto_id", StringType(), True),      # "bitcoin"
    StructField("symbol", StringType(), True),         # "BTC"
    StructField("name", StringType(), True),           # "Bitcoin"
    
    # Prix & volumes
    StructField("price_usd", DoubleType(), True),
    StructField("market_cap", DoubleType(), True),
    StructField("market_cap_rank", IntegerType(), True),
    StructField("volume_24h", DoubleType(), True),
    
    # Variations (%)
    StructField("change_1h", DoubleType(), True),
    StructField("change_24h", DoubleType(), True),
    StructField("change_7d", DoubleType(), True),
    
    # All-Time High/Low
    StructField("ath", DoubleType(), True),
    StructField("ath_date", StringType(), True),
    StructField("ath_change_pct", DoubleType(), True),
    StructField("atl", DoubleType(), True),
    StructField("atl_date", StringType(), True),
    StructField("atl_change_pct", DoubleType(), True),
    
    # Supply (circulation)
    StructField("circulating_supply", DoubleType(), True),
    StructField("total_supply", DoubleType(), True),
    StructField("max_supply", DoubleType(), True),
])


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def main():
    """Point d'entrée du consumer"""
    
    print("=" * 60)
    print(" CONSUMER SPARK STREAMING - CRYPTO PRICES")
    print("=" * 60)
    
    # --------------------------------------------------------
    # 1. CRÉER SESSION SPARK
    # --------------------------------------------------------
    print("\n Initialisation Spark Session...")
    
    spark = SparkSession.builder \
        .appName("CryptoPricesConsumer") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
        .getOrCreate()
    
    # Réduire les logs Spark (moins de bruit)
    spark.sparkContext.setLogLevel("WARN")
    
    print(f" Spark Session créée")
    print(f"   Version: {spark.version}")
    
    # --------------------------------------------------------
    # 2. LIRE DEPUIS KAFKA (Streaming)
    # --------------------------------------------------------
    print(f"\n Connexion à Kafka...")
    print(f"   Broker: {KAFKA_BROKER}")
    print(f"   Topic: {KAFKA_TOPIC}")
    
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()
    
    print(f" Stream Kafka connecté")
    
    # --------------------------------------------------------
    # 3. PARSER LES MESSAGES JSON
    # --------------------------------------------------------
    print(f"\n Configuration du parsing JSON...")
    
    # Kafka envoie des bytes, on convertit en string
    value_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string")
    
    # Parser le JSON selon notre schema
    parsed_df = value_df.select(
        from_json(col("json_string"), schema).alias("data")
    ).select("data.*")
    
    # Convertir timestamp ISO 8601 string → datetime Spark
    parsed_df = parsed_df.withColumn(
        "event_ts", 
        col("timestamp").cast("timestamp")
    )
    
    print(f" Schema configuré ({len(schema.fields)} champs)")
    
    # --------------------------------------------------------
    # 4. FONCTION D'ÉCRITURE DANS INFLUXDB
    # --------------------------------------------------------
    
    def write_to_influx(batch_df, epoch_id):
        """
        Callback appelé pour chaque micro-batch.
        
        Args:
            batch_df: DataFrame contenant le batch de données
            epoch_id: Numéro du batch (0, 1, 2, ...)
        """
        
        # Ignorer les batchs vides
        if batch_df.rdd.isEmpty():
            print(f"⏭  Batch {epoch_id}: vide (aucune donnée)")
            return
        
        # Sélectionner uniquement les colonnes nécessaires
        batch = batch_df.select(
            "event_ts", "crypto_id", "symbol", "name",
            "price_usd", "market_cap", "market_cap_rank", "volume_24h",
            "change_1h", "change_24h", "change_7d",
            "ath", "ath_change_pct", "atl", "atl_change_pct",
            "circulating_supply", "total_supply", "max_supply"
        )
        
        count = batch.count()
        print(f"\n Batch {epoch_id}: {count} ligne(s) reçue(s)")
        
        # --------------------------------------------------------
        # Connexion InfluxDB
        # --------------------------------------------------------
        
        client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        
        write_api = client.write_api(write_options=WriteOptions(
            batch_size=INFLUX_BATCH_SIZE,
            write_type=SYNCHRONOUS,  # Écriture synchrone (attendre confirmation)
        ))
        
        points = []
        
        try:
            # --------------------------------------------------------
            # Créer les Points InfluxDB
            # --------------------------------------------------------
            
            for row in batch.toLocalIterator():
                # Créer un Point (ligne de données InfluxDB)
                p = Point(INFLUX_MEASUREMENT)
                
                # TAGS (identifiants, indexés)
                p = p.tag("crypto_id", str(row.crypto_id))
                p = p.tag("symbol", str(row.symbol))
                p = p.tag("name", str(row.name))
                
                # FIELDS (valeurs métriques)
                # Gestion des valeurs null (si CoinGecko API retourne null)
                p = p.field("price_usd", float(row.price_usd) if row.price_usd else 0.0)
                p = p.field("market_cap", float(row.market_cap) if row.market_cap else 0.0)
                p = p.field("market_cap_rank", int(row.market_cap_rank) if row.market_cap_rank else 0)
                p = p.field("volume_24h", float(row.volume_24h) if row.volume_24h else 0.0)
                
                p = p.field("change_1h", float(row.change_1h) if row.change_1h else 0.0)
                p = p.field("change_24h", float(row.change_24h) if row.change_24h else 0.0)
                p = p.field("change_7d", float(row.change_7d) if row.change_7d else 0.0)
                
                p = p.field("ath", float(row.ath) if row.ath else 0.0)
                p = p.field("ath_change_pct", float(row.ath_change_pct) if row.ath_change_pct else 0.0)
                p = p.field("atl", float(row.atl) if row.atl else 0.0)
                p = p.field("atl_change_pct", float(row.atl_change_pct) if row.atl_change_pct else 0.0)
                
                p = p.field("circulating_supply", float(row.circulating_supply) if row.circulating_supply else 0.0)
                p = p.field("total_supply", float(row.total_supply) if row.total_supply else 0.0)
                p = p.field("max_supply", float(row.max_supply) if row.max_supply else 0.0)
                
                # TIMESTAMP - DÉSACTIVÉ TEMPORAIREMENT POUR DEBUG
                # On laisse InfluxDB utiliser l'heure d'arrivée
                # if row.event_ts is not None:
                #     p = p.time(row.event_ts)
                
                points.append(p)
                
                # Écriture par batch de 1000 (optimisation)
                if len(points) >= 1000:
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
                    points = []
            
            # Écrire les points restants
            if points:
                print(f"🔄 Tentative d'écriture de {len(points)} points...")
                print(f"   URL: {INFLUX_URL}")
                print(f"   Org: {INFLUX_ORG}")
                print(f"   Bucket: {INFLUX_BUCKET}")
                print(f"   Token (premiers 10 chars): {INFLUX_TOKEN[:10]}...")
                
                try:
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
                    write_api.flush()
                    print(f"✅ Batch {epoch_id}: {count} point(s) écrit(s) avec succès !")
                except Exception as write_error:
                    print(f"❌ ERREUR lors du write:")
                    print(f"   Type: {type(write_error).__name__}")
                    print(f"   Message: {write_error}")
                    raise  # Re-lever l'erreur pour voir la stack trace
            else:
                print(f"⚠️  Aucun point à écrire pour batch {epoch_id}")
            
            print(f"   Measurement: {INFLUX_MEASUREMENT}")
            print(f"   Bucket: {INFLUX_BUCKET}")
            
        except Exception as e:
            print(f" Erreur lors de l'écriture InfluxDB:")
            print(f"   {e}")
            
            # Afficher la stack trace complète (debug)
            import traceback
            traceback.print_exc()
            
        finally:
            # Toujours fermer la connexion
            client.close()
    
    # --------------------------------------------------------
    # 5. LANCER LE STREAMING
    # --------------------------------------------------------
    
    print(f"\n Configuration écriture InfluxDB...")
    print(f"   URL: {INFLUX_URL}")
    print(f"   Bucket: {INFLUX_BUCKET}")
    print(f"   Measurement: {INFLUX_MEASUREMENT}")
    
    query = parsed_df.writeStream \
        .foreachBatch(write_to_influx) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/spark-checkpoint-prices") \
        .start()
    
    print("\n" + "=" * 60)
    print(" CONSUMER DÉMARRÉ - EN ATTENTE DE DONNÉES...")
    print("=" * 60)
    print("\n Appuyez sur Ctrl+C pour arrêter\n")
    
    # Bloquer jusqu'à arrêt manuel (Ctrl+C)
    query.awaitTermination()


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    main()