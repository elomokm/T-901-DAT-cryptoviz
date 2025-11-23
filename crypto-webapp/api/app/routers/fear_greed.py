from fastapi import APIRouter, HTTPException
import requests
from app.models import FearGreedIndex

router = APIRouter(tags=["fear-greed"])


def classify_fear_greed(value: int) -> str:
    """Classify fear and greed index value."""
    if value <= 25:
        return "Extreme Fear"
    elif value <= 45:
        return "Fear"
    elif value <= 55:
        return "Neutral"
    elif value <= 75:
        return "Greed"
    else:
        return "Extreme Greed"


@router.get("/fear-greed", response_model=FearGreedIndex)
async def get_fear_greed():
    """
    Get fear & greed index directly from Alternative.me API.
    NO INFLUXDB REQUIRED!
    """
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            # Fallback to neutral if API fails
            return FearGreedIndex(value=50, classification="Neutral", timestamp="")
        
        data = response.json().get("data", [{}])[0]
        value = int(data.get("value", 50))
        
        return FearGreedIndex(
            value=value,
            classification=classify_fear_greed(value),
            timestamp=data.get("timestamp", "")
        )
        
    except requests.RequestException:
        # Fallback to neutral if API fails
        return FearGreedIndex(value=50, classification="Neutral", timestamp="")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
