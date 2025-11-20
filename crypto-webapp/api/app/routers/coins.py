from fastapi import APIRouter, HTTPException, Query
from typing import Literal
from app.influx_client import get_query_api, get_bucket
from app.models import Coin, CoinHistory, PaginatedCoins

router = APIRouter(prefix="/coins", tags=["coins"])


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
    days: int = Query(default=7, ge=1, le=365),
    interval: str = Query(default="1h", regex="^(1m|5m|15m|30m|1h|4h|1d)$")
):
    """Get price history and current coin details for a specific coin."""
    query_api = get_query_api()
    bucket = get_bucket()

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
        
        # Get price history
        history_query = f'''
        from(bucket: "{bucket}")
            |> range(start: -{days}d)
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
