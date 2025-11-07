# 🚀 Crypto Monitoring Pipeline

Pipeline de collecte et analyse de données crypto en temps réel avec architecture agent-based.

## 📊 Architecture

```
┌─────────────────┐      ┌─────────────────┐
│  CoinGecko API  │      │CoinMarketCap API│
│   60s polling   │      │  120s polling   │
└────────┬────────┘      └────────┬────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│ CoinGecko Agent │      │ CoinMarketCap   │
│                 │      │     Agent       │
└────────┬────────┘      └────────┬────────┘
         │                        │
         └───────┬────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ crypto-prices │  ← Kafka Topic
         │  + validation │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │ Spark Consumer│
         │  + Validation │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │   InfluxDB    │  ← Time-series DB
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │    Grafana    │  ← Dashboards
         └───────────────┘
```

### Stack Technique
- **Collecte** : Python Agents (CoinGecko, CoinMarketCap, Fear & Greed)
- **Message Broker** : Apache Kafka
- **Traitement** : Spark Structured Streaming  
- **Stockage** : InfluxDB (time-series)
- **Visualisation** : Grafana

### Agents Disponibles
- ✅ **CoinGeckoAgent** : 20 cryptos, prix + metadata (60s)
- ✅ **CoinMarketCapAgent** : Validation croisée + anomalies (120s)
- ✅ **FearGreedAgent** : Sentiment du marché (300s)
- ⏳ **BinanceWebSocketAgent** : Temps réel (à venir)
- ⏳ **NewsScraperAgent** : Actualités crypto (à venir)

---

## ⚡ Quick Start

### Prérequis
- **Python 3.12+**
- **Java 17** (pour Spark)
- **Docker & Docker Compose**

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/elomokm/T-901-DAT-cryptoviz.git
cd T-901-DAT-cryptoviz/crypto-monitoring

# 2. Créer l'environnement Python
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# ⚠️ Éditer .env et remplacer 'your_influxdb_token_here' avec ton token
```

### Configuration InfluxDB

```bash
# 1. Démarrer l'infrastructure
docker-compose up -d kafka zookeeper influxdb grafana

# 2. Accéder à InfluxDB UI : http://localhost:8086
#    - Username: admin
#    - Password: (créer lors de la première connexion)
#    - Org: crypto-org
#    - Bucket: crypto-data

# 3. Créer un token API
#    Settings → API Tokens → Generate API Token → All Access Token
#    Copier le token dans .env (variable INFLUX_TOKEN)
```

### Lancement du Pipeline

```bash
# Terminal 1 : CoinGecko Agent (20 cryptos toutes les 60s)
python run_coingecko_agent.py

# Terminal 2 : CoinMarketCap Agent (validation croisée, 120s)
python run_coinmarketcap_agent.py

# Terminal 3 : Spark Consumer Prices (Kafka → InfluxDB - données brutes)
python consumer_prices.py

# Terminal 4 : Spark Consumer Validation (validation croisée automatique)
python consumer_validation.py

# Terminal 5 (optionnel) : Monitor DLQ (anomalies en temps réel)
python monitor_dlq.py

# Terminal 6 (optionnel) : Validation manuelle (debug)
python cross_validation.py 60
```

### Vérification

```bash
# Voir les données dans InfluxDB
docker exec -it influxdb influx query 'from(bucket: "crypto-data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "crypto_market")
  |> filter(fn: (r) => r["_field"] == "price_usd")
  |> limit(n: 5)'
