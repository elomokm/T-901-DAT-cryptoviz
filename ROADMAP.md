# 🚀 CryptoViz - Roadmap de Développement

## 📊 État d'Avancement Actuel

### ✅ Phase 0 : Infrastructure de Base (TERMINÉ)
- [x] Kafka + Zookeeper
- [x] InfluxDB 2.x
- [x] Grafana + provisioning
- [x] Spark Structured Streaming consumer
- [x] Architecture BaseAgent (design pattern)

### ✅ Phase 1.1 : Agent CoinMarketCap (TERMINÉ)
- [x] Agent CoinMarketCap avec détection d'anomalies
- [x] Validation croisée CoinGecko vs CoinMarketCap
- [x] Script d'analyse de divergence
- [x] Documentation complète

---

## 🎯 Roadmap Complète

### **Semaine 1 : Agents + Data Quality**

#### Phase 1.2 : Data Quality Framework (2 jours)
**Objectif:** Garantir la qualité et fiabilité des données

**Tâches:**
- [ ] Schema validation (Avro/JSON Schema)
- [ ] Consumer Spark de validation croisée
- [ ] Dead Letter Queue (DLQ) pour messages invalides
- [ ] Métriques de qualité (InfluxDB)

**Livrables:**
```
crypto-monitoring/
  validators/
    schema_validator.py       ← Validation Avro/JSON
    cross_validator.py        ← Compare CG vs CMC
    anomaly_detector.py       ← ML-based anomaly detection
  consumer_validation.py      ← Consumer Spark dédié
  schemas/
    crypto_price.avsc         ← Schema Avro
```

#### Phase 1.3 : Binance WebSocket Agent (2-3 jours)
**Objectif:** Données temps réel (trades, orderbook)

**Tâches:**
- [ ] Créer `binance_websocket_agent.py`
- [ ] Stream trades temps réel (BTC, ETH, BNB)
- [ ] Order book depth (bid/ask)
- [ ] Nouveau consumer Spark pour `crypto-realtime`

**Livrables:**
```
crypto-monitoring/
  agents/
    binance_websocket_agent.py
  consumer_realtime.py        ← Consumer pour WebSocket
  run_binance_agent.py
```

**Complexité:** 🔴 Moyenne (WebSocket + gestion reconnexion)

#### Phase 1.4 : News Scraper Agent (2 jours - OPTIONNEL)
**Objectif:** Analyse sentiment + actualités crypto

**Tâches:**
- [ ] Scraper CoinTelegraph, Decrypt
- [ ] Reddit API (/r/cryptocurrency)
- [ ] Sentiment analysis (TextBlob/VADER)
- [ ] Consumer Spark pour `crypto-news`

**Livrables:**
```
crypto-monitoring/
  agents/
    news_scraper_agent.py
  consumer_news.py
  requirements.txt            ← + beautifulsoup4, textblob
```

---

### **Semaine 2 : Sécurité + WebApp Foundation**

#### Phase 2.1 : Sécurisation Kafka (1-2 jours)
**Objectif:** Production-ready Kafka security

**Tâches:**
- [ ] SASL/SCRAM authentication
- [ ] SSL/TLS encryption
- [ ] ACLs (Access Control Lists)
- [ ] Mise à jour docker-compose.yml

**Configuration:**
```yaml
# docker-compose.yml
kafka:
  environment:
    KAFKA_SECURITY_PROTOCOL: SASL_SSL
    KAFKA_SASL_MECHANISM: SCRAM-SHA-256
  volumes:
    - ./kafka/secrets:/etc/kafka/secrets
```

#### Phase 2.2 : FastAPI Backend (2 jours)
**Objectif:** API REST pour la webapp

**Tâches:**
- [ ] Créer projet FastAPI
- [ ] Endpoints `/api/prices`, `/api/market`
- [ ] Querying InfluxDB avec Flux
- [ ] Cache Redis (optionnel)
- [ ] CORS configuration

**Structure:**
```
crypto-app/api/
  app/
    main.py                   ← FastAPI app
    routes/
      prices.py               ← /api/prices
      market.py               ← /api/market
      news.py                 ← /api/news
    services/
      influx_service.py       ← Query InfluxDB
      cache_service.py        ← Redis cache
    models/
      crypto.py               ← Pydantic models
```

**Endpoints:**
```python
GET  /api/prices?symbols=BTC,ETH&interval=1h
GET  /api/market/overview
GET  /api/market/dominance
GET  /api/news?limit=10
WS   /ws/prices               ← WebSocket pour temps réel
```

#### Phase 2.3 : Next.js Setup (1-2 jours)
**Objectif:** Structure de la webapp

**Tâches:**
- [ ] Setup Next.js 14 (App Router)
- [ ] Configuration Tailwind CSS
- [ ] Composants de base (Layout, Navbar)
- [ ] Routing structure

**Structure:**
```
crypto-app/web/
  app/
    layout.tsx
    page.tsx                  ← Landing page
    dashboard/
      page.tsx                ← Main dashboard
      prices/
        page.tsx              ← Prix en temps réel
      market/
        page.tsx              ← Market overview
      news/
        page.tsx              ← Actualités crypto
  components/
    charts/
      PriceChart.tsx          ← Chart interactif
      MarketCapChart.tsx
    tables/
      CryptoTable.tsx
    ui/
      Card.tsx
      Badge.tsx
  lib/
    api.ts                    ← Client API (fetch)
```

---

### **Semaine 3 : WebApp Features + Polish**

