from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import NewsArticle, NewsSource

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=list[NewsArticle])
async def get_news(
    limit: int = Query(default=20, ge=1, le=100),
    source: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get news articles.
    TODO: Integrate with real news API (CryptoPanic, CoinGecko News, etc.)
    For now returns empty list - InfluxDB not required.
    """
    # Placeholder - news feature requires separate implementation
    return []


@router.get("/sources", response_model=list[NewsSource])
async def get_news_sources():
    """Get available news sources with article counts."""
    # Placeholder - returns empty list
    return []
