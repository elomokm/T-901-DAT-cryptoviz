from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config import settings
from ..influx_client import get_query_api
from ..models import CoinSummary, PricePoint, CoinHistoryResponse

# Fields we care about for the summary
SUMMARY_FIELDS = [
    "price_usd", "market_cap", "market_cap_rank", "volume_24h",
    "change_1h", "change_24h", "change_7d",
    "ath", "ath_change_pct", "atl", "atl_change_pct",
    "circulating_supply", "total_supply", "max_supply"
]


def _build_ids_regex(ids: List[str]) -> str:
    escaped = [i.replace("/", "\/") for i in ids]
    return f"^({'|'.join(escaped)})$"


def _query_last_snapshot(minutes_back: Optional[int] = None, filter_ids: Optional[List[str]] = None, order: str = "market_cap_desc") -> List[CoinSummary]:
    """Return latest snapshot for each crypto in the last window."""
    if minutes_back is None:
        minutes_back = settings.snapshot_minutes_back
    ids_filter = ""
    if filter_ids:
        ids_filter = f"\n  |> filter(fn: (r) => r.crypto_id =~ /{_build_ids_regex(filter_ids)}/)"

    flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -{minutes_back}m)
  |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
  |> filter(fn: (r) =>
      r._field == "price_usd" or
      r._field == "market_cap" or
      r._field == "market_cap_rank" or
      r._field == "volume_24h" or
      r._field == "change_1h" or
      r._field == "change_24h" or
      r._field == "change_7d" or
      r._field == "ath" or
      r._field == "ath_change_pct" or
      r._field == "atl" or
      r._field == "atl_change_pct" or
      r._field == "circulating_supply" or
      r._field == "total_supply" or
      r._field == "max_supply"
  )
    {ids_filter}
  |> group(columns: ["crypto_id", "symbol", "name", "_field"])
  |> last()