```

**Accès Grafana** : http://localhost:3000 (admin/admin)

---

## 📁 Structure du Projet

```
crypto-monitoring/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Classe abstraite (Template Pattern)
│   ├── config.py              # Configuration centralisée
│   ├── coingecko_agent.py     # Agent CoinGecko (20 cryptos)
│   └── fear_greed_agent.py    # Agent Fear & Greed Index
│
├── grafana/
│   ├── dashboards/            # Dashboards JSON
│   └── provisioning/          # Config auto Grafana
│
├── _archive/                  # Ancien code (référence)
│
├── consumer_prices.py         # Spark Consumer (Kafka → InfluxDB)
├── docker-compose.yml         # Infrastructure (Kafka, InfluxDB, Grafana)
├── requirements.txt           # Dépendances Python
├── .env.example               # Template de configuration
├── TROUBLESHOOTING.md         # Guide de debugging
└── README.md                  # Ce fichier
```

---

## 🔧 Configuration

### Variables d'Environnement (.env)

| Variable | Description | Défaut |
|----------|-------------|--------|
| `KAFKA_BROKER` | Adresse Kafka | `localhost:9092` |
| `INFLUX_URL` | URL InfluxDB | `http://localhost:8086` |
| `INFLUX_TOKEN` | Token API InfluxDB | **REQUIS** |
| `INFLUX_ORG` | Organisation InfluxDB | `crypto-org` |
| `INFLUX_BUCKET` | Bucket de stockage | `crypto-data` |
| `COINGECKO_POLL_INTERVAL` | Intervalle CoinGecko (s) | `60` |
| `FEAR_GREED_POLL_INTERVAL` | Intervalle Fear & Greed (s) | `300` |

---

## 📊 Agents Disponibles

### 1. CoinGeckoAgent ✅
**Source** : CoinGecko API  
**Topic Kafka** : `crypto-prices`  
**Fréquence** : 60s  
**Données** : 20 cryptos (BTC, ETH, USDT, XRP, BNB, SOL, etc.)

**Champs collectés** :
- Prix USD, Market Cap, Volume 24h
- Variations 1h/24h/7d
- ATH/ATL avec dates et % changement
- Circulating/Total/Max Supply

### 2. FearGreedAgent ✅
**Source** : Alternative.me API  
**Topic Kafka** : `crypto-market-sentiment`  
**Fréquence** : 300s (5 min)  
**Données** : Index de sentiment (0-100)

---

## 🛠️ Développement

### Créer un Nouvel Agent

```python
# agents/my_new_agent.py
from agents.base_agent import BaseAgent
from agents.config import TOPICS
import requests

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyNewAgent",
            topic=TOPICS['prices'],
            poll_interval=120
        )
    
    def fetch_data(self):
        """Implémenter la logique de collecte"""
        response = requests.get("https://api.example.com/data")
        data = response.json()
        
        # Transformer et retourner une liste de dicts
        return [{"field1": "value1", "field2": "value2"}]

if __name__ == "__main__":
    agent = MyNewAgent()
    agent.run()
```

---

## 🐛 Troubleshooting

### Problème : "No data" dans InfluxDB malgré logs de succès

**Cause** : Problème de timestamp (données rejetées silencieusement)

**Solution** : Voir [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### Problème : KafkaTimeoutError

```bash
# Vérifier que Kafka tourne
docker ps | grep kafka

# Redémarrer Kafka
docker-compose restart kafka
```

### Problème : ImportError dotenv

```bash
pip install python-dotenv==1.0.1
```

---

## 📚 Documentation

- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Guide de debugging détaillé
- [STATUS.md](../STATUS.md) - État du projet et roadmap

---

## 🚀 Roadmap

### Phase 1 : Infrastructure ✅
- [x] Architecture agent-based
- [x] CoinGecko Agent (20 cryptos)
- [x] Spark Consumer
- [x] Pipeline Kafka → InfluxDB
- [x] Dashboards Grafana basiques

### Phase 2 : Agents ✅/🔄
- [x] Fear & Greed Index
- [ ] Binance WebSocket (temps réel)
- [ ] CoinMarketCap (validation croisée)

### Phase 3 : Production 📋
- [ ] Docker Compose complet (agents inclus)
- [ ] Tests unitaires (pytest)
- [ ] CI/CD (GitHub Actions)
- [ ] Health checks & Alerting

---

## 📄 Licence

MIT

## 👤 Auteur

**Elom Okoumassoun**  
GitHub: [@elomokm](https://github.com/elomokm)
