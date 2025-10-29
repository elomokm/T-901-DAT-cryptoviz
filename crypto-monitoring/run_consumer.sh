#!/bin/zsh

# 1. activer le venv recréé
source /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring/.venv/bin/activate


# Variables Kafka/Influx
export KAFKA_STARTING_OFFSETS=earliest          # ou earliest si tu veux relire tout
export KAFKA_MAX_OFFSETS_PER_TRIGGER=10      # force plusieurs micro-batches
export SPARK_CHECKPOINT_DIR=./checkpoints/crypto_consumer

export INFLUX_URL=http://localhost:8086
export INFLUX_TOKEN=Y_Fn0YsUAnSnyikigehkC6WzFWa4shZkVwhM0U5KKbtb43E1y_A6QpyzKv-VYgPcYHLZctOeegOsDYmFGaYkQQ==
export INFLUX_ORG=crypto-org
export INFLUX_BUCKET=crypto-data

# Pour que Spark utilise la venv Python
export PYSPARK_PYTHON="$(pwd)/.venv/bin/python"
export PYSPARK_DRIVER_PYTHON="$(pwd)/.venv/bin/python"

# (Optionnel) Voir aussi les batches sur la console
export STREAM_DEBUG_CONSOLE=1
export JAVA_HOME="$(/usr/libexec/java_home -v 17)"

# Java 21/Hadoop compat: allow legacy SecurityManager API used by Hadoop UGI
export SPARK_SUBMIT_OPTS="${SPARK_SUBMIT_OPTS} -Djava.security.manager=allow"

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.extraJavaOptions=-Djava.security.manager=allow \
  --conf spark.executor.extraJavaOptions=-Djava.security.manager=allow \
  crypto_consumer_spark.py