"""
    tables = get_query_api().query(org=settings.influx_org, query=flux)
    by_crypto: Dict[str, Dict[str, Any]] = {}

    for table in tables:
        for record in table.records:
            crypto_id = record["crypto_id"]
            if crypto_id not in by_crypto:
                by_crypto[crypto_id] = {
                    "id": crypto_id,
                    "symbol": record["symbol"],
                    "name": record["name"],
                    "last_updated": record.get_time(),
                }
            field = record["_field"]
            by_crypto[crypto_id][field] = record.get_value()
            # Update timestamp if newer
            if record.get_time() > by_crypto[crypto_id]["last_updated"]:
                by_crypto[crypto_id]["last_updated"] = record.get_time()

    coins: List[CoinSummary] = []
    for data in by_crypto.values():
        price = data.get("price_usd")
        if price is None:
            continue
        coins.append(
            CoinSummary(
                id=data["id"],
                symbol=str(data.get("symbol", "")).upper(),
                name=data.get("name", data["id"]),
                price_usd=float(price),
                market_cap=_safe_float(data.get("market_cap")),
                market_cap_rank=_safe_int(data.get("market_cap_rank")),
                volume_24h=_safe_float(data.get("volume_24h")),
                change_1h=_safe_float(data.get("change_1h")),
                change_24h=_safe_float(data.get("change_24h")),
                change_7d=_safe_float(data.get("change_7d")),
                ath=_safe_float(data.get("ath")),
                ath_change_pct=_safe_float(data.get("ath_change_pct")),
                atl=_safe_float(data.get("atl")),
                atl_change_pct=_safe_float(data.get("atl_change_pct")),
                circulating_supply=_safe_float(data.get("circulating_supply")),
                total_supply=_safe_float(data.get("total_supply")),
                max_supply=_safe_float(data.get("max_supply")),
                last_updated=data["last_updated"],
                sparkline_7d=None,
            )
        )

    # Sorting
    order_map = {
        "market_cap_desc": (lambda c: (c.market_cap or 0), True),
        "market_cap_asc": (lambda c: (c.market_cap or 0), False),
        "price_desc": (lambda c: (c.price_usd or 0), True),
        "price_asc": (lambda c: (c.price_usd or 0), False),
        "volume_desc": (lambda c: (c.volume_24h or 0), True),
        "volume_asc": (lambda c: (c.volume_24h or 0), False),
    }
    key_fn, reverse = order_map.get(order, order_map["market_cap_desc"])
    coins.sort(key=key_fn, reverse=reverse)
    return coins


def list_coins(limit: int = 50, page: int = 1, order: str = "market_cap_desc", ids: Optional[List[str]] = None) -> List[CoinSummary]:
    coins = _query_last_snapshot(filter_ids=ids, order=order)
    start = (page - 1) * limit
    end = start + limit
    return coins[start:end]


def get_coin_detail(crypto_id: str) -> Optional[CoinSummary]:
    """Return the latest snapshot for a given crypto_id or None if not found."""
    flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
  |> filter(fn: (r) => r.crypto_id == "{crypto_id}")
  |> filter(fn: (r) =>
      r._field == "price_usd" or
      r._field == "market_cap" or
      r._field == "market_cap_rank" or
      r._field == "volume_24h" or
      r._field == "change_1h" or
      r._field == "change_24h" or
      r._field == "change_7d" or
      r._field == "ath" or
      r._field == "ath_change_pct" or
      r._field == "atl" or
      r._field == "atl_change_pct" or
      r._field == "circulating_supply" or
      r._field == "total_supply" or
      r._field == "max_supply"
  )
  |> group(columns: ["crypto_id", "symbol", "name", "_field"])
  |> last()
"""
    tables = get_query_api().query(org=settings.influx_org, query=flux)
    data: Dict[str, Any] = {}
    last_ts: Optional[datetime] = None
    symbol = None
    name = None
    for table in tables:
        for record in table.records:
            symbol = symbol or record["symbol"]
            name = name or record["name"]
            field = record["_field"]
            data[field] = record.get_value()
            t = record.get_time()
            last_ts = t if (last_ts is None or t > last_ts) else last_ts
    if not data or "price_usd" not in data:
        return None
    return CoinSummary(
        id=crypto_id,
        symbol=str(symbol or crypto_id[:3]).upper(),
        name=name or crypto_id,
        price_usd=float(data.get("price_usd", 0.0)),
        market_cap=_safe_float(data.get("market_cap")),
        market_cap_rank=_safe_int(data.get("market_cap_rank")),
        volume_24h=_safe_float(data.get("volume_24h")),
        change_1h=_safe_float(data.get("change_1h")),
        change_24h=_safe_float(data.get("change_24h")),
        change_7d=_safe_float(data.get("change_7d")),
        ath=_safe_float(data.get("ath")),
        ath_change_pct=_safe_float(data.get("ath_change_pct")),
        atl=_safe_float(data.get("atl")),
        atl_change_pct=_safe_float(data.get("atl_change_pct")),
        circulating_supply=_safe_float(data.get("circulating_supply")),
        total_supply=_safe_float(data.get("total_supply")),
        max_supply=_safe_float(data.get("max_supply")),
        last_updated=last_ts or datetime.utcnow(),
        sparkline_7d=None,
    )


def get_coin_history(crypto_id: str, days: int = 7, interval: str = "1h") -> CoinHistoryResponse:
    """Return time series of price_usd for a crypto with given window and interval."""
    # Basic guardrails
    if days <= 0:
        days = 1
    allowed = {"1m","5m","15m","30m","1h","2h","4h","12h","1d"}
    if interval not in allowed:
        interval = "1h"

    flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r._measurement == "{settings.influx_measurement}")
  |> filter(fn: (r) => r._field == "price_usd")
  |> filter(fn: (r) => r.crypto_id == "{crypto_id}")
  |> aggregateWindow(every: {interval}, fn: last, createEmpty: false)
  |> keep(columns: ["_time", "_value"]) 
"""
    tables = get_query_api().query(org=settings.influx_org, query=flux)
    points: List[PricePoint] = []
    for table in tables:
        for record in table.records:
            points.append(PricePoint(time=record.get_time(), value=float(record.get_value())))
    # Ensure ascending order by time
    points.sort(key=lambda p: p.time)
    return CoinHistoryResponse(id=crypto_id, days=days, interval=interval, series=points)


def _safe_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _safe_int(v):
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None
