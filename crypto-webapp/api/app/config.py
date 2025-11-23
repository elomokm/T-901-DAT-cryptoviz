import os
from dotenv import load_dotenv

load_dotenv()

# InfluxDB Configuration
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "crypto_org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "crypto_data")

# API Configuration
API_TITLE = "Crypto Webapp API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "API for cryptocurrency data visualization"
