# CryptoViz - Real-Time Cryptocurrency Monitoring Platform

> **Big Data Analytics Platform for Cryptocurrency Market Intelligence**

CryptoViz is a comprehensive big data application designed to continuously collect, process, and visualize cryptocurrency market data in real-time. Built using modern big data technologies, it implements the **Producer/Consumer paradigm** to handle high-velocity data streams from multiple sources.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Components](#components)
- [Data Flow](#data-flow)
- [Analytics](#analytics)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)

---

## 🎯 Overview

CryptoViz addresses the need for **real-time cryptocurrency market intelligence** by providing three core capabilities as required by the project specifications:

### 1. **Online Market Data Feed Collectors** (Web Scrapers)
Continuously collect cryptocurrency data from multiple sources:
- **CoinGecko API**: Price, volume, market cap for 20 major cryptocurrencies
- **CoinMarketCap API**: Professional-grade market data for cross-validation
- **News RSS Feeds**: Real-time crypto news from CoinDesk & CoinTelegraph
- **Sentiment Data**: Fear & Greed Index for market psychology

### 2. **Online Analytics Builder** (Stream Processing)
Process collected data in real-time using Apache Spark Structured Streaming:
- **Price Analytics**: Moving averages, volatility, price ranges
- **Anomaly Detection**: Volume spikes, rapid price changes, source divergence
- **Sentiment Analysis**: News sentiment classification (positive/negative/neutral)
- **Cross-Validation**: Detect price discrepancies between data sources

### 3. **Dynamic Viewer** (Visualization)
Visualize analytics with temporal dimensions through:
- **Next.js Web Application**: Modern, responsive cryptocurrency dashboard
- **Grafana Dashboards**: Real-time operational metrics and comparisons
- **Temporal Analysis**: Historical charts, trend analysis, time-series exploration

---

## 🏗️ Architecture

CryptoViz implements a **Lambda Architecture** for big data processing, combining real-time stream processing with batch analytics.

```
┌──────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                              │
│  CoinGecko │ CoinMarketCap │ News RSS │ Fear & Greed        │
└──────┬──────────────┬───────────┬───────────┬────────────────┘
       │              │           │           │
       ▼              ▼           ▼           ▼
┌──────────────────────────────────────────────────────────────┐
│          MARKET DATA FEED COLLECTORS (Producers)              │
│  • CoinGeckoAgent     • CoinMarketCapAgent                   │
│  • NewsScraperAgent   • FearGreedAgent                       │
│  Implements: Circuit Breaker, Retry Logic, Avro Validation   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    KAFKA MESSAGE BROKER                       │
│  Topics:                                                      │
│  • crypto-prices         • crypto-news                       │
│  • crypto-market-sentiment                                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│           SPARK STREAMING CONSUMERS (Analytics)               │
│  • consumer_prices.py        (price data ingestion)          │
│  • consumer_news.py          (news + sentiment analysis)     │
│  • consumer_analytics.py     (moving avg, volatility)        │
│  • consumer_anomaly_detection.py (anomaly alerts)            │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│              INFLUXDB (Time-Series Database)                  │
│  Measurements:                                                │
│  • crypto_market         • crypto_news                       │
│  • crypto_analytics      • crypto_anomalies                  │
└─────────┬─────────────────────────┬──────────────────────────┘
          │                         │
          ▼                         ▼
┌────────────────────┐    ┌────────────────────────────────────┐
│  GRAFANA           │    │  FASTAPI + NEXT.JS                 │
│  (Ops Dashboard)   │    │  (User Dashboard)                  │
│  Port 3000         │    │  API: 8000 / Web: 3001            │
└────────────────────┘    └────────────────────────────────────┘
```

---

## ✨ Key Features

### Data Collection
- ✅ **Multi-Source Aggregation**: CoinGecko, CoinMarketCap, RSS feeds
- ✅ **Real-Time Streaming**: Sub-minute data freshness
- ✅ **Schema Validation**: Avro schema enforcement
- ✅ **Resilience**: Circuit breakers, exponential backoff, retry logic
- ✅ **Deduplication**: Prevent duplicate data ingestion

### Stream Processing
- ✅ **Apache Spark Structured Streaming**: Distributed processing
- ✅ **Stateful Computations**: Moving averages, volatility
- ✅ **Anomaly Detection**: Real-time alerts on unusual market activity
- ✅ **Sentiment Analysis**: NLP-based news sentiment classification
- ✅ **Cross-Validation**: Compare data from multiple sources

### Analytics
- ✅ **Price Analytics**: Mean, std dev, min/max, volatility %
- ✅ **Volume Analysis**: 24h volume trends and anomalies
- ✅ **Market Sentiment**: Fear & Greed Index tracking
- ✅ **News Sentiment**: Positive/negative/neutral classification
- ✅ **Anomaly Detection**: Z-score based outlier detection

### Visualization
- ✅ **Real-Time Dashboards**: Live market data updates
- ✅ **Temporal Analysis**: Historical price charts (7d, 30d, 90d)
- ✅ **Global Market Stats**: Total market cap, volume, 24h change
- ✅ **News Feed**: Latest crypto news with sentiment indicators
- ✅ **Responsive UI**: Mobile-friendly design

---

## 🛠️ Technology Stack

### Data Collection & Messaging
- **Python 3.12**: Market data feed collectors
- **Apache Kafka 7.4.0**: Message streaming platform
- **Zookeeper 7.4.0**: Kafka coordination
- **Avro 1.10.2**: Schema validation

### Stream Processing & Storage
- **Apache Spark 3.4.1**: Distributed stream processing
- **InfluxDB 2.7**: Time-series database
- **Grafana 10.0**: Metrics visualization

### Backend & API
- **FastAPI 0.115.0**: High-performance REST API
- **Uvicorn 0.30.6**: ASGI server
- **Pydantic 2.9.2**: Data validation

### Frontend
- **Next.js 14.2.11**: React framework
- **TypeScript 5.3.3**: Type-safe JavaScript
- **Tailwind CSS 3.4.1**: Utility-first CSS
- **Recharts 2.10.3**: Chart library

### DevOps & Infrastructure
- **Docker & Docker Compose**: Containerization
- **Git**: Version control

---

## 📁 Project Structure

```
cryptoviz/
├── crypto-monitoring/           # Data pipeline (Producers + Consumers)
│   ├── agents/                  # Market Data Feed Collectors
│   │   ├── base_agent.py       # Abstract base class (Producer pattern)
│   │   ├── coingecko_agent.py  # CoinGecko market data collector
│   │   ├── coinmarketcap_agent.py
│   │   ├── news_scraper_agent.py
│   │   └── fear_greed_agent.py
│   ├── schemas/
│   │   └── crypto_price.avsc   # Avro schema (20+ fields)
│   ├── consumer_prices.py      # Spark consumer for price data
│   ├── consumer_news.py        # Spark consumer for news (+ sentiment)
│   ├── consumer_analytics.py   # Advanced analytics consumer
│   ├── consumer_anomaly_detection.py
│   ├── docker-compose.yml      # Infrastructure services
│   ├── grafana/                # Grafana dashboards
│   └── requirements.txt
│
├── crypto-app/                  # Web application
│   ├── api/                     # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/        # API endpoints
│   │   │   │   ├── coins.py
│   │   │   │   ├── news.py
│   │   │   │   ├── global_stats.py
│   │   │   │   └── fear_greed.py
│   │   │   └── services/       # Business logic
│   │   └── Dockerfile
│   │
│   └── web/                     # Next.js frontend
│       ├── app/
│       │   ├── page.tsx        # Home dashboard
│       │   └── coin/[id]/      # Coin detail pages
│       ├── components/
│       │   ├── CryptoTable.tsx
│       │   ├── NewsSection.tsx
│       │   └── GlobalStatsCards.tsx
│       ├── lib/
│       │   └── api.ts          # API client
│       └── Dockerfile
│
└── README.md                    # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (20.10+)
- **Python 3.12+** (for local development)
- **Node.js 18+** (for frontend development)
- **CoinMarketCap API Key** (free tier: https://coinmarketcap.com/api/)

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/cryptoviz.git
cd cryptoviz
```

#### 2. Configure Environment

```bash
# Create .env file in crypto-monitoring/
cd crypto-monitoring
cp .env.example .env

# Edit .env and add your configuration:
# - INFLUX_TOKEN (generated on first run)
# - CMC_API_KEY (from CoinMarketCap)
```

#### 3. Start Infrastructure Services

```bash
# In crypto-monitoring/
docker-compose up -d

# Wait for services to be ready (~30 seconds)
docker-compose ps
```

This starts:
- ✅ Zookeeper (port 2181)
- ✅ Kafka (port 9092)
- ✅ InfluxDB (port 8086)
- ✅ Grafana (port 3000)

#### 4. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 5. Start Market Data Feed Collectors (Producers)

```bash
# Terminal 1: CoinGecko collector (every 60s)
python run_coingecko_agent.py

# Terminal 2: CoinMarketCap collector (every 120s)
python run_coinmarketcap_agent.py

# Terminal 3: News scraper (every 300s)
python run_news_scraper.py

# Terminal 4: Fear & Greed Index (every 300s)
python run_fear_greed_agent.py
```

#### 6. Start Spark Consumers (Analytics Builders)

```bash
# Terminal 5: Price data consumer
python consumer_prices.py

# Terminal 6: News consumer (with sentiment analysis)
python consumer_news.py

# Terminal 7: Analytics consumer
python consumer_analytics.py

# Terminal 8: Anomaly detection consumer
python consumer_anomaly_detection.py
```

#### 7. Start Web Application

```bash
# Terminal 9: FastAPI backend
cd crypto-app/api
uvicorn app.main:app --reload --port 8000

# Terminal 10: Next.js frontend
cd crypto-app/web
npm install
npm run dev
```

#### 8. Access Dashboards

- **Web App**: http://localhost:3001
- **Grafana**: http://localhost:3000 (admin/admin)
- **FastAPI Docs**: http://localhost:8000/docs
- **InfluxDB UI**: http://localhost:8086

---

## 🔧 Components

### 1. Market Data Feed Collectors (Producers)

#### CoinGeckoAgent
- **Purpose**: Collect market data for 20 major cryptocurrencies
- **Frequency**: Every 60 seconds
- **Data**: Price, market cap, volume, ATH/ATL, supply metrics
- **Kafka Topic**: `crypto-prices`

#### CoinMarketCapAgent
- **Purpose**: Professional-grade market data for cross-validation
- **Frequency**: Every 120 seconds
- **Data**: Top 20 cryptos by market cap
- **Kafka Topic**: `crypto-prices`

#### NewsScraperAgent
- **Purpose**: Scrape cryptocurrency news from RSS feeds
- **Sources**: CoinDesk, CoinTelegraph
- **Frequency**: Every 300 seconds (5 minutes)
- **Kafka Topic**: `crypto-news`

#### FearGreedAgent
- **Purpose**: Collect market sentiment index
- **Source**: Alternative.me API
- **Frequency**: Every 300 seconds
- **Kafka Topic**: `crypto-market-sentiment`

### 2. Stream Processing Consumers (Analytics Builders)

#### consumer_prices.py
- Ingests price data from `crypto-prices` topic
- Writes to InfluxDB measurement: `crypto_market`
- Fields: 20+ metrics per cryptocurrency

#### consumer_news.py
- Ingests news from `crypto-news` topic
- **Sentiment Analysis**: Keyword-based classification
- Writes to InfluxDB measurement: `crypto_news`
- Tags: source, sentiment

#### consumer_analytics.py
- Calculates advanced metrics:
  - Moving averages (approximation over window)
  - Volatility (standard deviation %)
  - Price ranges (min/max)
  - Volume statistics
- Writes to InfluxDB measurement: `crypto_analytics`

#### consumer_anomaly_detection.py
- Detects real-time anomalies:
  - **Volume Spikes**: >3σ from mean
  - **Price Spikes**: >5% change in <1 min
  - **Source Divergence**: >1% difference between sources
- Writes to InfluxDB measurement: `crypto_anomalies`
- Severity levels: critical, high, medium

### 3. Dynamic Viewers

#### Next.js Web Application
- **Home Dashboard**:
  - Global market stats (market cap, volume, 24h change)
  - Latest crypto news with sentiment indicators
  - Top 100 cryptocurrencies table
- **Coin Detail Pages**:
  - Price history charts (7d, 30d)
  - Detailed metrics (ATH/ATL, supply, etc.)
  - Sparkline visualizations

#### Grafana Dashboards
- **Core Metrics**: Real-time price, volume, market cap
- **Comparisons**: Multi-source data validation
- **Alerts**: Anomaly notifications

---

## 📊 Data Flow

### Producer/Consumer Paradigm

```
PRODUCERS (Agents)                    CONSUMERS (Spark)
─────────────────                     ──────────────────
CoinGecko Agent      ─┐              ┌─→ consumer_prices.py
CoinMarketCap Agent  ─┼─→ Kafka ────→┼─→ consumer_analytics.py
News Scraper Agent   ─┼─→ Topics     │   consumer_anomaly_detection.py
Fear & Greed Agent   ─┘              └─→ consumer_news.py
                                            │
                                            ↓
                                        InfluxDB
                                            │
                                       ┌────┴─────┐
                                       ↓          ↓
                                   Grafana   Next.js
```

### Data Pipeline Stages

1. **Collection** (Producers):
   - Fetch data from external APIs/RSS
   - Validate against Avro schemas
   - Send to Kafka topics

2. **Streaming** (Kafka):
   - Buffer messages
   - Decouple producers from consumers
   - Enable horizontal scaling

3. **Processing** (Spark Consumers):
   - Parse JSON messages
   - Calculate analytics
   - Detect anomalies
   - Analyze sentiment

4. **Storage** (InfluxDB):
   - Time-series optimized storage
   - Indexed by tags (crypto_id, source, sentiment)
   - Retention policies (configurable)

5. **Visualization** (Grafana + Next.js):
   - Query InfluxDB via Flux
   - Render real-time charts
   - Display temporal trends

---

## 📈 Analytics

### Price Analytics
- **Moving Averages**: Approximation over batch window
- **Volatility**: Standard deviation as percentage
- **Price Range**: Min/max within window
- **Data Quality**: Count of data points per crypto

### Anomaly Detection
- **Volume Anomalies**: Z-score > 3.0
- **Price Spikes**: >5% change in <1 minute
- **Source Divergence**: >1% difference between CoinGecko/CMC
- **Alerting**: Severity-based notifications (critical/high/medium)

### Sentiment Analysis
- **News Sentiment**: Keyword-based classification
  - **Positive**: surge, rally, bullish, adoption, etc.
  - **Negative**: crash, drop, hack, ban, etc.
  - **Neutral**: No strong sentiment
- **Sentiment Score**: -1.0 (very negative) to +1.0 (very positive)
- **Applications**: Correlation with price movements

---

## 🐳 Deployment

### Docker Compose (Development)

```bash
# Start all infrastructure services
cd crypto-monitoring
docker-compose up -d

# View logs
docker-compose logs -f kafka
docker-compose logs -f influxdb

# Stop services
docker-compose down
```

### Production Deployment (TODO)

- [ ] Kubernetes manifests
- [ ] Helm charts
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Prometheus + AlertManager)
- [ ] Secrets management (Vault)

---

## 📚 API Documentation

### FastAPI Endpoints

**Base URL**: `http://localhost:8000`

#### Health Checks
- `GET /health` - API health status
- `GET /health/influx` - InfluxDB connection test

#### Coins
- `GET /coins?limit=50&page=1` - List cryptocurrencies
- `GET /coins/{crypto_id}` - Get specific coin details
- `GET /coins/{crypto_id}/history?days=7&interval=1h` - Historical data

#### Global Stats
- `GET /global` - Global market statistics

#### News
- `GET /news?limit=20&source=coindesk&hours=24` - Latest news
- `GET /news/sources` - List news sources

#### Sentiment
- `GET /fear-greed` - Fear & Greed Index

**Interactive Docs**: http://localhost:8000/docs

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- **Python**: PEP 8, type hints, docstrings
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits format

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **CoinGecko** - Free cryptocurrency API
- **CoinMarketCap** - Professional market data
- **Alternative.me** - Fear & Greed Index
- **CoinDesk & CoinTelegraph** - Crypto news sources

---

## 📞 Contact

**Project Team**: T-DAT-901 Epitech

**Repository**: https://github.com/your-org/cryptoviz

---

**Built with ❤️ for the cryptocurrency community**
