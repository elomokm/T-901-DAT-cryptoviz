# CryptoViz

## Objectif
CryptoViz est une application temps réel qui a pour but de :
1. **Collecter** en continu des actualités et des données de marché liées aux cryptomonnaies.
2. **Analyser** ces données pour extraire des métriques utiles (volume, sources, sentiment, prix, variations).
3. **Visualiser** dynamiquement les résultats, avec une dimension temporelle.

---

## Architecture cible

### Composants principaux
- **Scraper (Producer)**  
  Le Scraper n’est pas limité aux news. J’ai choisi de créer deux producteurs Kafka :
  - un qui alimente les données d’actualités crypto (flux RSS),  
  - un autre qui alimente les données de marché (API CoinGecko).  

  Cela me permet de traiter séparément les deux flux, puis de les corréler dans l’Analytics Builder. 

- **Analytics Builder (Consumer)**  
  - Consomme les messages depuis Kafka.  
  - Nettoie, normalise et enrichit les données (ex : score de sentiment pour les news, variation pour les prix).  
  - Stocke les résultats dans **PostgreSQL**.  
  - Expose une API (FastAPI) pour interroger les données.  

- **Viewer (Frontend)**  
  - Application React affichant des graphiques dynamiques (ex: volume de news dans le temps, top sources, évolution du prix du BTC).  
  - Se connecte à l’API analytics.

### Schéma simplifié
[Sources RSS] → [Scraper News] ┐

│→ [Kafka] → [Analytics Worker FastAPI] → [PostgreSQL] → [React Viewer]

│
[API CoinGecko] → [Scraper Marché] ┘


# CryptoViz - Market Pipeline (MVP)

## Setup
cp .env.example .env

## Run
docker compose up --build

Services:
- Postgres: 5432 (Adminer http://localhost:8080)
- Kafka: 9092 (Kafka UI http://localhost:8085)
- Scraper Binance -> market.raw.trade.binance
- Normalizer -> market.normalized.trade
- Spark Aggregator (1m) -> market.agg.ohlcv.1m
- Writer Timeseries -> Postgres.candles_1m

## Vérifications
- Kafka UI: messages sur les topics
- Adminer: table candles_1m se remplit
