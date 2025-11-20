from fastapi import APIRouter, HTTPException
from app.influx_client import get_query_api, get_bucket
from app.models import FearGreedIndex

router = APIRouter(tags=["fear-greed"])


def classify_fear_greed(value: int) -> str:
    """Classify fear and greed index value."""
    if value <= 25:
        return "Extreme Fear"
    elif value <= 45:
        return "Fear"
    elif value <= 55:
        return "Neutral"
    elif value <= 75:
        return "Greed"
    else:
        return "Extreme Greed"


@router.get("/fear-greed", response_model=FearGreedIndex)
async def get_fear_greed():
    """Get the latest fear and greed index."""
    query_api = get_query_api()
    bucket = get_bucket()

    try:
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "fear_greed_index")
            |> filter(fn: (r) => r._field == "value")
            |> last()
        '''

        tables = query_api.query(query)

        for table in tables:
            for record in table.records:
                value = int(record.get_value())
                return FearGreedIndex(
                    value=value,
                    classification=classify_fear_greed(value),
                    timestamp=record.get_time()
                )

        raise HTTPException(status_code=404, detail="Fear and Greed index not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")
