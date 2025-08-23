import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from psycopg_pool import ConnectionPool
import redis.asyncio as aioredis

import os
DSN = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") \
      or "postgresql://postgres:postgres@postgres:5432/cryptoviz"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

pool = ConnectionPool(DSN, min_size=1, max_size=5, kwargs={"autocommit": True})
rds = aioredis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="CryptoViz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _interval(tf: str) -> str:
    m = {"1m":"1 minute","5m":"5 minutes","15m":"15 minutes","1h":"1 hour","1d":"1 day"}
    return m.get(tf, "1 minute")

@app.get("/timeseries/candles")
def candles(symbol: str, tf: str = "1m", start: Optional[str] = None, end: Optional[str] = None):
    start_ts = start or "now() - interval '24 hours'"
    end_ts = end or "now()"
    with pool.connection() as con, con.cursor() as cur:
        if tf == "1m":
            cur.execute(
                f"""SELECT ts, open, high, low, close, volume
                    FROM candles
                    WHERE symbol=%s AND ts BETWEEN {start_ts} AND {end_ts}
                    ORDER BY ts ASC""",
                (symbol,)
            )
        else:
            cur.execute(
                f"""SELECT time_bucket(%s, ts) AS ts,
                           first(open, ts), max(high), min(low), last(close, ts), sum(volume)
                    FROM candles
                    WHERE symbol=%s AND ts BETWEEN {start_ts} AND {end_ts}
                    GROUP BY ts
                    ORDER BY ts ASC""",
                (_interval(tf), symbol)
            )
        rows = cur.fetchall()
    return [
        {"ts": r[0].isoformat(), "open": float(r[1]), "high": float(r[2]),
         "low": float(r[3]), "close": float(r[4]), "volume": float(r[5])}
        for r in rows
    ]

@app.get("/market/top")
def market_top(limit: int = 20):
    with pool.connection() as con, con.cursor() as cur:
        cur.execute("""
        WITH last AS (
          SELECT DISTINCT ON (symbol) symbol, close, ts
          FROM candles
          ORDER BY symbol, ts DESC
        ),
        prev AS (
          SELECT c.symbol, c.close
          FROM candles c
          JOIN last l ON l.symbol=c.symbol
          WHERE c.ts <= l.ts - interval '24 hours'
          ORDER BY c.symbol, c.ts DESC
        )
        SELECT l.symbol,
               l.close AS price,
               CASE WHEN p.close IS NULL THEN NULL
                    ELSE (l.close - p.close)/NULLIF(p.close,0)*100 END AS change24h
        FROM last l
        LEFT JOIN prev p ON p.symbol=l.symbol
        ORDER BY price DESC
        LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
    return [{"symbol": r[0], "price": float(r[1]), "change24h": (None if r[2] is None else float(r[2]))} for r in rows]

@app.get("/news")
def news(symbol: Optional[str] = None, limit: int = 50):
    with pool.connection() as con, con.cursor() as cur:
        if symbol:
            cur.execute("""
              SELECT ts, source, title, url, symbols, sentiment
              FROM news_articles
              WHERE symbols @> ARRAY[%s]::text[]
              ORDER BY ts DESC
              LIMIT %s
            """, (symbol, limit))
        else:
            cur.execute("""
              SELECT ts, source, title, url, symbols, sentiment
              FROM news_articles
              ORDER BY ts DESC
              LIMIT %s
            """, (limit,))
        rows = cur.fetchall()
    out = []
    for ts, source, title, url, symbols, sentiment in rows:
        out.append({
            "ts": ts.isoformat(), "source": source, "title": title,
            "url": url, "symbols": symbols or [], "sentiment": (None if sentiment is None else float(sentiment))
        })
    return out

@app.get("/news/volume")
def news_volume():
    with pool.connection() as con, con.cursor() as cur:
        try:
            cur.execute("""
                SELECT bucket, source, volume
                FROM mv_news_volume_1m
                WHERE bucket >= now() - interval '24 hours'
                ORDER BY bucket DESC, source
            """)
            rows = cur.fetchall()
            return [{"bucket": r[0].isoformat(), "source": r[1], "volume": int(r[2])} for r in rows]
        except Exception:
            return []

@app.websocket("/ws/quotes")
async def ws_quotes(ws: WebSocket):
    await ws.accept()
    pub = rds.pubsub()
    await pub.subscribe("quotes")
    try:
        async for msg in pub.listen():
            if msg and msg.get("type") == "message":
                await ws.send_text(msg["data"])
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await pub.unsubscribe("quotes")
            await pub.close()
        except Exception:
            pass
