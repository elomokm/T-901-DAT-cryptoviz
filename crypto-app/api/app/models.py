from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class PricePoint(BaseModel):
    time: datetime
    value: float

class CoinSummary(BaseModel):
    id: str
    symbol: str
    name: str
    price_usd: float
    market_cap: Optional[float] = None
    market_cap_rank: Optional[int] = None
    volume_24h: Optional[float] = None
    change_1h: Optional[float] = None
    change_24h: Optional[float] = None
    change_7d: Optional[float] = None
    ath: Optional[float] = None
    ath_change_pct: Optional[float] = None
    atl: Optional[float] = None
    atl_change_pct: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    last_updated: datetime
    sparkline_7d: Optional[List[float]] = None  # placeholder

class GlobalStats(BaseModel):
    total_market_cap: float
    total_volume_24h: float
    market_cap_change_24h: Optional[float] = None
    count: int

class CoinHistoryResponse(BaseModel):
    id: str
    days: int
    interval: str
    series: List[PricePoint]

class NewsArticle(BaseModel):
    title: str
    link: str
    published_date: str
    source: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class NewsResponse(BaseModel):
    count: int
    news: List[NewsArticle]
