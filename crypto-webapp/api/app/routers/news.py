from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.influx_client import get_query_api, get_bucket
from app.models import NewsArticle, NewsSource

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=list[NewsArticle])
async def get_news(
    limit: int = Query(default=20, ge=1, le=100),
    source: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168)
):
    """Get news articles."""
    query_api = get_query_api()
    bucket = get_bucket()

    try:
        # Build query with optional source filter
        source_filter = ""
        if source:
            source_filter = f'|> filter(fn: (r) => r.source == "{source}")'

        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r._measurement == "crypto_news")
            {source_filter}
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: {limit})
        '''

        tables = query_api.query(query)

        news = []
        for table in tables:
            for record in table.records:
                article = NewsArticle(
                    title=str(record.values.get("title", "")),
                    link=str(record.values.get("link", "")),
                    published_date=record.values.get("published_date") or record.get_time(),
                    source=str(record.values.get("source", "unknown")),
                    description=record.values.get("description")
                )
                news.append(article)

        return news

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")


@router.get("/sources", response_model=list[NewsSource])
async def get_news_sources():
    """Get available news sources with article counts."""
    query_api = get_query_api()
    bucket = get_bucket()

    try:
        query = f'''
        from(bucket: "{bucket}")
            |> range(start: -7d)
            |> filter(fn: (r) => r._measurement == "crypto_news")
            |> filter(fn: (r) => r._field == "title")
            |> group(columns: ["source"])
            |> count()
        '''

        tables = query_api.query(query)

        sources = []
        for table in tables:
            for record in table.records:
                source_name = record.values.get("source", "unknown")
                count = int(record.get_value())
                sources.append(NewsSource(name=source_name, count=count))

        # Sort by count descending
        sources.sort(key=lambda x: x.count, reverse=True)

        return sources

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying InfluxDB: {str(e)}")
