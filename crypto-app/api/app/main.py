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


@app.get("/top-movers")
async def top_movers(limit: int = Query(3, description="Number of gainers/losers to return")) -> Dict[str, Any]:
    """
    Return top gainers and losers based on 24h price change.
    
    Strategy:
    1. Get current price (last 5min)
    2. Get price 24h ago
    3. Calculate % change
    4. Sort and return top gainers + losers
    """
    symbols = DEFAULT_CRYPTOS
    reg = _regex_from_list(symbols)
    
    # Query 1: Current prices (last point)
    flux_current = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -10m)
  |> filter(fn: (r) => r._measurement == "crypto_price")
  |> filter(fn: (r) => r._field == "price_usd")
  |> filter(fn: (r) => r.crypto =~ /{reg}/)
  |> group(columns: ["crypto"])
  |> last()
"""
    
    # Query 2: Prices 24h ago
    flux_24h = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -25h, stop: -23h)
  |> filter(fn: (r) => r._measurement == "crypto_price")
  |> filter(fn: (r) => r._field == "price_usd")
  |> filter(fn: (r) => r.crypto =~ /{reg}/)
  |> group(columns: ["crypto"])
  |> first()
"""
    
    client = get_client()
    
    # Get current prices
    current_prices: Dict[str, float] = {}
    tables_current = client.query_api().query(org=settings.influx_org, query=flux_current)
    for table in tables_current:
        for record in table.records:
            current_prices[str(record["crypto"])] = float(record.get_value())
    
    # Get 24h ago prices
    past_prices: Dict[str, float] = {}
    tables_past = client.query_api().query(org=settings.influx_org, query=flux_24h)
    for table in tables_past:
        for record in table.records:
            past_prices[str(record["crypto"])] = float(record.get_value())
    
    # Calculate % changes
    changes: List[Dict[str, Any]] = []
    for crypto in symbols:
        if crypto in current_prices and crypto in past_prices:
            current = current_prices[crypto]
            past = past_prices[crypto]
            pct_change = ((current - past) / past) * 100
            changes.append({
                "crypto": crypto,
                "current_price": current,
                "price_24h_ago": past,
                "change_24h_pct": round(pct_change, 2)
            })
    
    # Sort by change %
    changes_sorted = sorted(changes, key=lambda x: x["change_24h_pct"], reverse=True)
    
    # Top gainers (positive changes)
    gainers = [c for c in changes_sorted if c["change_24h_pct"] > 0][:limit]
    
    # Top losers (negative changes)
    losers = [c for c in changes_sorted if c["change_24h_pct"] < 0][-limit:]
    losers.reverse()  # Show worst first
    
    return {
        "gainers": gainers,
        "losers": losers,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/top-movers/mock")
async def top_movers_mock(limit: int = Query(3, description="Number of gainers/losers")) -> Dict[str, Any]:
    """
    Mock endpoint with realistic data for frontend development.
    Returns fake but realistic top gainers/losers.
    """
    import random
    
    # Base prices approximatifs (Nov 2025)
    base_prices = {
        "bitcoin": 42000,
        "ethereum": 2800,
        "binancecoin": 310,
        "ripple": 0.65,
        "dogecoin": 0.085,
        "solana": 95,
        "polygon": 0.78,
        "chainlink": 14.5,
        "avalanche": 22,
        "cardano": 0.42,
        "polkadot": 6.8
    }
    
    # Generate realistic 24h changes (-15% to +20%)
    all_movers = []
    for crypto, base_price in base_prices.items():
        change_pct = random.uniform(-15, 20)
        current_price = base_price * (1 + change_pct / 100)
        price_24h_ago = base_price
        
        all_movers.append({
            "crypto": crypto,
            "current_price": round(current_price, 8 if current_price < 1 else 2),
            "price_24h_ago": round(price_24h_ago, 8 if price_24h_ago < 1 else 2),
            "change_24h_pct": round(change_pct, 2)
        })
    
    # Sort by change
    sorted_movers = sorted(all_movers, key=lambda x: x["change_24h_pct"], reverse=True)
    
    gainers = [m for m in sorted_movers if m["change_24h_pct"] > 0][:limit]
    losers = [m for m in sorted_movers if m["change_24h_pct"] < 0][-limit:]
    losers.reverse()
    
    return {
        "gainers": gainers,
        "losers": losers,
        "timestamp": datetime.now().isoformat(),
        "is_mock": True
    }


@app.get("/crypto-list")
async def crypto_list() -> Dict[str, Any]:
    """
    Return full crypto list with current data for table display.
    Mock version with realistic data.
    """
    import random
    
    cryptos_data = [
        {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "base_price": 42000},
        {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "base_price": 2800},
        {"id": "binancecoin", "symbol": "BNB", "name": "BNB", "base_price": 310},
        {"id": "ripple", "symbol": "XRP", "name": "XRP", "base_price": 0.65},
        {"id": "dogecoin", "symbol": "DOGE", "name": "Dogecoin", "base_price": 0.085},
        {"id": "solana", "symbol": "SOL", "name": "Solana", "base_price": 95},
        {"id": "polygon", "symbol": "MATIC", "name": "Polygon", "base_price": 0.78},
        {"id": "chainlink", "symbol": "LINK", "name": "Chainlink", "base_price": 14.5},
        {"id": "avalanche", "symbol": "AVAX", "name": "Avalanche", "base_price": 22},
        {"id": "cardano", "symbol": "ADA", "name": "Cardano", "base_price": 0.42},
        {"id": "polkadot", "symbol": "DOT", "name": "Polkadot", "base_price": 6.8}
    ]
    
    result = []
    for idx, crypto in enumerate(cryptos_data, 1):
        change_24h = random.uniform(-15, 20)
        change_7d = random.uniform(-25, 35)
        current_price = crypto["base_price"] * (1 + change_24h / 100)
        volume_24h = current_price * random.uniform(1e9, 50e9)
        market_cap = current_price * random.uniform(1e9, 800e9)
        
        result.append({
            "rank": idx,
            "id": crypto["id"],
            "symbol": crypto["symbol"],
            "name": crypto["name"],
            "price": round(current_price, 8 if current_price < 1 else 2),
            "change_24h": round(change_24h, 2),
            "change_7d": round(change_7d, 2),
            "volume_24h": round(volume_24h, 0),
            "market_cap": round(market_cap, 0)
        })
    
    # Sort by market cap (rank)
    result.sort(key=lambda x: x["market_cap"], reverse=True)
    for idx, item in enumerate(result, 1):
        item["rank"] = idx
    
    return {
        "data": result,
        "timestamp": datetime.now().isoformat(),
        "is_mock": True
    }
