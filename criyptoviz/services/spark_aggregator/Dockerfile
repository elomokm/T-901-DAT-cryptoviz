FROM bitnami/spark:3.5
USER root
RUN pip install pyspark==3.5.0 kafka-python==2.0.2
USER 1001
WORKDIR /app
# on copie depuis la racine (grâce au build context: .)
COPY common /app/common
COPY services/spark_aggregator/stream_ohlcv_1m.py /app/stream_ohlcv_1m.py
