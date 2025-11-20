from typing import Optional
from datetime import datetime

from ..config import settings
from ..influx_client import get_query_api

class FearGreedData(dict):
    # simple dict-based payload to avoid new Pydantic model
    pass


def get_latest_fear_greed() -> Optional[FearGreedData]:
    """Try to read last fear & greed index from possible measurements/fields.
    Returns None if nothing found.
    """
    candidates = [
        {"measurement": "fear_greed", "fields": ["value", "index"]},
        {"measurement": "fear_greed_index", "fields": ["value", "index"]},
    ]

    for c in candidates:
        fields_filter = " or ".join([f'r._field == "{f}"' for f in c["fields"]])
        flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "{c['measurement']}")
  |> filter(fn: (r) => {fields_filter})
  |> group()
  |> last()
"""
        tables = get_query_api().query(org=settings.influx_org, query=flux)
        best_time: Optional[datetime] = None
        value: Optional[float] = None
        source = None
        for table in tables:
            for r in table.records:
                v = r.get_value()
                t = r.get_time()
                if v is None:
                    continue
                if best_time is None or t > best_time:
                    best_time = t
                    try:
                        value = float(v)
                    except Exception:
                        value = None
                    source = r.values.get("source")
        if best_time is not None and value is not None:
            return FearGreedData({
                "value": value,
                "time": best_time.isoformat(),
                "source": source,
                "measurement": c["measurement"],
            })

    return None
