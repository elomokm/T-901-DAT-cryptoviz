from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import API_TITLE, API_VERSION, API_DESCRIPTION
from app.influx_client import InfluxClientManager
from app.models import HealthResponse
from app.routers import coins, global_stats, news, fear_greed, analytics, bootstrap

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

# Add CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers under a common API prefix
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(bootstrap.router)
api_v1.include_router(coins.router)
api_v1.include_router(global_stats.router)
api_v1.include_router(news.router)
api_v1.include_router(fear_greed.router)
api_v1.include_router(analytics.router)
app.include_router(api_v1)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Close InfluxDB connection on shutdown."""
    InfluxClientManager.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
