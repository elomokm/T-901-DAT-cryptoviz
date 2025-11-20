from fastapi import APIRouter, HTTPException, Query
from typing import Literal
import requests
from datetime import datetime, timedelta
from app.influx_client import get_query_api, get_bucket
from app.models import Coin, CoinHistory, PaginatedCoins

router = APIRouter(prefix="/coins", tags=["coins"])

# Cache simple pour les infos CoinGecko (éviter trop d'appels API)
_coingecko_cache = {}


def fetch_coingecko_historical(coin_id: str, days: int) -> dict:
    """
    Fetch historical data directly from CoinGecko API (primary source).
    Returns complete data in one call - no need for scraping!
    """
    try:
        # CoinGecko market_chart endpoint - données historiques complètes
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'hourly' if days <= 7 else 'daily'
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Aussi récupérer les infos actuelles
            coin_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            coin_response = requests.get(coin_url, params={
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false'
            }, timeout=10)
            
            coin_info = coin_response.json() if coin_response.status_code == 200 else {}
            
            return {
                'success': True,
                'source': 'coingecko_api',
                'prices': data.get('prices', []),
                'market_caps': data.get('market_caps', []),
                'volumes': data.get('total_volumes', []),
                'coin_info': coin_info
            }
        else:
            print(f"⚠️  CoinGecko API error {response.status_code}")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ CoinGecko historical fetch error: {e}")
        return {'success': False}


