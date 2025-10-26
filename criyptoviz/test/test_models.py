from common.models import TradeNormalized
from datetime import datetime, timezone

def test_trade_normalized_valid():
    t = TradeNormalized(
        source="binance",
        symbol="BTC-USDT",
        price=60000.0,
        amount=0.01,
        ts_event=datetime.now(timezone.utc),
        ts_ingest=datetime.now(timezone.utc),
    )
    assert t.symbol == "BTC-USDT"
