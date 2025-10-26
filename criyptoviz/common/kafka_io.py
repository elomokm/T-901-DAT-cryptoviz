# helpers Producer/Consumer Kafka
import json, os
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer

def make_producer():
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
    return KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v, default=_json_dt).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        acks="all",                         # ok (équivalent -1)
        retries=10,
        linger_ms=5,
        max_in_flight_requests_per_connection=1,
        request_timeout_ms=30000
    )


# common/kafka_io.py
def make_consumer(topic_or_topics, group_id):
    from kafka import KafkaConsumer
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
    topics = topic_or_topics if isinstance(topic_or_topics, (list, tuple)) else [topic_or_topics]
    return KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda v: v.decode("utf-8") if v else None,
        auto_offset_reset="latest",
        enable_auto_commit=False,
        group_id=group_id
    )


def _json_dt(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError
