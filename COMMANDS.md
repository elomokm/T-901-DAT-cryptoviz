# CryptoViz - Commandes Essentielles

Aide-mémoire des commandes les plus utilisées.

---

## 🐳 Docker & Infrastructure

### Démarrer l'infrastructure
```bash
cd crypto-monitoring
docker-compose up -d
```

### Arrêter l'infrastructure
```bash
docker-compose down
```

### Voir les logs
```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f kafka
docker-compose logs -f influxdb
docker-compose logs -f grafana
```

### Redémarrer un service
```bash
docker-compose restart kafka
docker-compose restart influxdb
```

### Statut des services
```bash
docker-compose ps
```

### Supprimer tout (données incluses) ⚠️
```bash
docker-compose down -v
```

---

## 🔧 Producers (Agents)

### Lancer tous les agents automatiquement
```bash
cd crypto-monitoring
./start_all.sh
```

### Lancer individuellement

#### CoinGecko Agent
```bash
cd crypto-monitoring
source .venv/bin/activate
python run_coingecko_agent.py
```

#### CoinMarketCap Agent
```bash
python run_coinmarketcap_agent.py
```

#### News Scraper Agent
```bash
python run_news_scraper.py
```

#### Fear & Greed Agent
```bash
python run_fear_greed_agent.py
```

---

## ⚙️ Consumers (Analytics)

### Lancer tous les consumers
Inclus dans `start_all.sh`, ou manuellement:

#### Price Data Consumer
```bash
cd crypto-monitoring
source .venv/bin/activate
python consumer_prices.py
```

#### News Consumer (avec sentiment)
```bash
python consumer_news.py
```

#### Analytics Consumer
```bash
python consumer_analytics.py
```

#### Anomaly Detection Consumer
```bash
python consumer_anomaly_detection.py
```

---

## 🌐 Web Application

### Backend API (FastAPI)
```bash
cd crypto-app/api
uvicorn app.main:app --reload --port 8000
```

Accès: http://localhost:8000/docs

### Frontend (Next.js)
```bash
cd crypto-app/web
npm install  # Première fois uniquement
npm run dev
```

Accès: http://localhost:3001

---

## 🔍 Vérifications & Debug

### Vérifier Kafka topics
```bash
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Consommer messages Kafka (debug)
```bash
# Topic crypto-prices
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto-prices \
  --from-beginning

# Topic crypto-news
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto-news \
  --from-beginning
```

### Test API santé
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/influx
```

### Test endpoints API
```bash
# Liste coins
curl http://localhost:8000/coins?limit=5

# Détail coin
curl http://localhost:8000/coins/bitcoin

# News
curl http://localhost:8000/news?limit=10

# Global stats
curl http://localhost:8000/global
```

---

## 📊 InfluxDB

### Query Flux (dans l'UI)
```flux
// Dernières valeurs crypto_market
from(bucket: "crypto-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "crypto_market")
  |> filter(fn: (r) => r.crypto_id == "bitcoin")

// Analytics calculés
from(bucket: "crypto-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "crypto_analytics")

// Anomalies détectées
from(bucket: "crypto-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "crypto_anomalies")
  |> filter(fn: (r) => r.severity == "critical")
```

---

## 🧹 Nettoyage

### Arrêter tout proprement
```bash
# Ctrl+C dans chaque terminal des agents/consumers

# Arrêter Docker
docker-compose down
```

### Reset complet (⚠️ perte de données)
```bash
docker-compose down -v
rm -rf /tmp/spark-checkpoint-*
```

---

## 📦 Installation & Setup

### Première installation
```bash
# 1. Cloner repo
git clone <repo-url>
cd cryptoviz

# 2. Setup Python
cd crypto-monitoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Setup .env
cp .env.example .env
# Éditer .env avec vos API keys

# 4. Démarrer infra
docker-compose up -d

# 5. Attendre 30s
sleep 30

# 6. Lancer tout
./start_all.sh
```

### Mise à jour dépendances
```bash
# Python
cd crypto-monitoring
source .venv/bin/activate
pip install --upgrade -r requirements.txt

# Frontend
cd crypto-app/web
npm install
```

---

## 🔄 Git

### Workflow de développement
```bash
# Créer branche
git checkout -b feature/my-feature

# Ajouter changements
git add .
git commit -m "feat: add my feature"

# Push
git push origin feature/my-feature
```

### Voir modifications
```bash
git status
git diff
git log --oneline -10
```

---

## 🐛 Troubleshooting Rapide

### Kafka ne démarre pas
```bash
docker-compose restart zookeeper
sleep 5
docker-compose restart kafka
```

### InfluxDB inaccessible
```bash
docker-compose restart influxdb
# Attendre 10s
docker-compose logs influxdb
```

### Consumer Spark ne lit pas
```bash
# Vérifier que Kafka a des messages
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto-prices \
  --max-messages 5

# Supprimer checkpoints
rm -rf /tmp/spark-checkpoint-*
```

### Frontend ne se connecte pas à l'API
```bash
# Vérifier CORS
curl -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS http://localhost:8000/coins
```

---

## 📚 Documentation

### Lire la doc
```bash
# README principal
cat README.md

# Architecture technique
cat ARCHITECTURE.md

# Guide rapide
cat QUICKSTART.md

# Changelog
cat CHANGELOG.md
```

---

**Bon développement! 🚀**
