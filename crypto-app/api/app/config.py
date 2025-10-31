from pydantic import BaseModel
import os

class Settings(BaseModel):
    influx_url: str = os.getenv("INFLUX_URL", "http://localhost:8086")
    influx_org: str = os.getenv("INFLUX_ORG", "crypto-org")
    influx_bucket: str = os.getenv("INFLUX_BUCKET", "crypto-data")
    influx_token: str = os.getenv("INFLUX_TOKEN", "")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3001")
    default_cryptos: str = os.getenv("DEFAULT_CRYPTOS", "bitcoin,cardano,ethereum,polkadot,solana")

settings = Settings()
