import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from typing import Optional

# InfluxDB v2 client (installed via requirements.txt)
from influxdb_client import InfluxDBClient, Point, WriteOptions

# 1. Définition du schéma des messages JSON envoyés par le producer
crypto_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("crypto", StringType(), True),
    StructField("price_usd", DoubleType(), True),
    StructField("price_eur", DoubleType(), True),
    StructField("change_24h", DoubleType(), True),
    StructField("market_cap", DoubleType(), True),
    StructField("volume_24h", DoubleType(), True),
])

def main():
    # 2. Création de la SparkSession en mode Structured Streaming
    spark = (
        SparkSession.builder
        .appName("CryptoConsumerSpark")
        # .master("local[*]")   # décommente si tu veux forcer local
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    # 3. Lecture du topic Kafka en streaming
    #    - subscribe = "crypto-prices"
    #    - startingOffsets = "latest": on lit à partir de maintenant
    starting_offsets = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

    max_offsets = os.getenv("KAFKA_MAX_OFFSETS_PER_TRIGGER", "100")

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "crypto-prices")
        .option("startingOffsets", starting_offsets)
        .option("maxOffsetsPerTrigger", max_offsets)
        .option("failOnDataLoss", "false")
        .load()
    )

    # kafka_df a les colonnes:
    #   key: binary
    #   value: binary
    #   topic, partition, offset, timestamp, timestampType
    #
    # Nous on veut décoder `value` (binaire) en string JSON,
    # puis parser ce JSON avec le schéma défini.

    values_df = kafka_df.selectExpr("CAST(value AS STRING) as json_str")

    parsed_df = (
        values_df
        .select(from_json(col("json_str"), crypto_schema).alias("data"))
        .select("data.*")
    )

    # 4. Convertir le champ timestamp (string ISO8601) en vrai timestamp Spark
    #    Remarque: ton timestamp est du type "2025-10-26T16:15:21.362177+00:00"
    #    Spark sait parser les formats ISO8601 avec timezone via to_timestamp dans les versions récentes.
    #    Si jamais ça renvoie null, on fera un traitement custom. On tente simple d'abord.
    parsed_df = parsed_df.withColumn(
        "event_ts",
        to_timestamp(col("timestamp"))
    )

    # 5. (Optionnel mais utile) réorganiser les colonnes pour l'affichage
    final_df = (
        parsed_df
        .select(
            "event_ts",
            "timestamp",
            "crypto",
            "price_usd",
            "price_eur",
            "change_24h",
            "market_cap",
            "volume_24h"
        )
    )

    # 6. Ecriture dans InfluxDB (foreachBatch) + logs console
    INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
    INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
    INFLUX_ORG = os.getenv("INFLUX_ORG", "crypto-org")
    INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "crypto-data")
    INFLUX_BATCH_SIZE = int(os.getenv("INFLUX_BATCH_SIZE", "5"))
    INFLUX_FLUSH_INTERVAL_MS = int(os.getenv("INFLUX_FLUSH_INTERVAL_MS", "2000"))

    def write_to_influx(batch_df, epoch_id):
        if batch_df.rdd.isEmpty():
            print(f"Batch {epoch_id}: vide")
            return

        # On réduit aux colonnes nécessaires
        cols = [
            "event_ts",
            "crypto",
            "price_usd",
            "price_eur",
            "change_24h",
            "market_cap",
            "volume_24h",
        ]
        batch = batch_df.select(*cols)

        # Diagnostics: show batch time span and per-crypto counts
        try:
            from pyspark.sql import functions as F
            span = batch.agg(
                F.min("event_ts").alias("min_event_ts"),
                F.max("event_ts").alias("max_event_ts"),
                F.count(F.lit(1)).alias("rows")
            ).collect()[0]
            print(
                f"Batch {epoch_id} stats => rows={span['rows']}, "
                f"min_event_ts={span['min_event_ts']}, max_event_ts={span['max_event_ts']}"
            )

            per_crypto = (
                batch.groupBy("crypto").count().orderBy("crypto")
            )
            # Show up to 20 cryptos; safe in driver logs
            per_crypto.show(truncate=False)
        except Exception as diag_err:
            print(f"[diag] Batch {epoch_id} diagnostics failed: {diag_err}")

        # Création du client pour ce micro-batch
        client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        write_api = client.write_api(write_options=WriteOptions(
            batch_size=INFLUX_BATCH_SIZE,
            flush_interval=INFLUX_FLUSH_INTERVAL_MS,
            jitter_interval=0,
            retry_interval=1000,
        ))

        points = []
        count = 0
        for row in batch.toLocalIterator():
            p = (
                Point("crypto_price")
                .tag("crypto", str(row.crypto))
                .field("price_usd", float(row.price_usd) if row.price_usd is not None else 0.0)
                .field("price_eur", float(row.price_eur) if row.price_eur is not None else 0.0)
                .field("change_24h", float(row.change_24h) if row.change_24h is not None else 0.0)
                .field("market_cap", float(row.market_cap) if row.market_cap is not None else 0.0)
                .field("volume_24h", float(row.volume_24h) if row.volume_24h is not None else 0.0)
            )
            if row.event_ts is not None:
                p = p.time(row.event_ts)

            points.append(p)
            count += 1

            # Ecrit par paquets pour limiter la mémoire locale
            if len(points) >= max(1000, INFLUX_BATCH_SIZE):
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
                points = []

        if points:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

        write_api.flush()
        client.close()
        print(f"Batch {epoch_id}: écrit {count} points dans InfluxDB")

    checkpoint_dir = os.getenv("SPARK_CHECKPOINT_DIR", "./checkpoints/crypto_consumer")

    query = (
        final_df
        .writeStream
        .outputMode("append")
        .foreachBatch(write_to_influx)
        .option("checkpointLocation", checkpoint_dir)
        .trigger(processingTime="5 seconds")
        .start()
    )

    # Optional: debug to console in parallel (set STREAM_DEBUG_CONSOLE=1)
    if os.getenv("STREAM_DEBUG_CONSOLE", "0") in ("1", "true", "True"):
        (
            final_df
            .writeStream
            .outputMode("append")
            .format("console")
            .option("truncate", "false")
            .option("numRows", 10)
            .option("checkpointLocation", checkpoint_dir + "_console")
            .trigger(processingTime="5 seconds")
            .start()
        )

    # 7. Attendre la terminaison du stream (Ctrl+C pour stopper)
    query.awaitTermination()

if __name__ == "__main__":
    main()
