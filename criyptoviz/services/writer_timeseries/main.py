import json, os, psycopg2
from common.kafka_io import make_consumer
TABLE = os.getenv("TARGET_TABLE", "candles_1m")

def upsert(conn, r):
    with conn.cursor() as c:
        c.execute(f"""
            INSERT INTO {TABLE}(symbol, window_start, open, high, low, close, volume, sources_used, quality_flags)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (symbol, window_start) DO UPDATE SET
              open=EXCLUDED.open,
              high=EXCLUDED.high,
              low=EXCLUDED.low,
              close=EXCLUDED.close,
              volume=EXCLUDED.volume,
              sources_used=EXCLUDED.sources_used
        """, (
            r["symbol"], r["window_start"], r["open"], r["high"], r["low"], r["close"], r["volume"],
            r.get("sources_used", None), None
        ))

def main():
    topic = os.getenv("INPUT_TOPIC","market.agg.ohlcv.1m")
    dsn = os.getenv("PG_DSN")
    consumer = make_consumer(topic, group_id="writer-timeseries")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    for msg in consumer:
        rec = msg.value
        upsert(conn, rec)
        consumer.commit()

if __name__ == "__main__":
    main()
