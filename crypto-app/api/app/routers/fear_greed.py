from fastapi import APIRouter, HTTPException

from ..services.fear_greed_service import get_latest_fear_greed

router = APIRouter(prefix="/fear-greed", tags=["fear-greed"])

@router.get("")
def fear_greed():
    data = get_latest_fear_greed()
    if not data:
        raise HTTPException(status_code=404, detail="Fear & Greed index not available")
    return data
