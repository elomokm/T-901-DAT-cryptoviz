from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class GlobalStats(BaseModel):
    total_market_cap: float
    total_volume: float = 0  # Renamed from total_volume_24h
    market_cap_change_percentage_24h: float = 0
    active_cryptocurrencies: int  # Renamed from count
    markets: int = 0  # Not available, set default
    market_cap_percentage: dict = {"btc": 0, "eth": 0}  # Not available, set default


class Coin(BaseModel):
    id: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    current_price: float
    market_cap: float
    market_cap_rank: Optional[int] = None
    total_volume: float
    price_change_percentage_24h: Optional[float] = None
    price_change_percentage_7d: Optional[float] = None
    ath: Optional[float] = None
    ath_change_percentage: Optional[float] = None
    ath_date: Optional[str] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None


class CoinDetail(Coin):
    """Extended coin model with additional details"""
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_30d: Optional[float] = None
    atl: Optional[float] = None
    atl_change_percentage: Optional[float] = None
    atl_date: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    whitepaper: Optional[str] = None
    blockchain_site: Optional[list] = []


class CoinHistory(BaseModel):
    timestamp: datetime
    price_usd: float


class NewsArticle(BaseModel):
    title: str
    link: str
    published_date: Optional[datetime] = None
    source: str
    description: Optional[str] = None


class NewsSource(BaseModel):
    name: str
    count: int


class FearGreedIndex(BaseModel):
    value: int
    classification: str
    timestamp: datetime


class CryptoAnalytics(BaseModel):
    crypto_id: str
    symbol: str
    name: str
    price_mean: float
    price_std: float
    price_min: float
    price_max: float
    price_range: float
    volatility_pct: float
    volume_mean: float
    volume_std: float
    anomaly_count: int
    data_points: int
    timestamp: datetime


class ComparisonResult(BaseModel):
    cryptos: list
    period: str
    comparison_time: str
    rankings: dict


class PaginatedCoins(BaseModel):
    coins: list[Coin]
    total: int
    page: int
    limit: int
    total_pages: int
