# CryptoViz — README complet

Dernière mise à jour : août 2025

## 1) Vue d’ensemble

CryptoViz est une application de visualisation crypto en 3 parties :

* **Frontend** : React + Vite (routing, dashboard, pages News & Portfolio).
* **API** : FastAPI, expose des endpoints pour bougies 1 min (Timescale), top marché, actualités.
* **Ingestion** : un **scraper** qui récupère des bougies **1 minute** depuis **Coinbase Exchange** (HTTP public) et les insère dans Postgres/Timescale. Il publie aussi le dernier prix sur Redis (Pub/Sub).

L’ensemble est orchestré par **Docker Compose** :

| Service  | Image / Build                             | Port hôte | Rôle                                  |
| -------- | ----------------------------------------- | --------- | ------------------------------------- |
| postgres | timescale/timescaledb\:latest-pg16        | 5432      | Stockage TimescaleDB (bougies, news). |
| redis    | redis:7                                   | 6379      | Cache + Pub/Sub temps réel.           |
| api      | build `services/api` (FastAPI + Uvicorn)  | 8000      | Endpoints HTTP.                       |
| web      | build `web` (Vite + React)                | 5173      | Frontend SPA.                         |
| scraper  | build `services/scraper` (Python + httpx) | —         | Ingestion bougies 1 min Coinbase.     |

### État actuel

* **OK** : Postgres/Timescale en place, table `candles` fonctionnelle (hypertable).
* **OK** : API endpoints `/market/top`, `/timeseries/candles`, `/news`, `/news/volume` (ce dernier renvoie des données si la vue continue existe).
* **OK** : Front **Dashboard** connecté à `/market/top` (affiche les symboles pour lesquels des bougies existent).
* **OK** : **Scraper** opérationnel via Coinbase (contourne les erreurs 451 de Binance en France). Ingestion multi-symboles via variable d’environnement `SYMBOLS`.
* **Optionnel** : Mode **DISCOVER\_ALL** (découverte auto de toutes les paires USD/USDC/EUR côté scraper). **À implémenter** dans le code si souhaité (le Compose est déjà prêt, voir § 6.3).
* **À faire** : Page News branchée à l’API, Portfolio (tables users/trades), graphiques de volumes/sentiments, WebSocket côté front.

---

## 2) Arborescence

```
cryptoviz/
├─ infra/
│  └─ docker-compose.yml
├─ services/
│  ├─ api/
│  │  ├─ Dockerfile
│  │  ├─ requirements.txt
│  │  └─ main.py
│  └─ scraper/
│     ├─ Dockerfile
│     ├─ requirements.txt
│     └─ main.py
└─ web/
   ├─ vite.config.ts
   ├─ index.html
   └─ src/
      ├─ main.tsx
      ├─ App.tsx
      └─ pages/
         ├─ Dashboard.tsx
         ├─ News.tsx
         └─ Portfolio.tsx
```

---

## 3) Démarrage rapide

Depuis `infra/` :

```bash
# Build & run
docker compose up -d --build

# Suivre les logs clés
docker compose logs -f api
docker compose logs -f scraper

# Frontend
# Ouvre http://localhost:5173/
```

Tests rapides :

```bash
# L’API doit répondre
curl -sS 'http://localhost:8000/market/top?limit=5' | jq .

# Données bougies pour un symbole
curl -sS 'http://localhost:8000/timeseries/candles?symbol=BTCUSDT&tf=1m' | head

# Comptage en base
docker compose exec postgres psql -U postgres -d cryptoviz -c "select symbol, count(*) from candles group by symbol order by symbol;"
```

**Après redémarrage du PC** :

```bash
cd infra
docker compose up -d
```

---

## 4) Configuration & variables d’environnement

### 4.1 API (FastAPI)

* `POSTGRES_DSN=postgresql://postgres:postgres@postgres:5432/cryptoviz`
* `REDIS_URL=redis://redis:6379/0`
* CORS côté FastAPI : autoriser `http://localhost:5173` dans `main.py`.

### 4.2 Frontend (Vite)

* `VITE_API_URL=http://localhost:8000`
* Volumes dans Compose :

  * `../web:/app:delegated` (pour travailler en live)
  * `/app/node_modules` (garde les deps du conteneur)