def fetch_influxdb_fallback(coin_id: str, time_range: str, interval: str) -> dict:
    """
    Fallback: fetch from InfluxDB if API fails.
    Uses scraped data stored in the database.
    """
    try:
        query_api = get_query_api()
        bucket = get_bucket()
        
        # Query InfluxDB pour fallback
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: {time_range})
            |> filter(fn: (r) => r._measurement == "crypto_market")
            |> filter(fn: (r) => r.crypto_id == "{coin_id}")
            |> filter(fn: (r) => r._field == "price_usd")
            |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
        '''
        
        tables = query_api.query(query)
        prices = []
        
        for table in tables:
            for record in table.records:
                prices.append([
                    int(record.get_time().timestamp() * 1000),
                    float(record.get_value())
                ])
        
        if prices:
            return {
                'success': True,
                'source': 'influxdb_fallback',
                'prices': prices,
                'market_caps': [],
                'volumes': []
            }
        else:
            return {'success': False}
            
    except Exception as e:
        print(f"❌ InfluxDB fallback error: {e}")
        return {'success': False}

def get_coingecko_info(coin_id: str) -> dict:
    """Fetch additional info from CoinGecko API (cached)"""
    if coin_id in _coingecko_cache:
        return _coingecko_cache[coin_id]
    
    try:
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}",
            params={"localization": "false", "tickers": "false", "market_data": "false", "community_data": "false", "developer_data": "false"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            info = {
                "description": data.get("description", {}).get("en", ""),
                "homepage": data.get("links", {}).get("homepage", [""])[0],
                "whitepaper": data.get("links", {}).get("whitepaper", ""),
                "blockchain_site": data.get("links", {}).get("blockchain_site", [])[:3],  # Top 3 explorers
            }
            _coingecko_cache[coin_id] = info
            return info
    except Exception as e:
        print(f"Error fetching CoinGecko info for {coin_id}: {e}")
    
    return {"description": "", "homepage": "", "whitepaper": "", "blockchain_site": []}


@router.get("", response_model=PaginatedCoins)
async def get_coins(
    limit: int = Query(default=100, ge=1, le=500),
    page: int = Query(default=1, ge=1),
    order: Literal["market_cap_desc", "price_desc", "volume_desc"] = "market_cap_desc"
):
    """Get list of coins with pagination and sorting."""
    query_api = get_query_api()
    bucket = get_bucket()

    # Map order parameter to InfluxDB field
    order_field_map = {
        "market_cap_desc": "market_cap",
        "price_desc": "price_usd",
        "volume_desc": "volume_24h"
    }
    order_field = order_field_map.get(order, "market_cap")

    try:
        # Query to get the latest data for each coin
        # Measurement aligned with consumers: "crypto_market"
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "crypto_market")
            |> pivot(rowKey:["_time", "crypto_id"], columnKey: ["_field"], valueColumn: "_value")
            |> group(columns: ["crypto_id"])
            |> last(column: "_time")
            |> group()
        '''

        tables = query_api.query(query)

        coins_data = []
        for table in tables:
            for record in table.records:
                # Map InfluxDB fields to frontend-expected field names
                coin_data = {
                    "id": record.values.get("crypto_id", ""),
                    "name": record.values.get("name"),
                    "symbol": record.values.get("symbol"),
                    "current_price": float(record.values.get("price_usd", 0)),
                    "market_cap": float(record.values.get("market_cap", 0)),
                    "market_cap_rank": int(record.values.get("market_cap_rank", 0)) if record.values.get("market_cap_rank") else 0,
                    "total_volume": float(record.values.get("volume_24h", 0)),
                    "price_change_percentage_24h": record.values.get("change_24h", 0),
                    "price_change_percentage_7d": record.values.get("change_7d"),
                    "circulating_supply": record.values.get("circulating_supply", 0),
                    "total_supply": record.values.get("total_supply"),
                    "max_supply": record.values.get("max_supply"),
                    "ath": record.values.get("ath", 0),
                    "ath_change_percentage": record.values.get("ath_change_pct", 0),
                    "ath_date": record.values.get("ath_date", ""),
                }
                coin = Coin(**coin_data)
                coins_data.append(coin)

        # Sort coins based on order parameter
        if order == "market_cap_desc":
            coins_data.sort(key=lambda x: x.market_cap or 0, reverse=True)
        elif order == "price_desc":
            coins_data.sort(key=lambda x: x.price_usd or 0, reverse=True)
        elif order == "volume_desc":
            coins_data.sort(key=lambda x: x.volume_24h or 0, reverse=True)

        # Pagination
        total = len(coins_data)
        total_pages = (total + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_coins = coins_data[start_idx:end_idx]

        return PaginatedCoins(
            coins=paginated_coins,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")


@router.get("/{coin_id}", response_model=Coin)
async def get_coin(coin_id: str):
    """Get details for a specific coin."""
    query_api = get_query_api()
    bucket = get_bucket()

    try:
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "crypto_market")
            |> filter(fn: (r) => r.crypto_id == "{coin_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> last(column: "_time")
        '''

        tables = query_api.query(query)

        for table in tables:
            for record in table.records:
                coin_data = {
                    "id": coin_id,
                    "name": record.values.get("name"),
                    "symbol": record.values.get("symbol"),
                    "current_price": float(record.values.get("price_usd", 0)),
                    "market_cap": float(record.values.get("market_cap", 0)),
                    "market_cap_rank": int(record.values.get("market_cap_rank", 0)) if record.values.get("market_cap_rank") else None,
                    "total_volume": float(record.values.get("volume_24h", 0)),
                    "price_change_percentage_24h": record.values.get("change_24h"),
                    "price_change_percentage_7d": record.values.get("change_7d"),
                    "ath": record.values.get("ath"),
                    "ath_change_percentage": record.values.get("ath_change_pct"),
                    "ath_date": record.values.get("ath_date"),
                    "circulating_supply": record.values.get("circulating_supply"),
                    "total_supply": record.values.get("total_supply"),
                    "max_supply": record.values.get("max_supply"),
                }
                return Coin(**coin_data)

        raise HTTPException(status_code=404, detail=f"Coin '{coin_id}' not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")


@router.get("/{coin_id}/history")
async def get_coin_history(
    coin_id: str,
    days: int = Query(default=7, ge=0, le=365),
    interval: str = Query(default="1h", regex="^(1m|5m|15m|30m|1h|4h|1d)$"),
    hours: int = Query(default=0, ge=0, le=168)  # Pour les périodes < 1 jour
):
    """
    Get price history with hybrid approach:
    1. Try CoinGecko API (fetch all historical data in one call)
    2. Fallback to InfluxDB if API fails
    
    This way we're not dependent on scrapers for historical data!
    """
    
    # Calculer le nombre de jours total
    total_days = days if days > 0 else hours / 24
    
    # STRATÉGIE 1: Essayer CoinGecko API directement (RECOMMANDÉ)
    print(f"🔍 Fetching {total_days}d of {coin_id} from CoinGecko API...")
    cg_data = fetch_coingecko_historical(coin_id, int(total_days) if total_days >= 1 else 1)
    
    if cg_data['success']:
        print(f"✅ CoinGecko API: {len(cg_data['prices'])} data points fetched")
        
        # Extraire les données
        coin_info = cg_data.get('coin_info', {})
        market_data = coin_info.get('market_data', {})
        
        # Préparer la réponse
        coin_data = {
            "id": coin_id,
            "name": coin_info.get('name', coin_id.title()),
            "symbol": coin_info.get('symbol', coin_id[:3]).upper(),
            "current_price": market_data.get('current_price', {}).get('usd', 0),
            "market_cap": market_data.get('market_cap', {}).get('usd', 0),
            "market_cap_rank": market_data.get('market_cap_rank'),
            "total_volume": market_data.get('total_volume', {}).get('usd', 0),
            "high_24h": market_data.get('high_24h', {}).get('usd', 0),
            "low_24h": market_data.get('low_24h', {}).get('usd', 0),
            "price_change_24h": market_data.get('price_change_24h', 0),
            "price_change_percentage_24h": market_data.get('price_change_percentage_24h', 0),
            "price_change_percentage_7d": market_data.get('price_change_percentage_7d', 0),
            "price_change_percentage_30d": market_data.get('price_change_percentage_30d', 0),
            "circulating_supply": market_data.get('circulating_supply', 0),
            "total_supply": market_data.get('total_supply'),
            "max_supply": market_data.get('max_supply'),
            "ath": market_data.get('ath', {}).get('usd', 0),
            "ath_change_percentage": market_data.get('ath_change_percentage', {}).get('usd', 0),
            "ath_date": market_data.get('ath_date', {}).get('usd', ''),
            "atl": market_data.get('atl', {}).get('usd', 0),
            "atl_change_percentage": market_data.get('atl_change_percentage', {}).get('usd', 0),
            "atl_date": market_data.get('atl_date', {}).get('usd', ''),
            "description": coin_info.get('description', {}).get('en', ''),
            "homepage": coin_info.get('links', {}).get('homepage', [''])[0],
            "whitepaper": coin_info.get('links', {}).get('whitepaper', ''),
            "blockchain_site": coin_info.get('links', {}).get('blockchain_site', [])[:3],
        }
        
        # Formater les prix pour le frontend
        prices = []
        for price_point in cg_data['prices']:
            prices.append({
                'timestamp': datetime.fromtimestamp(price_point[0] / 1000).isoformat(),
                'price': price_point[1]
            })
        
        coin_data['prices'] = prices
        
        return coin_data
    
    # STRATÉGIE 2: Fallback InfluxDB (données scrapées)
    print(f"⚠️  CoinGecko API failed, trying InfluxDB fallback...")
    
    query_api = get_query_api()
    bucket = get_bucket()
    
    # Déterminer la durée InfluxDB
    if hours > 0:
        time_range = f"-{hours}h"
    elif days == 0:
        time_range = "-1h"
    else:
        time_range = f"-{days}d"

    # Map interval to InfluxDB duration
    interval_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d"
    }
    influx_interval = interval_map.get(interval, "1h")

    try:
        # Get current coin data
        coin_query = f'''
        from(bucket: "{bucket}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "crypto_market")
            |> filter(fn: (r) => r.crypto_id == "{coin_id}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> last(column: "_time")
        '''
        
        coin_tables = query_api.query(coin_query)
        coin_data = None
        
        for table in coin_tables:
            for record in table.records:
                coin_data = {
                    "id": coin_id,
                    "name": record.values.get("name"),
                    "symbol": record.values.get("symbol"),
                    "current_price": float(record.values.get("price_usd", 0)),
                    "market_cap": float(record.values.get("market_cap", 0)),
                    "market_cap_rank": int(record.values.get("market_cap_rank", 0)) if record.values.get("market_cap_rank") else None,
                    "total_volume": float(record.values.get("volume_24h", 0)),
                    "high_24h": float(record.values.get("price_usd", 0)),  # Simplified for now
                    "low_24h": float(record.values.get("price_usd", 0)),   # Simplified for now
                    "price_change_24h": record.values.get("change_24h", 0),
                    "price_change_percentage_24h": record.values.get("change_24h"),
                    "price_change_percentage_7d": record.values.get("change_7d"),
                    "circulating_supply": record.values.get("circulating_supply", 0),
                    "total_supply": record.values.get("total_supply"),
                    "max_supply": record.values.get("max_supply"),
                    "ath": record.values.get("ath", 0),
                    "ath_change_percentage": record.values.get("ath_change_pct", 0),
                    "ath_date": record.values.get("ath_date", ""),
                    "atl": record.values.get("atl", 0),
                    "atl_change_percentage": record.values.get("atl_change_pct", 0),
                    "atl_date": record.values.get("atl_date", ""),
                }
                break
        
        if not coin_data:
            raise HTTPException(status_code=404, detail=f"Coin '{coin_id}' not found")
        
        # Calculate 24h high/low from price history
        high_low_query = f'''
        from(bucket: "{bucket}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "crypto_market")
            |> filter(fn: (r) => r.crypto_id == "{coin_id}")
            |> filter(fn: (r) => r._field == "price_usd")
        '''
        
        high_low_tables = query_api.query(high_low_query)
        prices_24h = []
        for table in high_low_tables:
            for record in table.records:
                prices_24h.append(float(record.get_value()))
        
        if prices_24h:
            coin_data["high_24h"] = max(prices_24h)
            coin_data["low_24h"] = min(prices_24h)
        else:
            # Fallback to current price if no history
            coin_data["high_24h"] = coin_data["current_price"]
            coin_data["low_24h"] = coin_data["current_price"]
        
        # Enrichir avec les infos CoinGecko
        coingecko_info = get_coingecko_info(coin_id)
        coin_data.update(coingecko_info)
        
        # Get price history
        history_query = f'''
        from(bucket: "{bucket}")
            |> range(start: {time_range})
            |> filter(fn: (r) => r._measurement == "crypto_market")
            |> filter(fn: (r) => r.crypto_id == "{coin_id}")
            |> filter(fn: (r) => r._field == "price_usd")
            |> aggregateWindow(every: {influx_interval}, fn: mean, createEmpty: false)
            |> yield(name: "mean")
        '''

        history_tables = query_api.query(history_query)

        prices = []
        for table in history_tables:
            for record in table.records:
                prices.append({
                    "timestamp": record.get_time().isoformat(),
                    "price": float(record.get_value())
                })

        # Sort by timestamp
        prices.sort(key=lambda x: x["timestamp"])
        
        # Combine coin data with price history
        return {
            **coin_data,
            "prices": prices
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")
