# 🧪 Guide Complet - Tester le Projet de A à Z

## 📋 Prérequis

### Vérifier que tout est installé
```bash
# Python 3.12+
python3 --version

# Docker
docker --version
docker-compose --version

# Java (pour Spark)
java -version
```

---

## 🚀 Étape 1 : Démarrer l'Infrastructure Docker

### 1.1 Stopper tout ce qui tourne (si nécessaire)
```bash
cd /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring

# Stopper et nettoyer
docker-compose down -v
```

### 1.2 Démarrer les services
```bash
# Lancer tous les conteneurs
docker-compose up -d

# Vérifier que tout tourne
docker ps
```

**Sortie attendue :** 4 conteneurs actifs
```
CONTAINER ID   IMAGE                    STATUS
abc123         kafka                    Up
def456         zookeeper                Up
ghi789         influxdb:2.7             Up
jkl012         grafana/grafana          Up
```

### 1.3 Vérifier les logs (optionnel)
```bash
# Logs Kafka
docker logs kafka --tail 20

# Logs InfluxDB
docker logs influxdb --tail 20

# Logs Grafana
docker logs grafana --tail 20
```

---

## 🔧 Étape 2 : Activer l'Environnement Python

```bash
cd /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring

# Activer le virtualenv
source .venv/bin/activate

# Vérifier les packages installés
pip list | grep -E "kafka|influx|spark|python-dotenv"
```

**Packages attendus :**
```
kafka-python         2.0.2
influxdb-client      1.43.0
pyspark              3.4.0
python-dotenv        1.0.1
```

---

## 📊 Étape 3 : Tester les Agents (Producteurs Kafka)

### 3.1 Lancer l'Agent CoinGecko (Terminal 1)

```bash
# Dans le virtualenv activé
python run_coingecko_agent.py
```

**Sortie attendue :**
```
============================================================
🚀 CoinGecko Agent - Collecte prix et métadonnées
============================================================
✅ [CoinGeckoAgent] Connecté à Kafka (localhost:9092)

📊 [CoinGeckoAgent] Itération #1 - 15:23:45
✅ [CoinGeckoAgent] 20 cryptos récupérées
✅ [CoinGeckoAgent] 20 messages envoyés à Kafka
```

**➡️ Laisser tourner en arrière-plan**

---

### 3.2 Lancer l'Agent CoinMarketCap (Terminal 2)

**Ouvrir un NOUVEAU terminal**, puis :

```bash
cd /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring
source .venv/bin/activate

python run_coinmarketcap_agent.py
```

**Sortie attendue :**
```
============================================================
🚀 CoinMarketCap Agent - Source Alternative + Validation
============================================================
✅ CMC_API_KEY configurée: 82f293d6...ef23
⏱️  Intervalle de polling: 120s

✅ [CoinMarketCapAgent] Connecté à Kafka (localhost:9092)

📊 [CoinMarketCapAgent] Itération #1 - 15:24:00
✅ [CoinMarketCapAgent] 20 cryptos récupérées
✅ [CoinMarketCapAgent] 20 messages envoyés à Kafka
```

**➡️ Laisser tourner en arrière-plan**

---

### 3.3 Vérifier que les Messages Arrivent dans Kafka (Terminal 3)

**Ouvrir un NOUVEAU terminal**, puis :

```bash
# Lister les topics Kafka
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

**Topics attendus :**
```
crypto-prices
crypto-market-sentiment
```

**Consommer quelques messages du topic :**
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto-prices \
  --from-beginning \
  --max-messages 5
```

**Sortie attendue (JSON) :**
```json
{"source":"coingecko","crypto_id":"bitcoin","symbol":"BTC","price_usd":100234.56,...}
{"source":"coinmarketcap","crypto_id":"bitcoin","symbol":"BTC","price_usd":100189.12,...}
```

---

## 🔥 Étape 4 : Lancer le Consumer Spark (Terminal 4)

**Ouvrir un NOUVEAU terminal**, puis :

```bash
cd /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring
source .venv/bin/activate

# Lancer le consumer Spark
python consumer_prices.py
```

**Sortie attendue :**
```
============================================================
🔥 SPARK CONSUMER : Kafka → InfluxDB
============================================================
✅ InfluxDB configuré: http://localhost:8086
📊 Bucket: crypto-data | Org: crypto-org

[Spark logs...]
Writing batch to InfluxDB: 20 records
✅ Batch written successfully to InfluxDB
```

