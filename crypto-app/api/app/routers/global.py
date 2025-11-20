from fastapi import APIRouter

from ..models import GlobalStats
from ..services.global_service import get_global_stats

router = APIRouter(prefix="/global", tags=["global"])

@router.get("", response_model=GlobalStats)
def get_global():
    return get_global_stats()
