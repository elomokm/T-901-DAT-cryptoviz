"""
Bootstrap endpoint - optimized single call to fetch all dashboard data
Combines coins list, global stats, and fear/greed index
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import asyncio
import logging

from app.direct_api_fetcher import DirectAPIFetcher
from app.influx_client import InfluxClientManager

router = APIRouter(prefix="/bootstrap", tags=["bootstrap"])
logger = logging.getLogger(__name__)

# Shared DirectAPIFetcher instance
api_fetcher = DirectAPIFetcher()


def _fetch_coins_from_influx(limit: int = 50) -> List[Dict]:
    """
    Fallback: Fetch coins from InfluxDB historical data
    Used when external APIs are rate-limited
    """
    try:
        client = InfluxClientManager.get_client()
        
        # Query recent data for top coins
        query = f"""
        from(bucket: "crypto_data")
            |> range(start: -1h)
            |> filter(fn: (r) => r["_measurement"] == "crypto_prices")
            |> filter(fn: (r) => r["_field"] == "current_price" or r["_field"] == "market_cap")
            |> group(columns: ["crypto_id"])
            |> last()
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> group()
            |> sort(columns: ["market_cap"], desc: true)
            |> limit(n: {limit})
        """
        
        tables = client.query_api().query(query)
        
        coins = []
        for table in tables:
            for record in table.records:
                coin_data = {
                    'id': record.values.get('crypto_id'),
                    'symbol': record.values.get('symbol', '').upper(),
                    'name': record.values.get('name', record.values.get('crypto_id', '').title()),
                    'image': None,
                    'current_price': record.values.get('current_price'),
                    'market_cap': record.values.get('market_cap'),
                    'market_cap_rank': None,
                    'total_volume': None,
                    'price_change_24h': None,
                    'price_change_percentage_24h': None,
                    'sparkline_in_7d': []
                }
                coins.append(coin_data)
        
        logger.info(f"✅ Fetched {len(coins)} coins from InfluxDB")
        return coins
        
    except Exception as e:
        logger.error(f"❌ Error fetching from InfluxDB: {e}")
        return []


@router.get("")
async def get_bootstrap(
    limit: int = Query(50, ge=1, le=250, description="Number of coins to fetch"),
    sparkline: bool = Query(True, description="Include 7-day sparkline data")
) -> Dict[str, Any]:
    """
    🚀 Bootstrap endpoint - fetch all dashboard data in one optimized call
    
    Returns:
    - coins: Top cryptocurrencies with current prices and sparklines
    - global: Global market statistics
    - fearGreed: Fear & Greed index
    - Metadata: stale, rate_limited flags for cache status
    """
    try:
        # Run all three API calls in parallel for speed
        coins_task = asyncio.to_thread(api_fetcher.fetch_coin_list, page=1, limit=limit)
        global_task = asyncio.to_thread(api_fetcher.fetch_global_stats)
        fear_greed_task = asyncio.to_thread(api_fetcher.fetch_fear_greed)
        
        coins_data, global_data, fear_greed_data = await asyncio.gather(
            coins_task,
            global_task,
            fear_greed_task,
            return_exceptions=True
        )
        
        # Handle coins data
        coins_list = []
        coins_metadata = {}
        if isinstance(coins_data, Exception):
            logger.error(f"Coins fetch failed: {coins_data}")
            # Fallback to InfluxDB for coins list
            logger.info("📊 Falling back to InfluxDB for coins list...")
            try:
                coins_list = await asyncio.to_thread(_fetch_coins_from_influx, limit)
                coins_metadata = {'source': 'influxdb_fallback', 'stale': True, 'rate_limited': True}
            except Exception as e:
                logger.error(f"InfluxDB fallback failed: {e}")
        elif coins_data and len(coins_data) == 2:
            coins_list, coins_metadata = coins_data
        else:
            # Empty response, try InfluxDB fallback
            logger.info("📊 Empty API response, falling back to InfluxDB...")
            try:
                coins_list = await asyncio.to_thread(_fetch_coins_from_influx, limit)
                coins_metadata = {'source': 'influxdb_fallback', 'stale': True, 'rate_limited': True}
            except Exception as e:
                logger.error(f"InfluxDB fallback failed: {e}")
        
        # Handle global stats
        global_stats = None
        if isinstance(global_data, Exception):
            logger.error(f"Global stats fetch failed: {global_data}")
        else:
            global_stats = global_data
        
        # Handle fear & greed
        fear_greed = None
        if isinstance(fear_greed_data, Exception):
            logger.error(f"Fear/Greed fetch failed: {fear_greed_data}")
        else:
            fear_greed = fear_greed_data
        
        # Determine overall cache status (worst case wins)
        stale = coins_metadata.get('stale', False)
        rate_limited = coins_metadata.get('rate_limited', False)
        
        return {
            "coins": coins_list,
            "global": global_stats,
            "fearGreed": fear_greed,
            "stale": stale,
            "rate_limited": rate_limited,
            "source": coins_metadata.get('source', 'api'),
            "method": coins_metadata.get('method', 'direct')
        }
        
    except Exception as e:
        logger.error(f"❌ Bootstrap fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch bootstrap data: {str(e)}")
