"""
Service pour récupérer les actualités crypto depuis InfluxDB
"""
from typing import List, Optional
from datetime import datetime, timedelta
from app.influx import get_client
from app.config import settings
from app.models import NewsArticle


async def get_latest_news(
    limit: int = 20,
    source: Optional[str] = None,
    hours: int = 24
) -> List[NewsArticle]:
    """
    Récupère les dernières actualités crypto depuis InfluxDB.

    Args:
        limit: Nombre maximum d'articles à retourner
        source: Filtrer par source (coindesk, cointelegraph) - optionnel
        hours: Articles des X dernières heures

    Returns:
        Liste d'articles de news
    """
    client = get_client()
    query_api = client.query_api()

    # Calculer la période
    start_time = datetime.utcnow() - timedelta(hours=hours)
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Construire le filtre de source
    source_filter = f'|> filter(fn: (r) => r.source == "{source}")' if source else ''

    # Requête Flux pour récupérer les news
    query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: {start_time_str})
      |> filter(fn: (r) => r._measurement == "crypto_news")
      {source_filter}
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: {limit})
    '''

    try:
        result = query_api.query(query, org=settings.influx_org)

        news_list = []
        for table in result:
            for record in table.records:
                article = NewsArticle(
                    title=record.values.get('title', 'No Title'),
                    link=record.values.get('link', ''),
                    published_date=record.get_time().isoformat() if record.get_time() else datetime.utcnow().isoformat(),
                    source=record.values.get('source', 'unknown'),
                    description=record.values.get('description', ''),
                    image_url=record.values.get('image_url')
                )
                news_list.append(article)

        return news_list

    except Exception as e:
        print(f"Error querying news from InfluxDB: {e}")
        return []
