# Pydantic: TradeRaw, TradeNormalized, CandleAgg
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TradeRaw(BaseModel):
    source: str
    symbol_source: str        # ex: BTCUSDT
    price: float
    amount: float
    ts_event: datetime        # event time (exchange)
    ts_ingest: datetime       # time we received/produced
    trade_id: Optional[str] = None
    side: Optional[str] = None

class TradeNormalized(BaseModel):
    source: str               # binance, coinbase, ...
    symbol: str               # canonique ex: BTC-USDT
    price: float
    amount: float
    ts_event: datetime
    ts_ingest: datetime
    trade_id: Optional[str] = None
    side: Optional[str] = None
    schema_version: int = Field(default=0)

class CandleAgg(BaseModel):
    symbol: str
    window_start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    sources_used: Optional[List[str]] = None
