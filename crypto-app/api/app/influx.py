from influxdb_client import InfluxDBClient
from .config import settings

_client = None

def get_client() -> InfluxDBClient:
    global _client
    if _client is None:
        _client = InfluxDBClient(url=settings.influx_url, token=settings.influx_token, org=settings.influx_org, timeout=30000)
    return _client
