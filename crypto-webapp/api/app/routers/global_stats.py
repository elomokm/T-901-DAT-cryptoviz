from fastapi import APIRouter, HTTPException
import requests
from app.models import GlobalStats
from app.smart_cache import smart_cache

router = APIRouter(tags=["global"])


@router.get("/global", response_model=GlobalStats)
async def get_global_stats():
    """
    Get global market statistics with SmartCache & fallback APIs.
    Techniques anti-rate-limit:
    - Cache 2min (stats globales changent peu)
    - Fallback CoinPaprika si CoinGecko rate limited
    - Stale-while-revalidate (retourne vieux cache si tout échoue)
    """
    cache_key = "global_stats"
    
    def fetch_coingecko_global():
        """Primary: CoinGecko"""
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {})
    
    def fetch_coinpaprika_global():
        """Fallback: CoinPaprika"""
        url = "https://api.coinpaprika.com/v1/global"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Transform to CoinGecko format
        return {
            'total_market_cap': {'usd': data.get('market_cap_usd', 0)},
            'total_volume': {'usd': data.get('volume_24h_usd', 0)},
            'market_cap_change_percentage_24h_usd': data.get('market_cap_change_24h', 0),
            'active_cryptocurrencies': data.get('cryptocurrencies_number', 0),
            'markets': 0,
            'market_cap_percentage': {
                'btc': data.get('bitcoin_dominance_percentage', 0), 
                'eth': 0
            }
        }
    
    try:
        data = smart_cache.fetch_with_fallback(
            key=cache_key,
            primary_fetcher=fetch_coingecko_global,
            fallback_fetchers=[fetch_coinpaprika_global],
            ttl=120  # 2 minutes - stats changent peu
        )
        
        if not data:
            raise HTTPException(status_code=503, detail="All APIs unavailable")
        
        return GlobalStats(
            total_market_cap=data.get("total_market_cap", {}).get("usd", 0),
            total_volume=data.get("total_volume", {}).get("usd", 0),
            market_cap_change_percentage_24h=data.get("market_cap_change_percentage_24h_usd", 0),
            active_cryptocurrencies=data.get("active_cryptocurrencies", 0),
            markets=data.get("markets", 0),
            market_cap_percentage=data.get("market_cap_percentage", {"btc": 0, "eth": 0})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
