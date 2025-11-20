"""
Router pour les endpoints liés aux actualités crypto
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models import NewsArticle, NewsResponse
from app.services.news_service import get_latest_news

router = APIRouter(
    prefix="/news",
    tags=["News"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=NewsResponse)
async def get_news(
    limit: int = Query(default=20, ge=1, le=100, description="Nombre d'articles à retourner"),
    source: Optional[str] = Query(default=None, description="Filtrer par source (coindesk, cointelegraph)"),
    hours: int = Query(default=24, ge=1, le=168, description="Articles des X dernières heures")
):
    """
    Récupère les dernières actualités crypto.

    - **limit**: Nombre maximum d'articles (1-100)
    - **source**: Filtrer par source (optionnel)
    - **hours**: Articles des X dernières heures (1-168, default: 24h)
    """
    try:
        news = await get_latest_news(limit=limit, source=source, hours=hours)
        return NewsResponse(
            count=len(news),
            news=news
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/sources")
async def get_news_sources():
    """
    Retourne la liste des sources d'actualités disponibles.
    """
    return {
        "sources": [
            {
                "id": "coindesk",
                "name": "CoinDesk",
                "url": "https://www.coindesk.com"
            },
            {
                "id": "cointelegraph",
                "name": "CoinTelegraph",
                "url": "https://cointelegraph.com"
            }
        ]
    }