* `vite.config.ts` : plugin React + `server.hmr.clientPort=5173`.

### 4.3 Scraper (Coinbase)

* **Mode liste** (actuel) : `SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,...`

  * Le code mappe automatiquement `XXXUSDT` → `XXX-USD` (ou `-USDC`/`-EUR` si dispo).
* **Paramètres de rythme** :

  * `GRANULARITY_SECONDS=60` (bougies 1 minute)
  * `SLEEP_BETWEEN_SYMBOLS=0.25` (délai entre deux requêtes)
  * `LOOP_SLEEP=5` (délai entre deux boucles complètes)
* **Option découverte** (si implémentée dans le code) :

  * `DISCOVER_ALL=1`
  * `QUOTE_FILTER=USD,USDC` (ajouter `EUR` si souhaité)
  * `TARGET_RPS=8` (vise ≤ 8 req/s pour rester sous les limites publiques)

---

## 5) Modèle de données

### 5.1 Bougies (Timescale)

```sql
CREATE TABLE IF NOT EXISTS candles (
  symbol  TEXT NOT NULL,
  ts      TIMESTAMPTZ NOT NULL,
  open    NUMERIC NOT NULL,
  high    NUMERIC NOT NULL,
  low     NUMERIC NOT NULL,
  close   NUMERIC NOT NULL,
  volume  NUMERIC NOT NULL,
  PRIMARY KEY(symbol, ts)
);
SELECT create_hypertable('candles','ts', if_not_exists=>TRUE);
CREATE INDEX IF NOT EXISTS ix_candles_symbol_ts ON candles(symbol, ts DESC);
```

* `symbol` : garde le format interne (ex : `BTCUSDT`), même si la pair source est `BTC-USD` côté Coinbase.

