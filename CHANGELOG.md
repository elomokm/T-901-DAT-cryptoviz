# CryptoViz - Changelog

Toutes les modifications importantes apportées au projet CryptoViz.

---

## [v2.0.0] - 2025-01-16 - Réalignement avec Sujet T-DAT-901

### 🎯 Objectif de la Refonte

Réaligner l'architecture du projet avec les **exigences exactes du sujet**:
- ✅ Online Web Scrapper (Producer pattern)
- ✅ Online Analytics Builder (Consumer pattern + Spark)
- ✅ Dynamic Viewer (dimension temporelle)
- ✅ Paradigme Producer/Consumer strictement implémenté

---

### ✨ Nouveautés Majeures

#### 1. **News Scraper Agent** (Producer)
- Scraping RSS feeds en temps réel
- Sources: CoinDesk, CoinTelegraph
- Fréquence: Toutes les 5 minutes
- Output: Kafka topic `crypto-news`

**Fichiers ajoutés**:
- `crypto-monitoring/agents/news_scraper_agent.py`
- `crypto-monitoring/run_news_scraper.py`

#### 2. **Sentiment Analysis** (Consumer + Analytics)
- Analyse de sentiment keyword-based
- Classification: positive/negative/neutral
- Score: -1.0 à +1.0
- Stockage avec tag `sentiment`

**Fichiers modifiés**:
- `crypto-monitoring/consumer_news.py` (ajout fonction `analyze_sentiment()`)

#### 3. **Advanced Analytics Consumer**
- Calcul de moyennes mobiles (approximation)
- Volatilité (écart-type en %)
- Price ranges (min/max)
- Volume statistics

**Fichiers ajoutés**:
- `crypto-monitoring/consumer_analytics.py`

#### 4. **Anomaly Detection Consumer**
- Détection volume spikes (>3σ)
- Détection price spikes (>5% en <1min)
- Détection divergence sources (>1%)
- Alertes par severity (critical/high/medium)

**Fichiers ajoutés**:
- `crypto-monitoring/consumer_anomaly_detection.py`

#### 5. **News Display Component** (Frontend)
- Affichage news en temps réel
- Indicateurs de sentiment
- Auto-refresh toutes les 5 minutes
- Filtrage par source

**Fichiers ajoutés**:
- `crypto-app/web/components/NewsSection.tsx`
- `crypto-app/api/app/routers/news.py`
- `crypto-app/api/app/services/news_service.py`

---

### 🔄 Renommage & Clarification

#### Agents → "Market Data Feed Collectors"

Tous les agents ont été renommés conceptuellement pour mieux refléter leur rôle:

| Ancien Nom | Nouveau Nom | Justification |
|-----------|-------------|---------------|
| CoinGecko Agent | CoinGecko Market Data Feed Collector | Clarifier le rôle de scraping continu |
| CoinMarketCap Agent | CoinMarketCap Market Data Feed Collector | Idem |
| Fear & Greed Agent | Market Sentiment Data Feed Collector | Idem |
| News Scraper | News Feed Collector | Cohérence terminologique |

**Fichiers modifiés**:
- `crypto-monitoring/agents/base_agent.py` (docstring mis à jour)
- `crypto-monitoring/agents/coingecko_agent.py` (docstring)
- `crypto-monitoring/agents/coinmarketcap_agent.py` (docstring)
- `crypto-monitoring/agents/fear_greed_agent.py` (docstring)

---

### 📊 Nouveaux Measurements InfluxDB

| Measurement | Description | Tags | Fields |
|-------------|-------------|------|--------|
| **crypto_news** | Articles de news | source, sentiment | title, link, description, sentiment_score |
| **crypto_analytics** | Métriques avancées | crypto_id, symbol | price_mean, price_std, volatility_pct, volume_mean |
| **crypto_anomalies** | Alertes d'anomalies | crypto_id, anomaly_type, severity | value, expected, z_score, message |

---

### 🌐 Nouveaux Endpoints API

#### `/news` (GET)
Récupère les dernières actualités crypto.

**Query Params**:
- `limit` (int, default=20): Nombre d'articles
- `source` (str, optional): Filtrer par source
- `hours` (int, default=24): Articles des X dernières heures

**Response**:
```json
{
  "count": 10,
  "news": [
    {
      "title": "Bitcoin Surges to New ATH",
      "link": "https://...",
      "published_date": "2025-01-16T10:30:00Z",
      "source": "coindesk",
      "description": "...",
      "image_url": "https://...",
      "sentiment": "positive",
      "sentiment_score": 0.75
    }
  ]
}
```

#### `/news/sources` (GET)
Liste des sources de news disponibles.

**Response**:
```json
{
  "sources": [
    {"id": "coindesk", "name": "CoinDesk", "url": "https://coindesk.com"},
    {"id": "cointelegraph", "name": "CoinTelegraph", "url": "https://cointelegraph.com"}
  ]
}
```

