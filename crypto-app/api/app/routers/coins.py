from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from ..models import CoinSummary, CoinHistoryResponse
from ..services.coins_service import list_coins, get_coin_detail, get_coin_history

router = APIRouter(prefix="/coins", tags=["coins"])

@router.get("", response_model=List[CoinSummary])
def get_coins(
    limit: int = Query(50, ge=1, le=250),
    page: int = Query(1, ge=1),
    order: str = Query("market_cap_desc", pattern="^(market_cap|price|volume)_(asc|desc)$"),
    ids: Optional[str] = Query(None, description="Comma-separated crypto ids to filter"),
):
    ids_list = [i.strip() for i in ids.split(",") if i.strip()] if ids else None
    return list_coins(limit=limit, page=page, order=order, ids=ids_list)


@router.get("/{crypto_id}", response_model=CoinSummary)
def get_coin(crypto_id: str):
    coin = get_coin_detail(crypto_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin


@router.get("/{crypto_id}/history", response_model=CoinHistoryResponse)
def get_coin_history_route(
    crypto_id: str,
    days: int = Query(7, ge=1, le=365),
    interval: str = Query("1h"),
):
    return get_coin_history(crypto_id=crypto_id, days=days, interval=interval)
