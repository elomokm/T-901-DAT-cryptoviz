import json, os
import psycopg2, psycopg2.extras
from datetime import datetime
from common.kafka_io import make_consumer, make_producer

def load_registry(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as c:
        c.execute("SELECT symbol_canonique, aliases FROM symbol_registry WHERE enabled = TRUE;")
        rows = c.fetchall()
    mapping = {}
    for r in rows:
        canon = r["symbol_canonique"]
        aliases = r["aliases"] or {}
        for exch, sym in aliases.items():
            if sym:
                mapping[(exch, sym)] = canon
    return mapping

def main():
    pg_dsn = os.getenv("PG_DSN")
    in_topics = os.getenv("INPUT_TOPICS","market.raw.trade.binance").split(",")
    out_topic = os.getenv("OUTPUT_TOPIC","market.normalized.trade")

    consumer = make_consumer(in_topics[0], group_id="normalizer-market")
    producer = make_producer()
    conn = psycopg2.connect(pg_dsn)
    mapping = load_registry(conn)

    for msg in consumer:
        try:
            val = msg.value
            source = val["source"]
            sym_src = val["symbol_source"]
            canon = mapping.get((source, sym_src))
            if not canon:
                # dead-letter simplifié: ignorer (ou publier sur market.deadletter.raw)
                consumer.commit()
                continue
            out = {
                "source": source,
                "symbol": canon,
                "price": float(val["price"]),
                "amount": float(val["amount"]),
                "ts_event": val["ts_event"],
                "ts_ingest": val["ts_ingest"],
                "trade_id": val.get("trade_id"),
                "side": val.get("side"),
                "schema_version": 0
            }
            producer.send(out_topic, value=out, key=canon)
            consumer.commit()
        except Exception:
            # TODO: publier vers market.deadletter.normalized
            consumer.commit()

if __name__ == "__main__":
    main()
