#!/usr/bin/env python3
"""
Script de vérification des données dans InfluxDB.
Vérifie que les données des deux producteurs (CoinGecko et CoinMarketCap) sont présentes.
"""
import os
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

# Charger .env
load_dotenv()

# Config InfluxDB
INFLUX_URL = os.getenv('INFLUX_URL', 'http://localhost:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET')

def main():
    print("=" * 70)
    print(" VÉRIFICATION DES DONNÉES INFLUXDB")
    print("=" * 70)
    print(f"\nURL: {INFLUX_URL}")
    print(f"Org: {INFLUX_ORG}")
    print(f"Bucket: {INFLUX_BUCKET}")
    print(f"Token: {INFLUX_TOKEN[:10]}..." if INFLUX_TOKEN else "Token: MANQUANT")
    print()
    
    if not all([INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET]):
        print("❌ Configuration InfluxDB incomplète. Vérifiez votre .env")
        return
    
    # Connexion
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    
    print("🔍 Vérification 1: Nombre total de points dans le bucket")
    print("-" * 70)
    
    query_total = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "crypto_market")
      |> count()
    '''
    
    try:
        result = query_api.query(query_total)
        total_points = 0
        for table in result:
            for record in table.records:
                total_points += record.get_value()
        print(f"✅ Total de points (dernière heure): {total_points}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n🔍 Vérification 2: Données par source (coingecko vs coinmarketcap)")
    print("-" * 70)
    
    # Vérifier CoinGecko
    query_coingecko = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "crypto_market")
      |> filter(fn: (r) => r.source == "coingecko")
      |> filter(fn: (r) => r._field == "price_usd")
      |> last()
      |> group(columns: ["symbol"])
    '''
    
    try:
        result = query_api.query(query_coingecko)
        print("\n📊 CoinGecko (derniers prix):")
        coingecko_count = 0
        for table in result:
            for record in table.records:
                symbol = record.values.get('symbol', 'N/A')
                price = record.get_value()
                time = record.get_time()
                coingecko_count += 1
                print(f"  {symbol:6} | Prix: ${price:,.2f} | Time: {time}")
        
        if coingecko_count == 0:
            print("  ⚠️  Aucune donnée CoinGecko trouvée")
        else:
            print(f"\n  ✅ {coingecko_count} cryptos CoinGecko")
    except Exception as e:
        print(f"  ❌ Erreur CoinGecko: {e}")
    
    # Vérifier CoinMarketCap
    query_cmc = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "crypto_market")
      |> filter(fn: (r) => r.source == "coinmarketcap")
      |> filter(fn: (r) => r._field == "price_usd")
      |> last()
      |> group(columns: ["symbol"])
    '''
    
    try:
        result = query_api.query(query_cmc)
        print("\n📊 CoinMarketCap (derniers prix):")
        cmc_count = 0
        for table in result:
            for record in table.records:
                symbol = record.values.get('symbol', 'N/A')
                price = record.get_value()
                time = record.get_time()
                cmc_count += 1
                print(f"  {symbol:6} | Prix: ${price:,.2f} | Time: {time}")
        
        if cmc_count == 0:
            print("  ⚠️  Aucune donnée CoinMarketCap trouvée")
        else:
            print(f"\n  ✅ {cmc_count} cryptos CoinMarketCap")
    except Exception as e:
        print(f"  ❌ Erreur CoinMarketCap: {e}")
    
    print("\n🔍 Vérification 3: Liste des tags 'source' présents")
    print("-" * 70)
    
    query_sources = f'''
    import "influxdata/influxdb/schema"
    
    schema.tagValues(
      bucket: "{INFLUX_BUCKET}",
      tag: "source",
      predicate: (r) => r._measurement == "crypto_market",
      start: -1h
    )
    '''
    
    try:
        result = query_api.query(query_sources)
        sources = []
        for table in result:
            for record in table.records:
                sources.append(record.get_value())
        
        if sources:
            print(f"Sources détectées: {', '.join(sources)}")
        else:
            print("⚠️  Aucune source détectée")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n🔍 Vérification 4: Exemple de point complet (tous les champs)")
    print("-" * 70)
    
    query_sample = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "crypto_market")
      |> filter(fn: (r) => r.symbol == "BTC")
      |> last()
    '''
    
    try:
        result = query_api.query(query_sample)
        print("\nDernière donnée pour BTC:")
        fields_found = {}
        tags_found = {}
        
        for table in result:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                fields_found[field] = value
                
                # Collecter les tags
                for key in ['source', 'symbol', 'crypto_id', 'name']:
                    if key in record.values:
                        tags_found[key] = record.values[key]
        
        print("\nTags:")
        for tag, value in tags_found.items():
            print(f"  {tag}: {value}")
        
        print("\nFields:")
        for field, value in sorted(fields_found.items()):
            if isinstance(value, float):
                print(f"  {field}: {value:,.2f}")
            else:
                print(f"  {field}: {value}")
        
        if not fields_found:
            print("  ⚠️  Aucun field trouvé pour BTC")
        else:
            # Vérifier les champs critiques
            critical_fields = ['price_usd', 'market_cap', 'volume_24h']
            missing = [f for f in critical_fields if f not in fields_found]
            if missing:
                print(f"\n⚠️  Champs manquants: {', '.join(missing)}")
            else:
                print(f"\n✅ Tous les champs critiques présents")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print(" FIN DE LA VÉRIFICATION")
    print("=" * 70)
    
    client.close()

if __name__ == "__main__":
    main()