**➡️ Laisser tourner en arrière-plan**

---

## 📈 Étape 5 : Vérifier les Données dans InfluxDB

### 5.1 Via CLI (Terminal 5)

**Ouvrir un NOUVEAU terminal**, puis :

```bash
# Compter les messages par source
docker exec -it influxdb influx query '
from(bucket: "crypto-data")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_measurement"] == "crypto_market")
  |> filter(fn: (r) => r["_field"] == "price_usd")
  |> group(columns: ["source"])
  |> count()
'
```

**Sortie attendue :**
```
source          | _value
----------------|--------
coingecko       |    120
coinmarketcap   |     60
```

### 5.2 Via UI (Navigateur)

**Ouvrir dans un navigateur :**
👉 http://localhost:8086

**Credentials :**
- Username: `admin`
- Password: `adminpassword`

**Dans Data Explorer :**
1. Bucket : `crypto-data`
2. Measurement : `crypto_market`
3. Field : `price_usd`
4. Filter : `source` = `coingecko` ou `coinmarketcap`

---

## 📊 Étape 6 : Vérifier Grafana

### 6.1 Accéder à Grafana

**Ouvrir dans un navigateur :**
👉 http://localhost:3000

**Credentials :**
- Username: `admin`
- Password: `admin` (changer au premier login)

### 6.2 Vérifier le Dashboard

**Navigation :**
1. Menu (☰) → Dashboards
2. Cliquer sur **"Crypto Live Prices"**

**Panels attendus :**
- ✅ Total Market Cap
- ✅ Bitcoin Price (BTC)
- ✅ Total 24h Volume
- ✅ Top 3 Crypto Prices
- ✅ Top Movers (bar gauge)
- ✅ Market Overview (table)

**Si "No Data" :**
- Attendre 2-3 minutes que les agents collectent les données
- Vérifier le time range (en haut à droite : "Last 15 minutes")

---

## 🔍 Étape 7 : Validation Croisée (Terminal 6)

**Ouvrir un NOUVEAU terminal**, puis :

```bash
cd /Users/elomokoumassoun/Epitech/T-901-DAT-cryptoviz/crypto-monitoring
source .venv/bin/activate

# Analyser les divergences pendant 60 secondes
python cross_validation.py 60
```

**Sortie attendue :**
```
📊 VALIDATION CROISÉE : CoinGecko vs CoinMarketCap
================================================================
⏱️  Durée d'analyse: 60s
📡 Topic Kafka: crypto-prices

🔍 Écoute en cours...
------------------------------------------------------------------
[coingecko     ] BTC    = $   100,234.56
[coinmarketcap ] BTC    = $   100,189.12

✅ BTC - Divergence: 0.05%
   CoinGecko     : $100,234.56
   CoinMarketCap : $100,189.12
   Différence    : $45.44

[coingecko     ] ETH    = $     3,456.78
[coinmarketcap ] ETH    = $     3,451.23

✅ ETH - Divergence: 0.16%
```

**Si divergence > 5% :**
```
⚠️  SHIB - Divergence: 7.50%
   CoinGecko     : $0.00001234
   CoinMarketCap : $0.00001327
   Différence    : $0.00000093
```

---

## 🎯 Étape 8 : Résumé des Terminaux Actifs

**Après tous les tests, vous devriez avoir :**

| Terminal | Commande | État |
|----------|----------|------|
| Terminal 1 | `python run_coingecko_agent.py` | ✅ Running (60s poll) |
| Terminal 2 | `python run_coinmarketcap_agent.py` | ✅ Running (120s poll) |
| Terminal 3 | *(fermé après vérification Kafka)* | ⏸️ Fermé |
| Terminal 4 | `python consumer_prices.py` | ✅ Running (Spark) |
| Terminal 5 | *(fermé après vérification InfluxDB)* | ⏸️ Fermé |
| Terminal 6 | `python cross_validation.py 60` | ⏸️ Fermé (test ponctuel) |

---

## 🧪 Tests Fonctionnels Complets

### Test 1 : Pipeline End-to-End ✅

**But :** Vérifier que les données circulent de bout en bout

```bash
# 1. Agent envoie à Kafka
python run_coingecko_agent.py  # Terminal 1

# 2. Consumer lit de Kafka et écrit dans InfluxDB
python consumer_prices.py      # Terminal 4

# 3. Vérifier dans InfluxDB
docker exec -it influxdb influx query '
from(bucket: "crypto-data")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_field"] == "price_usd")
  |> limit(n: 5)
'
```

