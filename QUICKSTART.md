# CryptoViz - Guide de Démarrage Rapide ⚡

Ce guide vous permet de lancer CryptoViz en **moins de 10 minutes**.

---

## ✅ Prérequis

- [x] **Docker Desktop** installé et démarré
- [x] **Python 3.12+** installé
- [x] **Node.js 18+** installé (pour le frontend)
- [x] **Terminal** (bash/zsh)

---

## 🚀 Démarrage en 5 Étapes

### 1️⃣ Cloner et Configurer (2 min)

```bash
# Cloner le repo
git clone <your-repo-url>
cd cryptoviz

# Créer l'environnement Python
cd crypto-monitoring
python3 -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2️⃣ Configuration InfluxDB et API Keys (1 min)

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec votre éditeur préféré
nano .env  # ou vim, code, etc.
```

**Modifier ces variables**:
```bash
# InfluxDB Token (sera généré au premier lancement)
INFLUX_TOKEN=your_token_here  # Laisser vide pour l'instant

# CoinMarketCap API Key (obtenir gratuitement sur https://coinmarketcap.com/api/)
CMC_API_KEY=your_api_key_here
```

💡 **Note**: Le token InfluxDB sera généré automatiquement au premier lancement.

### 3️⃣ Démarrer l'Infrastructure (3 min)

```bash
# Démarrer Kafka, InfluxDB, Grafana
docker-compose up -d

# Attendre que tout soit prêt (~30 secondes)
sleep 30

# Vérifier que tout est up
docker-compose ps
```

**Vous devriez voir**:
```
NAME                    STATUS
kafka                   Up
zookeeper               Up
influxdb                Up
grafana                 Up
```

### 4️⃣ Obtenir le Token InfluxDB (1 min)

Première fois uniquement:

1. Ouvrir http://localhost:8086
2. Créer un compte:
   - Username: `admin`
   - Password: `password123` (changez en production!)
   - Organization: `crypto-org`
   - Bucket: `crypto-data`
3. Aller dans **API Tokens** (menu gauche)
4. Copier le token
5. Mettre à jour `.env`:
   ```bash
   INFLUX_TOKEN=<votre-token-copié>
   ```

### 5️⃣ Lancer Tout Automatiquement (1 min)

```bash
# Utiliser le script magique ✨
./start_all.sh
```

Ce script va:
- ✅ Vérifier Docker
- ✅ Lancer 4 **Producers** (CoinGecko, CMC, News, Fear&Greed)
- ✅ Lancer 4 **Consumers** (Prices, News, Analytics, Anomalies)
- ✅ Ouvrir 8 fenêtres de terminal automatiquement

---

## 🌐 Lancer le Frontend (2 min)

Dans **2 nouveaux terminaux**:

### Terminal 1 - FastAPI Backend

```bash
cd crypto-app/api
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 - Next.js Frontend

```bash
cd crypto-app/web
npm install  # Première fois uniquement
npm run dev
```

---

## 🎉 Accéder aux Dashboards

Ouvrez votre navigateur:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Web App** | http://localhost:3001 | Aucun |
| **API Docs** | http://localhost:8000/docs | Aucun |
| **Grafana** | http://localhost:3000 | admin/admin |
| **InfluxDB** | http://localhost:8086 | (créés à l'étape 4) |

---

## 📊 Vérifier que Tout Fonctionne

### 1. Données dans InfluxDB

```bash
# Ouvrir http://localhost:8086
# Data Explorer → Sélectionner bucket "crypto-data"
# Query Builder → Measurement "crypto_market"
# Vous devriez voir des données après 1-2 minutes
```

### 2. API Retourne des Données

```bash
# Test l'API
curl http://localhost:8000/coins?limit=5

# Devrait retourner JSON avec 5 cryptos
```

### 3. Frontend Affiche les Cryptos

- Ouvrir http://localhost:3001
- Vérifier que la table affiche les cryptos
- Vérifier que les news s'affichent (après 5 min)

---

## 🐛 Troubleshooting

### Problème: Docker services ne démarrent pas

**Solution**:
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

### Problème: "Cannot connect to Kafka"

**Solution**:
```bash
# Vérifier que Kafka est up
docker-compose ps kafka

# Redémarrer si nécessaire
docker-compose restart kafka
```

### Problème: "InfluxDB authentication failed"

**Solution**:
1. Vérifier que `INFLUX_TOKEN` dans `.env` est correct
2. Regénérer le token dans l'UI InfluxDB
3. Redémarrer les consumers

### Problème: Pas de données après 5 minutes

**Solution**:
```bash
# Vérifier les logs des agents
# Dans le terminal de CoinGeckoAgent, vous devriez voir:
# ✅ [CoinGeckoAgent] Envoyé vers crypto-prices: {...}

# Vérifier les logs des consumers
# Dans le terminal de consumer_prices, vous devriez voir:
# ✅ Batch 0: 20 cryptos écrits dans InfluxDB
```

### Problème: Web app ne se connecte pas à l'API

**Solution**:
```bash
# Vérifier que l'API tourne
curl http://localhost:8000/health

# Devrait retourner: {"status":"ok"}
```

---

## 🛑 Arrêter Tout

### Arrêt Gracieux

1. Fermer toutes les fenêtres de terminal (Ctrl+C dans chacune)
2. Arrêter Docker:
   ```bash
   docker-compose down
   ```

### Arrêt Complet (avec suppression des données)

```bash
docker-compose down -v  # ⚠️ Supprime les volumes InfluxDB!
```

---

## 📚 Prochaines Étapes

Maintenant que tout fonctionne, explorez:

1. **Grafana Dashboards**: http://localhost:3000
   - Dashboard "Crypto Core Metrics"
   - Dashboard "Multi-Source Comparisons"

2. **API Interactive Docs**: http://localhost:8000/docs
   - Tester tous les endpoints
   - Voir les schémas de réponse

3. **InfluxDB Data Explorer**: http://localhost:8086
   - Créer vos propres requêtes Flux
   - Visualiser les analytics

4. **Architecture**: Lire [ARCHITECTURE.md](ARCHITECTURE.md)
   - Comprendre le flux de données
   - Justification des choix techniques

---

## 🆘 Besoin d'Aide?

- **Documentation**: Lire [README.md](README.md)
- **Architecture**: Lire [ARCHITECTURE.md](ARCHITECTURE.md)
- **Changelog**: Lire [CHANGELOG.md](CHANGELOG.md)
- **Issues**: Ouvrir une issue sur GitHub

---

**Bon développement! 🚀**
