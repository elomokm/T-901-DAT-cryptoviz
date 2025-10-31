from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from datetime import datetime

from .config import settings
from .influx import get_client

app = FastAPI(title="Crypto API", version="0.1.0")

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_CRYPTOS = [c.strip() for c in settings.default_cryptos.split(",") if c.strip()]

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


def _regex_from_list(items: List[str]) -> str:
    escaped = [i.replace("/", "\/") for i in items]
    return f"^({'|'.join(escaped)})$"


@app.get("/overview/market-cap")
async def overview_market_cap(cryptos: str | None = Query(None, description="Comma-separated list of cryptos")) -> Dict[str, Any]:
    """Return latest market cap per crypto and total sum."""
    symbols = [c.strip() for c in (cryptos.split(",") if cryptos else DEFAULT_CRYPTOS) if c.strip()]
    reg = _regex_from_list(symbols)

    flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "crypto_price")
  |> filter(fn: (r) => r._field == "market_cap")
  |> filter(fn: (r) => r.crypto =~ /{reg}/)
  |> aggregateWindow(every: 5m, fn: last, createEmpty: false)
  |> group(columns: ["crypto"]) 
  |> last()
"""
    client = get_client()
    tables = client.query_api().query(org=settings.influx_org, query=flux)

    per_crypto: Dict[str, float] = {}
    ts: datetime | None = None
    for table in tables:
        for record in table.records:
            per_crypto[str(record["crypto"])] = float(record.get_value())
            ts = record.get_time()

    total = sum(per_crypto.values())
    return {"timestamp": ts.isoformat() if ts else None, "total_market_cap": total, "per_crypto": per_crypto, "cryptos": symbols}


@app.get("/overview/prices")
async def overview_prices(
    cryptos: str | None = Query(None, description="Comma-separated list of cryptos"),
    range: str = Query("24h", description="Range like 24h, 7d, 30d"),
    interval: str = Query("5m", description="Aggregate window, e.g., 1m,5m,1h")
) -> Dict[str, Any]:
    symbols = [c.strip() for c in (cryptos.split(",") if cryptos else DEFAULT_CRYPTOS) if c.strip()]
    reg = _regex_from_list(symbols)

    flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -{range})
  |> filter(fn: (r) => r._measurement == "crypto_price")
  |> filter(fn: (r) => r._field == "price_usd")
  |> filter(fn: (r) => r.crypto =~ /{reg}/)
  |> aggregateWindow(every: {interval}, fn: last, createEmpty: false)
  |> keep(columns: ["_time", "_value", "crypto"]) 
"""
    client = get_client()
    tables = client.query_api().query(org=settings.influx_org, query=flux)

    series: Dict[str, List[Dict[str, Any]]] = {s: [] for s in symbols}
    for table in tables:
        crypto = None
        if len(table.records) > 0:
            crypto = table.records[0]["crypto"]
        for record in table.records:
            c = str(record["crypto"]) if record["crypto"] else str(crypto)
            series.setdefault(c, []).append({
                "time": record.get_time().isoformat(),
                "value": float(record.get_value())
            })

    return {"cryptos": symbols, "series": series}
