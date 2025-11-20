from influxdb_client import InfluxDBClient
from .config import settings
from .influx import get_client

# Expose a query_api convenience

def get_query_api():
    client: InfluxDBClient = get_client()
    return client.query_api()
