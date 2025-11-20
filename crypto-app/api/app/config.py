from pydantic import BaseModel
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; env vars can still be provided by shell/docker
    pass

class Settings(BaseModel):
    influx_url: str = os.getenv("INFLUX_URL", "http://localhost:8086")
    influx_org: str = os.getenv("INFLUX_ORG", "crypto-org")
    influx_bucket: str = os.getenv("INFLUX_BUCKET", "crypto-data")
    influx_measurement: str = os.getenv("INFLUX_MEASUREMENT", "crypto_market")
    influx_token: str = os.getenv("INFLUX_TOKEN", "")
    # Allow Next.js dev servers by default
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
    # Snapshot lookback window for latest coin data (minutes)
    snapshot_minutes_back: int = int(os.getenv("SNAPSHOT_MINUTES_BACK", "60"))
    # Top 11 cryptos : BTC, ETH, BNB, XRP, DOGE, SOL, MATIC, LINK, AVAX, ADA, DOT
    default_cryptos: str = os.getenv(
        "DEFAULT_CRYPTOS",
        "bitcoin,ethereum,binancecoin,ripple,dogecoin,solana,polygon,chainlink,avalanche,cardano,polkadot"
    )

settings = Settings()
