from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import coins as coins_router
from .routers import global_stats as global_stats_router
from .influx import get_client
from .influx_client import get_query_api
from influxdb_client.rest import ApiException
from .routers import fear_greed as fear_greed_router
from .routers import debug as debug_router
from .routers import news as news_router

app = FastAPI(title="Crypto API", version="0.2.0")

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/influx")
async def health_influx():
    """Ping Influx and test auth by running a tiny query against the configured bucket."""
    resp = {"url": settings.influx_url}
    try:
        client = get_client()
        resp["ping"] = "ok" if client.ping() else "unreachable"
    except Exception as e:
        resp["ping"] = f"error: {e}"
        return resp

    # Test auth: run a minimal query (may 401 if token invalid/missing)
    try:
        q = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -1m)
  |> limit(n:1)
"""
        _ = get_query_api().query(org=settings.influx_org, query=q)
        resp["auth"] = "ok"
    except ApiException as ae:
        # influxdb_client wraps HTTP status in ApiException
        resp["auth"] = f"unauthorized ({ae.status})" if getattr(ae, 'status', None) == 401 else f"error: {ae}"
    except Exception as e:
        resp["auth"] = f"error: {e}"
    return resp

app.include_router(coins_router.router)
app.include_router(global_stats_router.router)
app.include_router(fear_greed_router.router)
app.include_router(debug_router.router)
app.include_router(news_router.router)