### 5.2 Articles d’actualités (optionnel, déjà défini)

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS news_articles (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ts        TIMESTAMPTZ NOT NULL,
  source    TEXT NOT NULL,
  url       TEXT NOT NULL,
  url_hash  TEXT GENERATED ALWAYS AS (encode(digest(url, 'sha256'), 'hex')) STORED,
  title     TEXT,
  summary   TEXT,
  content   TEXT,
  lang      TEXT,
  symbols   TEXT[] DEFAULT '{}',
  sentiment REAL,
  raw       JSONB
);
CREATE UNIQUE INDEX IF NOT EXISTS news_articles_url_uniq ON news_articles(url);
SELECT create_hypertable('news_articles','ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_news_articles_ts ON news_articles(ts DESC);
CREATE INDEX IF NOT EXISTS ix_news_articles_symbols ON news_articles USING GIN(symbols);

-- Vue continue (si tu l’utilises)
-- CREATE MATERIALIZED VIEW mv_news_volume_1m WITH (timescaledb.continuous) AS
-- SELECT time_bucket('1 minute', ts) AS bucket, source, COUNT(*)::bigint AS volume
-- FROM news_articles GROUP BY bucket, source;
-- add_continuous_aggregate_policy(...)
```

---

## 6) Endpoints API

### 6.1 `GET /market/top?limit=20`

Renvoie le dernier prix par symbole + variation 24h.

Exemple :

```bash
curl -s 'http://localhost:8000/market/top?limit=10' | jq .
```

> Remarque : la variation 24h nécessite au moins \~24 heures d’historique.

### 6.2 `GET /timeseries/candles?symbol=BTCUSDT&tf=1m&start=...&end=...`

* `tf`: `1m`, `5m`, `15m`, `1h`, `1d` (agrégation via `time_bucket` côté Timescale si tf ≠ `1m`).

### 6.3 `GET /news?symbol=BTC&limit=50`

* Filtre par symbole présent dans `symbols[]` (si `news_articles` alimentée).

### 6.4 `GET /news/volume`

* Lit la vue continue `mv_news_volume_1m` si elle existe (sinon liste vide).

### 6.5 `WS /ws/quotes`

* Redis Pub/Sub : envoie les derniers prix publiés par le scraper (`{"symbol":"BTCUSDT","price":...,"ts":...}`).

---

## 7) Frontend

* **Routing** via `react-router-dom` : `/` (Dashboard), `/news`, `/portfolio`.
* **Icônes** : `lucide-react`.
* **HMR** : activé via Vite (veille à installer les deps **dans le conteneur** si tu montes le code en volume).

Installation des deps dans le conteneur `web` :

```bash
docker compose exec web sh -lc 'npm i react-router-dom lucide-react && npm i -D @vitejs/plugin-react'
docker compose restart web
```

---

## 8) Dépannage (FAQ)

### 8.1 Le front affiche « Failed to fetch »

* Vérifie que l’API répond : `http://localhost:8000/docs`.
* Assure `VITE_API_URL=http://localhost:8000` (et redémarre `web`).
* CORS côté FastAPI : autoriser `http://localhost:5173`.

### 8.2 `react-router-dom`/`lucide-react` introuvables

* Installe **dans le conteneur** : `npm i react-router-dom lucide-react` puis redémarre.

### 8.3 Dashboard n’affiche que BTC/ETH

* Normal si le scraper n’ingère que ces symboles. Ajoute des tickers dans `SYMBOLS` **ou** active la découverte (si implémentée).

### 8.4 Binance 451 (France)

* Le scraper utilise **Coinbase** pour éviter le 451. Si tu remets Binance, tu auras à nouveau le blocage légal.

### 8.5 `curl` échoue avec zsh (`no matches found`)

* Cite l’URL : `curl -sS 'http://localhost:8000/market/top?limit=5'`.

### 8.6 HMR ne réagit pas

* Vérifie les volumes, `CHOKIDAR_USEPOLLING=true`, et `vite.config.ts`.

---

## 9) Roadmap

### 9.1 Court terme

* Page **News** branchée à `/news` + filtres (symbol, période).
* Graphiques (Volume actus, Sentiment, Prix) via agrégation Timescale (bucket 1m/5m/1h).
* WebSocket côté front (affichage prix live via `/ws/quotes`).

### 9.2 Moyen terme

* **Portfolio** : tables `users`, `trades`, endpoints POST/GET, calcul PnL.
* Fallback variation 24h (ex : 1h/4h) tant que l’historique n’est pas suffisant.
* Ingestion actualités (sources publiques), scoring de sentiment (modèle léger), vues continues.

### 9.3 Long terme

* Auth (sessions/JWT), profils utilisateurs.
* Alerting (seuils prix/volume), backtests simples.
* Déploiement cloud (compose → Swarm/K8s), monitoring (Prometheus/Grafana).

---

## 10) Sécurité & bonnes pratiques

* **Secrets** : ne jamais committer de clés/API, mots de passe, DSN sensibles.
* **Postgres** : changer `postgres/postgres` en prod, restreindre l’exposition du port.
* **Rate limiting** : respecter les limites publiques Coinbase (viser ≤ 8 req/s), ajouter un backoff 429.
* **Logs** : ne pas logger de données personnelles.

---

## 11) Annexes

### 11.1 Commandes utiles

```bash
# rebuild ciblé
docker compose build api scraper web

# restart ciblé
docker compose restart web api scraper

# inspecter un fichier dans le conteneur web
docker compose exec web sh -lc 'wc -l /app/src/App.tsx && head -n 5 /app/src/App.tsx'

# top 5 symboles par récence
docker compose exec postgres psql -U postgres -d cryptoviz -c \
  "select symbol, max(ts) as last from candles group by symbol order by last desc limit 5;"
```

---

## 12) Licence

Projet interne/étudiant. Définir une licence si publication.



##### RUN LE PROJET
# 1. Démarrer Colima (ou lancer Docker Desktop)
colima start --cpu 4 --memory 8 --arch x86_64

# 2. Vérifier le contexte Docker
docker context use colima   # ou "default" si Docker Desktop
docker info

# 3. Aller dans le dossier infra du projet
cd /chemin/vers/projet/infra

# 4. Builder et lancer
docker compose up --build
Backend : http://127.0.0.1:8000

Frontend : http://127.0.0.1:3000

Stopper : docker compose down







## Les plus performant 
## les moins performant
## Chart Graphique de la plus belle performance de la semaine