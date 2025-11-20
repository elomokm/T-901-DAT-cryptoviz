from fastapi import APIRouter, Query
from typing import List, Dict, Any
from ..config import settings
from ..influx_client import get_query_api

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/influx/summary")
def influx_summary(hours: int = Query(6, ge=1, le=48)):
    """Return basic diagnostics about data presence in InfluxDB.

    - Distinct crypto_ids with at least one point in the last `hours`
    - Last timestamp per crypto and overall latest
    - Total raw points written in last hour (all fields)
    """
    qa = get_query_api()

    # Snapshot query (one latest row per crypto_id per field; we only need times)
    flux_snap = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -{hours}h)
  |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
  |> group(columns: ["crypto_id", "symbol", "name", "_field"]) 
  |> last()
"""
    tables = qa.query(org=settings.influx_org, query=flux_snap)
    crypto_last: Dict[str, Any] = {}
    latest_ts = None
    for table in tables:
        for rec in table.records:
            cid = rec.values.get("crypto_id")
            t = rec.get_time()
            prev = crypto_last.get(cid)
            if not prev or t > prev:
                crypto_last[cid] = t
            if latest_ts is None or t > latest_ts:
                latest_ts = t

    # Count points in last hour
    flux_count = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
  |> count()
"""
    count_tables = qa.query(org=settings.influx_org, query=flux_count)
    total_points_last_hour = 0
    for table in count_tables:
        for rec in table.records:
            v = rec.get_value()
            if isinstance(v, (int, float)):
                total_points_last_hour += int(v)

    return {
        "bucket": settings.influx_bucket,
        "measurement": settings.influx_measurement,
        "crypto_count": len(crypto_last),
        "crypto_ids": sorted(list(crypto_last.keys())),
        "latest_timestamp_any": latest_ts,
        "total_points_last_hour": total_points_last_hour,
        "hours_window": hours,
    }
