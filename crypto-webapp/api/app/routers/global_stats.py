from fastapi import APIRouter, HTTPException
from app.influx_client import get_query_api, get_bucket
from app.models import GlobalStats

router = APIRouter(tags=["global"])


@router.get("/global", response_model=GlobalStats)
async def get_global_stats():
    """Get global market statistics."""
    query_api = get_query_api()
    bucket = get_bucket()

    try:
        # Query to get aggregated global stats
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

        total_market_cap = 0.0
        total_volume_24h = 0.0
        count = 0

        for table in tables:
            for record in table.records:
                market_cap = record.values.get("market_cap")
                volume = record.values.get("volume_24h")

                if market_cap:
                    total_market_cap += float(market_cap)
                if volume:
                    total_volume_24h += float(volume)
                count += 1

        return GlobalStats(
            total_market_cap=total_market_cap,
            total_volume=total_volume_24h,  # Renamed field
            market_cap_change_percentage_24h=0,  # Not yet calculated
            active_cryptocurrencies=count,  # Renamed from count
            markets=0,  # Not available yet
            market_cap_percentage={"btc": 0, "eth": 0}  # Not yet calculated
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")
