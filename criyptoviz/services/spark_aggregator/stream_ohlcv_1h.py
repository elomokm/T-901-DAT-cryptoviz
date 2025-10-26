import os, json
from pyspark.sql import SparkSession, functions as F, types as T

bootstrap = os.getenv("KAFKA_BOOTSTRAP","kafka:9092")
input_topic = os.getenv("INPUT_TOPIC","market.normalized.trade")
output_topic = os.getenv("OUTPUT_TOPIC","market.agg.ohlcv.1h")
watermark = os.getenv("WATERMARK","2 minutes")
window_size = os.getenv("WINDOW_SIZE","1 hour")

spark = (SparkSession.builder
    .appName("cv_ohlcv_1h")
    .getOrCreate())

schema = T.StructType([
    T.StructField("source", T.StringType()),
    T.StructField("symbol", T.StringType()),
    T.StructField("price", T.DoubleType()),
    T.StructField("amount", T.DoubleType()),
    T.StructField("ts_event", T.TimestampType()),
    T.StructField("ts_ingest", T.TimestampType()),
    T.StructField("trade_id", T.StringType()),
    T.StructField("side", T.StringType()),
    T.StructField("schema_version", T.IntegerType())
])

raw = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", bootstrap)
    .option("subscribe", input_topic)
    .option("startingOffsets", "latest")
    .load())

parsed = (raw
    .select(F.col("key").cast("string").alias("key"),
            F.col("value").cast("string").alias("value"))
    .withColumn("json", F.from_json("value", schema))
    .select("key","json.*"))

with_wm = parsed.withWatermark("ts_event", watermark)

# open/close par temps d'arrivée dans la fenêtre
win = F.window("ts_event", window_size)
agg = (with_wm
    .groupBy("symbol", win)
    .agg(
        F.first("price", ignorenulls=True).alias("open"),
        F.max("price").alias("high"),
        F.min("price").alias("low"),
        F.last("price", ignorenulls=True).alias("close"),
        F.sum("amount").alias("volume"),
        F.collect_set("source").alias("sources_used")
    )
    .select(
        F.col("symbol"),
        F.col("window.start").alias("window_start"),
        "open","high","low","close","volume","sources_used"
    )
)

def to_kv(df):
    return (df
        .select(
            F.col("symbol").alias("key"),
            F.to_json(F.struct(*df.columns)).alias("value"))
    )

out = (to_kv(agg)
    .writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", bootstrap)
    .option("topic", output_topic)
    .option("checkpointLocation", "/tmp/checkpoints/cv_ohlcv_1h")
    .outputMode("update")
    .start())

out.awaitTermination()