**✅ Succès si :** Vous voyez les données des dernières minutes

---

### Test 2 : Validation Croisée ✅

**But :** Comparer les prix des deux sources

```bash
# Lancer les deux agents
python run_coingecko_agent.py      # Terminal 1
python run_coinmarketcap_agent.py  # Terminal 2

# Analyser
python cross_validation.py 60      # Terminal 6
```

**✅ Succès si :** Divergence < 5% pour la plupart des cryptos

---

### Test 3 : Grafana Visualisation ✅

**But :** Voir les données en temps réel

1. **Ouvrir** http://localhost:3000
2. **Dashboard** → "Crypto Live Prices"
3. **Vérifier** que les graphiques se remplissent

**✅ Succès si :** Panels montrent des données et se rafraîchissent

---

### Test 4 : Détection d'Anomalies ✅

**But :** Vérifier que le système détecte les prix aberrants

```bash
# Regarder les logs de l'agent CoinMarketCap
# Dans Terminal 2, chercher les lignes :
⚠️  [CoinMarketCapAgent] ANOMALIE BTC: 100000.00 → 140000.00 (40.0%)
```

**✅ Succès si :** Flag `anomaly_detected=true` dans les messages

---

## 🐛 Troubleshooting

### Problème : "Connection refused to Kafka"

**Solution :**
```bash
# Vérifier que Kafka tourne
docker ps | grep kafka

# Redémarrer si nécessaire
docker-compose restart kafka zookeeper
```

---

### Problème : "InfluxDB write failed"

**Solution :**
```bash
# Vérifier le token dans .env
cat .env | grep INFLUX_TOKEN

# Vérifier la connexion
docker exec -it influxdb influx ping
```

---

### Problème : "No data in Grafana"

**Solutions :**
1. Vérifier le time range (Last 15 minutes minimum)
2. Attendre 2-3 minutes que les agents collectent
3. Vérifier que le consumer Spark tourne
4. Vérifier InfluxDB via CLI

```bash
docker exec -it influxdb influx query '
from(bucket: "crypto-data")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_field"] == "price_usd")
  |> count()
'
```

---

### Problème : "CMC API rate limit exceeded"

**Solution :**
```bash
# Dans .env, augmenter l'intervalle
COINMARKETCAP_POLL_INTERVAL=180  # 3 minutes au lieu de 2
```

---

## 📊 Métriques de Validation

### Pipeline Santé Check

Exécuter ce script pour vérifier tout le pipeline :

```bash
#!/bin/bash
echo "🔍 HEALTH CHECK COMPLET"
echo "===================="

# 1. Docker
echo "1️⃣ Docker Services..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "kafka|zookeeper|influx|grafana"

# 2. Kafka Topics
echo -e "\n2️⃣ Kafka Topics..."
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# 3. InfluxDB Data
echo -e "\n3️⃣ InfluxDB Records (last 10min)..."
docker exec -it influxdb influx query '
from(bucket: "crypto-data")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_field"] == "price_usd")
  |> group(columns: ["source"])
  |> count()
'

# 4. Python Processes
echo -e "\n4️⃣ Python Agents..."
ps aux | grep -E "coingecko|coinmarketcap|consumer_prices" | grep -v grep

echo -e "\n✅ Health Check Terminé"
```

---

## 🎉 Checklist Finale

Avant de passer à la phase suivante, vérifier :

- [ ] ✅ Docker services actifs (kafka, influxdb, grafana)
- [ ] ✅ Agent CoinGecko envoie des messages
- [ ] ✅ Agent CoinMarketCap envoie des messages
- [ ] ✅ Consumer Spark écrit dans InfluxDB
- [ ] ✅ Données visibles dans InfluxDB CLI
- [ ] ✅ Dashboard Grafana affiche les données
- [ ] ✅ Validation croisée montre divergence < 5%
- [ ] ✅ Aucune erreur dans les logs

---

## 🚀 Prochaines Étapes

Si tous les tests passent :

1. **Phase 1.2** : Data Quality Framework (schema validation)
2. **Phase 1.3** : Binance WebSocket Agent (temps réel)
3. **Phase 2** : Sécurité Kafka + WebApp

**📚 Documentation :**
- [ROADMAP.md](../ROADMAP.md) - Plan complet
- [CROSS_VALIDATION.md](CROSS_VALIDATION.md) - Validation multi-sources
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Résolution problèmes

---

**🎯 Bon test ! 🚀**
