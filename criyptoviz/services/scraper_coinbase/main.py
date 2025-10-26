import os, asyncio, json
from datetime import datetime, timezone
import websockets
from common.kafka_io import make_producer

WS_URL = "wss://advanced-trade-ws.coinbase.com"  # public market data
# Docs channel name: "market_trades" (public). Endpoint confirmé. 
# On s'abonne SANS JWT pour les canaux publics.  (Auth possible mais non requis)

def now_utc():
    return datetime.now(timezone.utc)

def subscribe_msg(products, channel="market_trades"):
    return {
        "type": "subscribe",
        "channel": channel,
        "product_ids": products
    }

async def run():
    products = os.getenv("PRODUCT_IDS_CSV","BTC-USD").split(",")
    topic = os.getenv("OUTPUT_TOPIC","market.raw.trade.coinbase")
    producer = make_producer()
    backoff = 1
    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=10) as ws:
                await ws.send(json.dumps(subscribe_msg(products)))
                backoff = 1
                async for raw in ws:
                    msg = json.loads(raw)
                    # Attendu: messages avec "type": "snapshot"/"update" selon channel
                    # Pour market_trades: on reçoit des trades individuels (docs AT WS).
                    # Format variant -> on garde un parse tolérant:
                    t = msg.get("events") or msg.get("trades") or []
                    # Certains messages contiennent une liste d'events ; on itère
                    # Les payloads exacts peuvent varier ; on extrait prx/qty/ts si présents
                    if isinstance(t, list) and t:
                        for ev in t:
                            trades = ev.get("trades") or []
                            for tr in trades:
                                # Exemples de champs typiques:
                                product_id = tr.get("product_id") or msg.get("product_id")
                                price = tr.get("price") or tr.get("p")
                                size  = tr.get("size")  or tr.get("q")
                                ts    = tr.get("time")  or tr.get("ts")
                                if not (product_id and price and size and ts):
                                    continue
                                # ts iso → datetime
                                try:
                                    ts_event = datetime.fromisoformat(ts.replace("Z","+00:00"))
                                except Exception:
                                    try:
                                        ts_event = datetime.utcfromtimestamp(float(ts)).replace(tzinfo=timezone.utc)
                                    except Exception:
                                        ts_event = now_utc()
                                rec = {
                                    "source": "coinbase",
                                    "symbol_source": product_id,      # ex: BTC-USD
                                    "price": float(price),
                                    "amount": float(size),
                                    "ts_event": ts_event,
                                    "ts_ingest": now_utc(),
                                    "trade_id": tr.get("trade_id") or tr.get("i"),
                                    "side": tr.get("side")
                                }
                                producer.send(topic, value=rec, key=product_id)
                    # Certains messages "subscriptions"/"status" → ignorer
        except Exception:
            await asyncio.sleep(backoff)
            backoff = min(backoff*2, 30)

if __name__ == "__main__":
    asyncio.run(run())