---

### 📝 Documentation

#### Nouveaux Fichiers

- **README.md**: Documentation complète du projet
  - Overview architecture
  - Guide de démarrage
  - Composants détaillés
  - API documentation

- **ARCHITECTURE.md**: Document technique
  - Justification des choix
  - Comparaison technologies
  - Design patterns
  - Flux de données détaillés
  - Schémas Avro & InfluxDB

- **CHANGELOG.md**: Ce fichier
  - Historique des modifications
  - Notes de migration

#### Scripts Utilitaires

- **start_all.sh**: Script de démarrage automatique
  - Lance Docker Compose
  - Démarre tous les producers (4 agents)
  - Démarre tous les consumers (4 consumers)
  - Multi-OS (macOS, Linux)

---

### 🔧 Améliorations Techniques

#### Resilience & Error Handling

1. **Circuit Breaker Pattern**: Tous les agents
2. **Exponential Backoff**: Retry logic sur API calls
3. **Batch Sending**: Optimisation throughput Kafka
4. **Schema Validation**: Avro validation avant envoi
5. **Deduplication**: Cache pour éviter doublons (news)

#### Performance

1. **Session Pooling HTTP**: Réutilisation connexions TCP
2. **Spark Micro-Batching**: Fenêtres 30-60s
3. **InfluxDB Batch Writes**: Réduction I/O
4. **Async Processing**: Kafka producer async

---

### 📦 Nouvelles Dépendances

#### Python (crypto-monitoring/requirements.txt)
- `feedparser==6.0.11` (RSS parsing)

#### Déjà présent (pas de changement)
- `kafka-python==2.2.15`
- `pyspark==3.4.1`
- `influxdb-client==1.48.0`
- `tenacity==9.1.2`
- `pybreaker==1.4.1`

---

### 🗑️ Suppressions

#### Fichiers Non Utilisés
- Aucun fichier supprimé (ajouts uniquement)

---

### ⚙️ Configuration

#### Nouvelles Variables d'Environnement

**crypto-monitoring/.env**:
```bash
# Agent News Scraper
NEWS_POLL_INTERVAL=300  # 5 minutes
```

---

### 🚀 Migration depuis v1.0

#### Étapes de Migration

1. **Pull les changements**:
   ```bash
   git pull origin feature/agent_opt_elom
   ```

2. **Mettre à jour les dépendances Python**:
   ```bash
   cd crypto-monitoring
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Mettre à jour .env**:
   ```bash
   cp .env.example .env
   # Ajouter NEWS_POLL_INTERVAL=300
   ```

4. **Redémarrer l'infrastructure**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

5. **Lancer les nouveaux composants**:
   ```bash
   # Option 1: Script automatique (recommandé)
   ./start_all.sh

   # Option 2: Manuel
   python run_news_scraper.py
   python consumer_news.py
   python consumer_analytics.py
   python consumer_anomaly_detection.py
   ```

6. **Vérifier que tout fonctionne**:
   - News scraper collecte articles (check logs)
   - InfluxDB contient measurement `crypto_news`
   - API `/news` retourne des articles
   - Frontend affiche la section news

---

### 📊 Métriques

#### Avant v2.0
- 3 Producers (agents)
- 1 Consumer (prices only)
- 1 Measurement InfluxDB
- 0 Analytics avancés

#### Après v2.0
- **4 Producers** (agents) ✅
- **4 Consumers** ✅
- **4 Measurements InfluxDB** ✅
- **3 Types d'Analytics**: moving avg, anomalies, sentiment ✅

---

### 🐛 Bugs Corrigés

#### Alignement avec Sujet
- ✅ Ajout d'un vrai "web scraper" (RSS feeds)
- ✅ Renforcement du paradigme producer/consumer
- ✅ Analytics builder plus complet (Spark)
- ✅ Dimension temporelle dans viewer

---

### 🔮 Roadmap Future

#### v2.1 (Court Terme)
- [ ] Ajouter plus de sources de news (Reddit, Twitter)
- [ ] Améliorer sentiment analysis (NLP model)
- [ ] Caching API (Redis)
- [ ] Tests unitaires (pytest)

#### v2.2 (Moyen Terme)
- [ ] Machine Learning pour prédictions
- [ ] Alerting Slack/Email sur anomalies
- [ ] WebSockets pour real-time frontend
- [ ] Dashboard Grafana personnalisé

#### v3.0 (Long Terme)
- [ ] Déploiement Kubernetes
- [ ] CI/CD Pipeline (GitHub Actions)
- [ ] Monitoring Prometheus
- [ ] Auto-scaling consumers

---

### 👥 Contributeurs

- **Elom Okouma-Koumassoun** - Architecture & Development

---

### 📄 License

MIT License - Voir LICENSE file

---

**Last Updated**: 2025-01-16
