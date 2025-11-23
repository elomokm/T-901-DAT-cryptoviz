"""
Bootstrap endpoint - NEVER-FAIL mode pour production
Retourne TOUJOURS des données (cache stale si nécessaire)
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, Optional, List, Tuple
import asyncio
import logging

from app.direct_api_fetcher import DirectAPIFetcher
from app.influx_client import InfluxClientManager

router = APIRouter(prefix="/bootstrap", tags=["bootstrap"])
logger = logging.getLogger(__name__)

# Shared API fetcher
api_fetcher = DirectAPIFetcher()

# Cache simple pour fallback ultime (garde dernières données valides)
_EMERGENCY_CACHE = {
    'coins': None,
    'global': None,
    'fear_greed': None
}


def _fetch_coins_with_fallback(limit: int) -> Tuple[List[Dict], Dict]:
    """Fetch coins avec fallback automatique - NEVER FAIL"""
    try:
        coins, metadata = api_fetcher.fetch_coin_list(page=1, limit=limit)
        if coins:
            # Update emergency cache
            _EMERGENCY_CACHE['coins'] = (coins, metadata)
            return coins, metadata
    except Exception as e:
        logger.warning(f"API coins fetch failed: {e}")
    
    # Fallback 1: InfluxDB
    try:
        logger.info("📊 Fallback to InfluxDB for coins...")
        coins = _fetch_coins_from_influx(limit)
        if coins:
            metadata = {'source': 'influxdb_fallback', 'stale': True, 'rate_limited': True}
            return coins, metadata
    except Exception as e:
        logger.warning(f"InfluxDB fallback failed: {e}")
    
    # Fallback 2: Emergency cache (données très anciennes mais mieux que rien)
    if _EMERGENCY_CACHE['coins']:
        logger.warning("🆘 Using EMERGENCY cache for coins")
        coins, metadata = _EMERGENCY_CACHE['coins']
        metadata['emergency'] = True
        return coins, metadata
    
    # Vraiment rien - retourner liste vide
    return [], {'source': 'empty', 'stale': True, 'rate_limited': True}


def _fetch_global_with_fallback() -> Optional[Dict]:
    """Fetch global stats avec fallback - peut retourner None"""
    try:
        stats = api_fetcher.fetch_global_stats()
        if stats:
            _EMERGENCY_CACHE['global'] = stats
            return stats
    except Exception as e:
        logger.warning(f"Global stats fetch failed: {e}")
    
    # Fallback: emergency cache
    if _EMERGENCY_CACHE['global']:
        logger.info("Using cached global stats")
        return _EMERGENCY_CACHE['global']
    
    return None


def _fetch_fear_greed_with_fallback() -> Optional[Dict]:
    """Fetch fear/greed avec fallback - peut retourner None"""
    try:
        data = api_fetcher.fetch_fear_greed()
        if data:
            _EMERGENCY_CACHE['fear_greed'] = data
            return data
    except Exception as e:
        logger.warning(f"Fear/Greed fetch failed: {e}")
    
    # Fallback: emergency cache
    if _EMERGENCY_CACHE['fear_greed']:
        logger.info("Using cached fear/greed")
        return _EMERGENCY_CACHE['fear_greed']
    
    return None


def _fetch_coins_from_influx(limit: int = 50) -> List[Dict]:
    """
    Fallback InfluxDB: Récupère coins depuis données historiques
    """
    try:
        client = InfluxClientManager.get_client()
        
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
                coins.append({
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
                })
        
        logger.info(f"✅ InfluxDB: {len(coins)} coins fetched")
        return coins
        
    except Exception as e:
        logger.error(f"❌ InfluxDB error: {e}")
        return []


@router.get("")
async def get_bootstrap(
    limit: int = Query(50, ge=1, le=250, description="Number of coins to fetch"),
    sparkline: bool = Query(True, description="Include 7-day sparkline data")
) -> Dict[str, Any]:
    """
    🚀 Bootstrap endpoint - NEVER-FAIL MODE
    
    Garanties production:
    - JAMAIS d'erreur HTTP 500
    - TOUJOURS retourne des données (même anciennes)
    - Fallback cascade: API → InfluxDB → Emergency cache
    - Mode dégradé totalement transparent pour l'utilisateur
    
    Returns:
    - coins: Liste cryptos (JAMAIS vide grâce aux fallbacks)
    - global: Stats globales (None si indisponible, pas critique)
    - fearGreed: Index (None si indisponible, pas critique)
    - Metadata: source, stale, rate_limited pour monitoring
    """
    # Valeurs par défaut safe
    coins_list = []
    coins_metadata = {'source': 'unknown', 'stale': False, 'rate_limited': False}
    global_stats = None
    fear_greed = None
    
    try:
        # Fetch all data in parallel
        coins_task = asyncio.to_thread(_fetch_coins_with_fallback, limit)
        global_task = asyncio.to_thread(_fetch_global_with_fallback)
        fear_greed_task = asyncio.to_thread(_fetch_fear_greed_with_fallback)
        
        coins_result, global_result, fear_greed_result = await asyncio.gather(
            coins_task,
            global_task,
            fear_greed_task,
            return_exceptions=True
        )
        
        # Handle coins (CRITIQUE - doit avoir des données)
        if not isinstance(coins_result, Exception) and coins_result:
            coins_list, coins_metadata = coins_result
            logger.info(f"✅ Bootstrap coins: {len(coins_list)} items from {coins_metadata.get('source')}")
        else:
            logger.error(f"❌ CRITICAL: All coins fallbacks failed!")
            coins_list = []
            coins_metadata = {'source': 'failed', 'stale': True, 'rate_limited': True}
        
        # Handle global stats (NON-CRITIQUE)
        if not isinstance(global_result, Exception):
            global_stats = global_result
        else:
            logger.warning(f"Global stats unavailable (non-critical)")
        
        # Handle fear/greed (NON-CRITIQUE)
        if not isinstance(fear_greed_result, Exception):
            fear_greed = fear_greed_result
        else:
            logger.warning(f"Fear/Greed unavailable (non-critical)")
        
        # Return data (NEVER raise exception)
        return {
            "coins": coins_list,
            "global": global_stats,
            "fearGreed": fear_greed,
            "stale": coins_metadata.get('stale', False),
            "rate_limited": coins_metadata.get('rate_limited', False),
            "source": coins_metadata.get('source', 'unknown'),
            "method": coins_metadata.get('method', 'direct'),
            "emergency": coins_metadata.get('emergency', False)
        }
        
    except Exception as e:
        # DERNIÈRE LIGNE DE DÉFENSE - ne JAMAIS crash
        logger.error(f"❌ FATAL bootstrap error: {e}", exc_info=True)
        
        # Retourner emergency cache ou données vides
        emergency_coins, emergency_meta = _EMERGENCY_CACHE.get('coins', ([], {}))
        
        return {
            "coins": emergency_coins,
            "global": _EMERGENCY_CACHE.get('global'),
            "fearGreed": _EMERGENCY_CACHE.get('fear_greed'),
            "stale": True,
            "rate_limited": True,
            "source": "emergency_recovery",
            "method": "cached",
            "emergency": True,
            "error": str(e)
        }
