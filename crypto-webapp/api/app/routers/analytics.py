"""
Router pour les analytics et comparaisons de cryptos
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.models import CryptoAnalytics, ComparisonResult
from app.influx_client import get_query_api

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/", response_model=List[CryptoAnalytics])
async def get_analytics(
    crypto_ids: Optional[str] = Query(None, description="Comma-separated crypto IDs"),
    limit: int = Query(50, le=200, description="Number of records per crypto")
):
    """
    Récupère les analytics pour les cryptos spécifiées.
    Si aucun crypto_id n'est fourni, retourne les analytics pour toutes les cryptos.
    """
    query_api = get_query_api()
    
    # Construire le filtre pour les crypto_ids
    crypto_filter = ""
    if crypto_ids:
        ids_list = [f'"{id.strip()}"' for id in crypto_ids.split(',')]
        crypto_filter = f'|> filter(fn: (r) => r["crypto_id"] == {" or r[crypto_id] == ".join(ids_list)})'
    
    query = f'''
        from(bucket: "crypto-data")
            |> range(start: -7d)
            |> filter(fn: (r) => r["_measurement"] == "crypto_analytics")
            {crypto_filter}
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: {limit})
    '''
    
    try:
        tables = query_api.query(query)
        
        analytics_list = []
        for table in tables:
            for record in table.records:
                analytics = CryptoAnalytics(
                    crypto_id=record.values.get("crypto_id", ""),
                    symbol=record.values.get("symbol", ""),
                    name=record.values.get("name", ""),
                    price_mean=record.values.get("price_mean", 0),
                    price_std=record.values.get("price_std", 0),
                    price_min=record.values.get("price_min", 0),
                    price_max=record.values.get("price_max", 0),
                    price_range=record.values.get("price_range", 0),
                    volatility_pct=record.values.get("volatility_pct", 0),
                    volume_mean=record.values.get("volume_mean", 0),
                    volume_std=record.values.get("volume_std", 0),
                    anomaly_count=int(record.values.get("anomaly_count", 0)),
                    data_points=int(record.values.get("data_points", 0)),
                    timestamp=record.get_time()
                )
                analytics_list.append(analytics)
        
        return analytics_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")


@router.get("/compare", response_model=ComparisonResult)
async def compare_cryptos(
    crypto_ids: str = Query(..., description="Comma-separated crypto IDs to compare (2-10 cryptos)"),
    period: str = Query("24h", description="Time period: 1h, 24h, 7d, 30d")
):
    """
    Compare plusieurs cryptos sur différents critères analytiques.
    Retourne les dernières analytics pour chaque crypto + données de comparaison.
    """
    query_api = get_query_api()
    
    # Valider et parser les crypto_ids
    ids_list = [id.strip() for id in crypto_ids.split(',') if id.strip()]
    if len(ids_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 crypto IDs required for comparison")
    if len(ids_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 cryptos for comparison")
    
    # Mapper le period à une durée InfluxDB
    period_map = {
        "1h": "-1h",
        "24h": "-24h",
        "7d": "-7d",
        "30d": "-30d"
    }
    time_range = period_map.get(period, "-24h")
    
    # Construire le filtre pour les crypto_ids
    crypto_filter_parts = [f'r["crypto_id"] == "{id}"' for id in ids_list]
    crypto_filter = " or ".join(crypto_filter_parts)
    
    query = f'''
        from(bucket: "crypto-data")
            |> range(start: {time_range})
            |> filter(fn: (r) => r["_measurement"] == "crypto_analytics")
            |> filter(fn: (r) => {crypto_filter})
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> group(columns: ["crypto_id"])
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: 1)
    '''
    
    try:
        tables = query_api.query(query)
        
        cryptos_data = []
        for table in tables:
            for record in table.records:
                crypto_analytics = {
                    "crypto_id": record.values.get("crypto_id", ""),
                    "symbol": record.values.get("symbol", ""),
                    "name": record.values.get("name", ""),
                    "price_mean": record.values.get("price_mean", 0),
                    "price_std": record.values.get("price_std", 0),
                    "price_min": record.values.get("price_min", 0),
                    "price_max": record.values.get("price_max", 0),
                    "price_range": record.values.get("price_range", 0),
                    "volatility_pct": record.values.get("volatility_pct", 0),
                    "volume_mean": record.values.get("volume_mean", 0),
                    "volume_std": record.values.get("volume_std", 0),
                    "anomaly_count": int(record.values.get("anomaly_count", 0)),
                    "data_points": int(record.values.get("data_points", 0)),
                    "timestamp": record.get_time().isoformat() if record.get_time() else None
                }
                cryptos_data.append(crypto_analytics)
        
        if not cryptos_data:
            raise HTTPException(status_code=404, detail="No analytics data found for specified cryptos")
        
        # Calculer les rankings
        sorted_by_volatility = sorted(cryptos_data, key=lambda x: x["volatility_pct"], reverse=True)
        sorted_by_volume = sorted(cryptos_data, key=lambda x: x["volume_mean"], reverse=True)
        sorted_by_price = sorted(cryptos_data, key=lambda x: x["price_mean"], reverse=True)
        
        return ComparisonResult(
            cryptos=cryptos_data,
            period=period,
            comparison_time=datetime.utcnow().isoformat(),
            rankings={
                "most_volatile": [c["crypto_id"] for c in sorted_by_volatility],
                "highest_volume": [c["crypto_id"] for c in sorted_by_volume],
                "highest_price": [c["crypto_id"] for c in sorted_by_price]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing cryptos: {str(e)}")


@router.get("/top-volatile", response_model=List[CryptoAnalytics])
async def get_top_volatile(limit: int = Query(10, le=50)):
    """Retourne les cryptos les plus volatiles"""
    query_api = get_query_api()
    
    query = f'''
        from(bucket: "crypto-data")
            |> range(start: -24h)
            |> filter(fn: (r) => r["_measurement"] == "crypto_analytics")
            |> filter(fn: (r) => r["_field"] == "volatility_pct")
            |> group(columns: ["crypto_id"])
            |> last()
            |> group()
            |> sort(columns: ["_value"], desc: true)
            |> limit(n: {limit})
    '''
    
    try:
        tables = query_api.query(query)
        volatile_ids = [record.values.get("crypto_id") for table in tables for record in table.records]
        
        if not volatile_ids:
            return []
        
        # Récupérer les analytics complets pour ces cryptos
        return await get_analytics(crypto_ids=",".join(volatile_ids), limit=1)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching volatile cryptos: {str(e)}")