#### Phase 3.1 : Charts Interactifs (2 jours)
**Objectif:** Visualisations premium

**Tâches:**
- [ ] Intégration ApexCharts ou Recharts
- [ ] Chart prix (candlestick, line)
- [ ] Chart market cap dominance
- [ ] Chart volume 24h
- [ ] Responsive design

**Composants:**
```tsx
<PriceChart 
  symbol="BTC" 
  interval="1h" 
  type="candlestick" 
/>

<MarketDominanceChart 
  cryptos={['BTC', 'ETH', 'BNB']} 
/>
```

#### Phase 3.2 : WebSocket Real-time (1 jour)
**Objectif:** Updates en temps réel sans refresh

**Tâches:**
- [ ] WebSocket client (Next.js)
- [ ] WebSocket server (FastAPI)
- [ ] Streaming Binance → WebSocket → UI

**Implémentation:**
```typescript
// lib/websocket.ts
const ws = new WebSocket('ws://localhost:8000/ws/prices');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updatePrices(data);
};
```

#### Phase 3.3 : News + Sentiment (1 jour)
**Objectif:** Section actualités avec sentiment

**Tâches:**
- [ ] Affichage news récentes
- [ ] Badge sentiment (positif/négatif/neutre)
- [ ] Filtres par source
- [ ] Recherche par mot-clé

#### Phase 3.4 : Dashboard Premium (1-2 jours)
**Objectif:** UI professionnelle inspirée TradingView

**Features:**
- [ ] Theme dark/light
- [ ] Layout multi-colonnes
- [ ] KPIs animés
- [ ] Alerts personnalisables
- [ ] Favoris cryptos

---

## 📂 Structure Finale du Projet

```
T-901-DAT-cryptoviz/
├── crypto-monitoring/           ← Pipeline de données
│   ├── agents/
│   │   ├── coingecko_agent.py          ✅
│   │   ├── coinmarketcap_agent.py      ✅
│   │   ├── binance_websocket_agent.py  ⏳
│   │   ├── news_scraper_agent.py       ⏳
│   │   └── fear_greed_agent.py         ✅
│   ├── validators/                     ⏳
│   ├── schemas/                        ⏳
│   ├── consumer_prices.py              ✅
│   ├── consumer_validation.py          ⏳
│   ├── consumer_realtime.py            ⏳
│   ├── consumer_news.py                ⏳
│   └── docker-compose.yml              ✅
│
├── crypto-app/                  ← WebApp
│   ├── api/                     ⏳ FastAPI
│   └── web/                     ⏳ Next.js
│
└── docs/
    ├── ROADMAP.md               ✅ (ce fichier)
    ├── CROSS_VALIDATION.md      ✅
    ├── TROUBLESHOOTING.md       ✅
    └── ARCHITECTURE.md          ⏳
```

---

## 🛠️ Commandes Rapides

### Lancer tous les agents
```bash
# Terminal 1 : CoinGecko
python run_coingecko_agent.py

# Terminal 2 : CoinMarketCap
python run_coinmarketcap_agent.py

# Terminal 3 : Binance (quand prêt)
python run_binance_agent.py

# Terminal 4 : Consumer Spark
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 consumer_prices.py
```

### Validation croisée
```bash
# Analyser divergences pendant 60s
python cross_validation.py 60
```

### Lancer la webapp (quand prête)
```bash
# Backend FastAPI
cd crypto-app/api
uvicorn app.main:app --reload

# Frontend Next.js
cd crypto-app/web
npm run dev
```

---

## 🎓 Critères d'Évaluation Projet

### Points Techniques (60%)
- [x] Kafka + Spark Streaming (15%)
- [x] InfluxDB + Grafana (10%)
- [ ] Data Quality + Validation (10%)
- [ ] Sécurité (SASL, SSL, ACLs) (10%)
- [ ] WebApp moderne (FastAPI + Next.js) (15%)

### Innovation (20%)
- [x] Validation croisée multi-sources (5%)
- [ ] WebSocket temps réel (5%)
- [ ] ML Anomaly detection (5%)
- [ ] Sentiment analysis (5%)

### Documentation (20%)
- [x] README complet (5%)
- [x] Architecture diagram (5%)
- [ ] API documentation (Swagger) (5%)
- [ ] Tests unitaires (5%)

---

## 📞 Prochaines Actions Immédiates

### 1️⃣ **AUJOURD'HUI** : Obtenir clé CoinMarketCap
```bash
# 1. Créer compte sur https://coinmarketcap.com/api/
# 2. Copier la clé API
# 3. Mettre dans .env
nano .env
# CMC_API_KEY=votre_cle_ici

# 4. Tester l'agent
python run_coinmarketcap_agent.py
```

### 2️⃣ **DEMAIN** : Data Quality Framework
- Créer schema Avro
- Consumer de validation

### 3️⃣ **Après-demain** : Binance WebSocket
- Agent temps réel
- Consumer dédié

---

## 📚 Ressources Utiles

- [CoinMarketCap API](https://coinmarketcap.com/api/)
- [Binance WebSocket Docs](https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [ApexCharts React](https://apexcharts.com/docs/react-charts/)
- [Kafka Security](https://kafka.apache.org/documentation/#security)

---

**🎯 Objectif Final:** Plateforme de monitoring crypto professionnelle avec validation croisée, temps réel, et UI moderne.

**⏰ Deadline:** 3 semaines à partir d'aujourd'hui (7 novembre 2025)

**📊 Progression:** 25% ████░░░░░░░░░░░░░░░░ (Infrastructure + Agent CMC)
