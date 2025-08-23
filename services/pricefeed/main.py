import os, time, json
from datetime import datetime, timezone
import httpx, psycopg, redis

DSN = os.getenv("POSTGRES_DSN","postgresql://postgres:postgres@postgres:5432/cryptoviz")
REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
SYMBOLS = os.getenv("SYMBOLS","BTCUSDT,ETHUSDT").split(",")

def ensure_tables():
    with psycopg.connect(DSN, autocommit=True) as con, con.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS candles(
          symbol TEXT NOT NULL,
          ts TIMESTAMPTZ NOT NULL,
          open NUMERIC NOT NULL, high NUMERIC NOT NULL, low NUMERIC NOT NULL,
          close NUMERIC NOT NULL, volume NUMERIC NOT NULL,
          PRIMARY KEY(symbol, ts)
        );""")
        cur.execute("SELECT create_hypertable('candles','ts', if_not_exists=>TRUE);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_candles_symbol_ts ON candles(symbol, ts DESC);")

def upsert(cur, s, k):
    ts = datetime.fromtimestamp(k[0]/1000, tz=timezone.utc)
    o,h,l,c,v = map(float, (k[1],k[2],k[3],k[4],k[5]))
    cur.execute("""
      INSERT INTO candles(symbol, ts, open, high, low, close, volume)
      VALUES (%s,%s,%s,%s,%s,%s,%s)
      ON CONFLICT (symbol, ts) DO UPDATE
      SET open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
          close=EXCLUDED.close, volume=EXCLUDED.volume
    """, (s, ts, o,h,l,c,v))
    return ts, c

def main():
    ensure_tables()
    r = redis.from_url(REDIS_URL, decode_responses=True)
    with psycopg.connect(DSN, autocommit=True) as con, con.cursor() as cur, httpx.Client(timeout=10) as http:
        while True:
            for s in SYMBOLS:
                try:
                    resp = http.get("https://api.binance.com/api/v3/klines",
                                    params={"symbol": s, "interval": "1m", "limit": 1})
                    resp.raise_for_status()
                    arr = resp.json()
                    if not arr: continue
                    ts, last = upsert(cur, s, arr[0])
                    r.set(f"price:{s}", last)
                    r.publish("quotes", json.dumps({"symbol":s, "price":last, "ts":ts.isoformat()}))
                except Exception as e:
                    print(f"[{s}] {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
