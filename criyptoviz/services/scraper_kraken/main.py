import os, asyncio, json
from datetime import datetime, timezone
import websockets
from common.kafka_io import make_producer

WS_URL = "wss://ws.kraken.com/"

def now(): return datetime.now(timezone.utc)

def build_sub(pairs):
    # pairs: ex "XBT/USDT"
    return {"event":"subscribe", "pair": pairs, "subscription":{"name":"trade"}}

def parse_trade(msg):
    # Format: [channelID, [ [price, volume, time, side, orderType, misc], ...], "trade", "pair"]
    if isinstance(msg, list) and len(msg) >= 4 and msg[2] == "trade":
        pair = msg[3]
        for tr in msg[1]:
            price = float(tr[0]); amount = float(tr[1])
            ts_event = datetime.fromtimestamp(float(tr[2]), tz=timezone.utc)
            yield pair, price, amount, ts_event

async def run():
    pairs = os.getenv("KRAKEN_PAIRS_CSV","XBT/USDT,ETH/USDT").split(",")
    topic = os.getenv("OUTPUT_TOPIC","market.raw.trade.kraken")
    producer = make_producer()
    backoff = 1
    print(f"[scraper-kraken] start pairs={pairs} -> {topic}")
    while True:
        try:
            print("[scraper-kraken] connecting WS ...")
            async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=10) as ws:
                await ws.send(json.dumps(build_sub(pairs)))
                backoff = 1
                n=0
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if isinstance(msg, dict):
                        # status/heartbeat → ignore
                        continue
                    for pair, price, amount, ts_event in parse_trade(msg):
                        rec = {
                            "source":"kraken",
                            "symbol_source": pair,   # ex "XBT/USDT"
                            "price": price,
                            "amount": amount,
                            "ts_event": ts_event,
                            "ts_ingest": now(),
                            "trade_id": None,
                            "side": None
                        }
                        producer.send(topic, value=rec, key=pair)
                        n += 1
                        if n % 200 == 0:
                            print(f"[scraper-kraken] sent {n}")
        except Exception as e:
            print(f"[scraper-kraken] error: {repr(e)} (retry)")
            await asyncio.sleep(backoff)
            backoff = min(backoff*2, 30)

if __name__ == "__main__":
    asyncio.run(run())
