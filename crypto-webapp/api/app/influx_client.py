from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from app.config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET


class InfluxClientManager:
    _client: InfluxDBClient | None = None
    _query_api: QueryApi | None = None

    @classmethod
    def get_client(cls) -> InfluxDBClient:
        if cls._client is None:
            cls._client = InfluxDBClient(
                url=INFLUX_URL,
                token=INFLUX_TOKEN,
                org=INFLUX_ORG
            )
        return cls._client

    @classmethod
    def get_query_api(cls) -> QueryApi:
        if cls._query_api is None:
            cls._query_api = cls.get_client().query_api()
        return cls._query_api

    @classmethod
    def close(cls):
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._query_api = None


def get_query_api() -> QueryApi:
    return InfluxClientManager.get_query_api()


def get_bucket() -> str:
    return INFLUX_BUCKET


def get_org() -> str:
    return INFLUX_ORG
