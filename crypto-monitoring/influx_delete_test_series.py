#!/usr/bin/env python3
"""
Delete all time-series in InfluxDB (bucket/org from env) where:
  _measurement == "crypto_price" AND crypto =~ /^test_/

Usage:
  python3 influx_delete_test_series.py            # asks for confirmation
  SKIP_CONFIRM=1 python3 influx_delete_test_series.py  # no prompt

Env (defaults for local dev):
  INFLUX_URL=http://localhost:8086
  INFLUX_TOKEN=Y_Fn0YsUAnSnyikigehkC6WzFWa4shZkVwhM0U5KKbtb43E1y_A6QpyzKv-VYgPcYHLZctOeegOsDYmFGaYkQQ==
  INFLUX_ORG=crypto-org
  INFLUX_BUCKET=crypto-data
"""
import os
import sys
from datetime import datetime
from influxdb_client import InfluxDBClient

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "Y_Fn0YsUAnSnyikigehkC6WzFWa4shZkVwhM0U5KKbtb43E1y_A6QpyzKv-VYgPcYHLZctOeegOsDYmFGaYkQQ==")
INFLUX_ORG = os.getenv("INFLUX_ORG", "crypto-org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "crypto-data")

PREDICATE = '_measurement="crypto_price" AND crypto=~/^test_/'
START = "1970-01-01T00:00:00Z"
STOP = "2100-01-01T00:00:00Z"

def main():
    print("Influx delete config:")
    print(f"  url={INFLUX_URL}")
    print(f"  org={INFLUX_ORG}")
    print(f"  bucket={INFLUX_BUCKET}")
    print(f"  predicate={PREDICATE}")
    print(f"  time range: {START} .. {STOP}")

    if os.getenv("SKIP_CONFIRM") not in ("1", "true", "True"):
        ans = input("Confirm deletion of matching series? (yes/NO) ").strip().lower()
        if ans != "yes":
            print("Aborted.")
            return 1

    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        delete_api = client.delete_api()
        try:
            delete_api.delete(
                start=START,
                stop=STOP,
                predicate=PREDICATE,
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
            )
            print("Delete request submitted successfully.")
        except Exception as e:
            print(f"Delete failed: {e}")
            return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
