# 🚀 Quick Start - CoinMarketCap Agent

## Prérequis
- ✅ Infrastructure lancée (Kafka, InfluxDB, Grafana)
- ✅ Python virtualenv activé
- ✅ Agent CoinGecko fonctionnel

## Étape 1 : Obtenir une Clé API CoinMarketCap (2 minutes)

### 1. Créer un compte gratuit
👉 https://coinmarketcap.com/api/

### 2. Copier votre clé API
Après inscription, vous obtiendrez une clé format :
```
a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6
```

### 3. Ajouter dans `.env`
```bash
cd crypto-monitoring
nano .env
```

Ajouter cette ligne :
```bash
CMC_API_KEY=a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6
```

**⚠️ Important :** Ne jamais commit le `.env` !

---

## Étape 2 : Lancer l'Agent CoinMarketCap

```bash
# Vérifier que le virtualenv est actif
source .venv/bin/activate

# Lancer l'agent
python run_coinmarketcap_agent.py
```

**Sortie attendue :**
```
============================================================
🚀 CoinMarketCap Agent - Source Alternative + Validation
============================================================
✅ CMC_API_KEY configurée: a1b2c3d4...o5p6
⏱️  Intervalle de polling: 120s

✅ [CoinMarketCapAgent] Connecté à Kafka (localhost:9092)

📊 [CoinMarketCapAgent] Itération #1 - 14:30:45
✅ [CoinMarketCapAgent] 20 cryptos récupérées
✅ [CoinMarketCapAgent] 20 messages envoyés à Kafka
```

---

## Étape 3 : Validation Croisée (Optionnel)

Dans un **nouveau terminal** :

```bash
cd crypto-monitoring
source .venv/bin/activate

# Analyser pendant 60 secondes
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
```

---

## Étape 4 : Vérifier InfluxDB

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

**Résultat attendu :**
```
source          | _value
----------------|-------
coingecko       |    120
coinmarketcap   |     60
```

---

## Étape 5 : Grafana Dashboard (Mise à jour)

### Ouvrir Grafana
👉 http://localhost:3000

### Créer un nouveau panel "Source Validation"

**Query Flux :**
```flux
from(bucket: "crypto-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "crypto_market")
  |> filter(fn: (r) => r["_field"] == "price_usd")
  |> filter(fn: (r) => r["symbol"] == "BTC")
  |> group(columns: ["source"])
```

**Type de visualization :** Time series (2 lignes)
- 🟢 CoinGecko (vert)
- 🔵 CoinMarketCap (bleu)

---

## 🐛 Troubleshooting

### Erreur : "CMC_API_KEY non définie"

**Solution :**
```bash
# Vérifier que la clé est dans .env
cat .env | grep CMC_API_KEY

# Si vide, ajouter la clé
echo "CMC_API_KEY=votre_cle_ici" >> .env

# Relancer l'agent
python run_coinmarketcap_agent.py
```

### Erreur : "API rate limit exceeded"

**Symptôme :** HTTP 429

**Solution :** Augmenter l'intervalle de polling
```bash
# Dans .env
COINMARKETCAP_POLL_INTERVAL=180  # 3 minutes
```

### Pas de messages dans Kafka

**Vérifier que Kafka tourne :**
```bash
docker ps | grep kafka
```

**Vérifier le topic :**
```bash
docker exec -it kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list
```

---

## ✅ Checklist de Validation

- [ ] Clé API CoinMarketCap configurée dans `.env`
- [ ] Agent CoinMarketCap lance sans erreur
- [ ] Messages visibles dans Kafka (via cross_validation.py)
- [ ] Données écrites dans InfluxDB
- [ ] Dashboard Grafana affiche les deux sources

---

## 🎯 Prochaines Étapes

1. **Data Quality Framework** (demain)
   - Schema validation
   - Consumer de validation croisée
   - Dead Letter Queue

2. **Binance WebSocket Agent** (après-demain)
   - Temps réel
   - Nouveau consumer Spark

3. **WebApp Next.js** (semaine prochaine)
   - FastAPI backend
   - Frontend moderne

---

📚 **Documentation complète :** Voir [ROADMAP.md](ROADMAP.md)

🔄 **Validation croisée :** Voir [CROSS_VALIDATION.md](crypto-monitoring/CROSS_VALIDATION.md)
