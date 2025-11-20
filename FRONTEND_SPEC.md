# CryptoViz - Spécification Frontend

Documentation complète pour le développement du frontend web CryptoViz.

---

## Table des matières

1. [Architecture Globale](#1-architecture-globale)
2. [API Backend - Endpoints](#2-api-backend---endpoints)
3. [Modèles de Données](#3-modèles-de-données)
4. [Frontend Actuel](#4-frontend-actuel)
5. [Données InfluxDB](#5-données-influxdb)
6. [Configuration](#6-configuration)
7. [Fonctionnalités Attendues](#7-fonctionnalités-attendues)
8. [Guide Rapide](#8-guide-rapide)

---

## 1. Architecture Globale

### Flux de données

```
[Sources de données]     [Message Broker]    [Stockage]     [API]      [Frontend]
CoinGecko API      -->   Kafka           --> InfluxDB   --> FastAPI --> Next.js
CoinMarketCap API  -->   (crypto-prices)     (crypto-data)   :8000      :3001
News RSS Feeds     -->   (crypto-news)
Fear & Greed API   -->   (crypto-market-sentiment)
```

### Ports utilisés

| Service | Port | URL |
|---------|------|-----|
| **API FastAPI** | 8000 | `http://localhost:8000` |
| **Web Next.js** | 3001 | `http://localhost:3001` |
| **Grafana** | 3000 | `http://localhost:3000` |
| **InfluxDB** | 8086 | `http://localhost:8086` |
| **Kafka** | 9092 | `localhost:9092` |

### Topics Kafka

- `crypto-prices` - Données de marché (prix, volume, market cap)
- `crypto-news` - Actualités crypto
- `crypto-market-sentiment` - Fear & Greed Index

---

## 2. API Backend - Endpoints

### Base URL

```
http://localhost:8000
```

Variable d'environnement frontend: `NEXT_PUBLIC_API_BASE`

---

### Health Check

#### GET `/health`

Statut de l'API.

**Réponse:**
```json
{
  "status": "ok"
}
```

#### GET `/health/influx`

Vérification connexion InfluxDB.

**Réponse:**
```json
{
  "url": "http://localhost:8086",
  "ping": "ok",
  "auth": "ok"
}
```

---

### Coins (Cryptomonnaies)

#### GET `/coins`

Liste les cryptomonnaies avec leur snapshot le plus récent.

**Paramètres Query:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Nombre de résultats (1-250) |
| `page` | int | 1 | Numéro de page |
| `order` | string | "market_cap_desc" | Tri (voir options ci-dessous) |
| `ids` | string | null | IDs comma-separated (ex: "bitcoin,ethereum") |

**Options de tri (`order`):**
- `market_cap_desc` / `market_cap_asc`
- `price_desc` / `price_asc`
- `volume_desc` / `volume_asc`

**Réponse:** `Array<CoinSummary>`
```json
[
  {
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "price_usd": 67234.56,
    "market_cap": 1312000000000,
    "market_cap_rank": 1,
    "volume_24h": 28500000000,
    "change_1h": 0.45,
    "change_24h": 2.34,
    "change_7d": -1.23,
    "ath": 69000,
    "ath_change_pct": -2.56,
    "atl": 67.81,
    "atl_change_pct": 99102.45,
    "circulating_supply": 19500000,
    "total_supply": 21000000,
    "max_supply": 21000000,
    "last_updated": "2025-11-20T10:30:00Z",
    "sparkline_7d": null
  }
]
```

---

#### GET `/coins/{crypto_id}`

Détail d'une crypto spécifique.

**Paramètres Path:**
- `crypto_id`: string (ex: "bitcoin", "ethereum")

**Réponse:** `CoinSummary`

**Erreurs:**
- 404: Coin not found

---

#### GET `/coins/{crypto_id}/history`

Historique des prix pour une crypto.

**Paramètres Path:**
- `crypto_id`: string

**Paramètres Query:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `days` | int | 7 | Période (1-365 jours) |
| `interval` | string | "1h" | Intervalle temporel |

**Options d'intervalle:**
- `1m`, `5m`, `15m`, `30m` (minutes)
- `1h`, `2h`, `4h`, `12h` (heures)
- `1d` (jour)

**Réponse:** `CoinHistoryResponse`
```json
{
  "id": "bitcoin",
  "days": 7,
  "interval": "1h",
  "series": [
    {
      "time": "2025-11-13T10:00:00Z",
      "value": 65000.50
    },
    {
      "time": "2025-11-13T11:00:00Z",
      "value": 65234.75
    }
  ]
}
```

---

### Global Stats

#### GET `/global`

Statistiques globales du marché.

**Réponse:** `GlobalStats`
```json
{
  "total_market_cap": 2450000000000,
  "total_volume_24h": 89000000000,
  "market_cap_change_24h": 1.56,
  "count": 20
}
```

---

### Fear & Greed Index

#### GET `/fear-greed`

Indice de peur et d'avidité du marché (0-100).

**Réponse:**
```json
{
  "value": 65.0,
  "time": "2025-11-20T10:30:00Z",
  "source": "alternative.me",
  "measurement": "fear_greed"
}
```

**Interprétation:**
- 0-25: Extreme Fear
- 26-45: Fear
- 46-55: Neutral
- 56-75: Greed
- 76-100: Extreme Greed

**Erreurs:**
- 404: Fear & Greed index not available

---

### News (Actualités)

#### GET `/news`

Récupère les dernières actualités crypto.

**Paramètres Query:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 20 | Nombre d'articles (1-100) |
| `source` | string | null | Filtrer par source |
| `hours` | int | 24 | Articles des X dernières heures (1-168) |

**Sources disponibles:**
- `coindesk`
- `cointelegraph`

**Réponse:** `NewsResponse`
```json
{
  "count": 15,
  "news": [
    {
      "title": "Bitcoin Surges Past $67,000",
      "link": "https://coindesk.com/article/...",
      "published_date": "2025-11-20T09:30:00Z",
      "source": "coindesk",
      "description": "Bitcoin has reached new highs...",
      "image_url": "https://coindesk.com/images/..."
    }
  ]
}
```

---

#### GET `/news/sources`

Liste des sources d'actualités disponibles.

**Réponse:**
```json
{
  "sources": [
    {
      "id": "coindesk",
      "name": "CoinDesk",
      "url": "https://www.coindesk.com"
    },
    {
      "id": "cointelegraph",
      "name": "CoinTelegraph",
      "url": "https://cointelegraph.com"
    }
  ]
}
```

---

### Debug

#### GET `/debug/influx/summary`

Diagnostics des données InfluxDB.

**Paramètres Query:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `hours` | int | 6 | Fenêtre de temps (1-48h) |

**Réponse:**
```json
{
  "bucket": "crypto-data",
  "measurement": "crypto_market",
  "crypto_count": 20,
  "crypto_ids": ["bitcoin", "ethereum", "cardano"],
  "latest_timestamp_any": "2025-11-20T10:30:00Z",
  "total_points_last_hour": 1200,
  "hours_window": 6
}
```

---

## 3. Modèles de Données

### Types TypeScript

```typescript
// Prix/valeur dans le temps
export interface PricePoint {
  time: string;      // ISO 8601 datetime
  value: number;     // Prix en USD
}

// Résumé d'une cryptomonnaie
export interface CoinSummary {
  id: string;                        // "bitcoin"
  symbol: string;                    // "BTC"
  name: string;                      // "Bitcoin"
  price_usd: number;                 // 67234.56
  market_cap?: number;               // 1312000000000
  market_cap_rank?: number;          // 1
  volume_24h?: number;               // 28500000000
  change_1h?: number;                // 0.45 (%)
  change_24h?: number;               // 2.34 (%)
  change_7d?: number;                // -1.23 (%)
  ath?: number;                      // All-Time High
  ath_change_pct?: number;           // % depuis ATH
  atl?: number;                      // All-Time Low
  atl_change_pct?: number;           // % depuis ATL
  circulating_supply?: number;       // 19500000
  total_supply?: number;             // 21000000
  max_supply?: number;               // 21000000
  last_updated: string;              // ISO 8601 datetime
  sparkline_7d?: number[] | null;    // Points pour mini-graphique
}

// Stats globales du marché
export interface GlobalStats {
  total_market_cap: number;          // 2450000000000
  total_volume_24h: number;          // 89000000000
  market_cap_change_24h?: number;    // 1.56 (%)
  count: number;                     // Nombre de cryptos
}

// Historique d'une crypto
export interface CoinHistoryResponse {
  id: string;                        // "bitcoin"
  days: number;                      // 7
  interval: string;                  // "1h"
  series: PricePoint[];              // Array de points
}

// Article d'actualité
export interface NewsArticle {
  title: string;                     // Titre
  link: string;                      // URL de l'article
  published_date: string;            // ISO 8601 datetime
  source: string;                    // "coindesk" | "cointelegraph"
  description?: string;              // Résumé (max 500 chars)
  image_url?: string;                // URL de l'image
}

// Réponse liste d'actualités
export interface NewsResponse {
  count: number;                     // Nombre d'articles
  news: NewsArticle[];               // Liste d'articles
}

// Fear & Greed Index
export interface FearGreedResponse {
  value: number;                     // 0-100
  time: string;                      // ISO 8601 datetime
  source: string;                    // "alternative.me"
  measurement: string;               // "fear_greed"
}
```

---

## 4. Frontend Actuel

### Configuration Technique

| Technologie | Version | Usage |
|-------------|---------|-------|
| Next.js | 14.2.11 | Framework React (App Router) |
| React | 18.2.0 | UI Library |
| TypeScript | 5.3.3 | Typage statique |
| Tailwind CSS | 3.4.1 | Styling utilitaire |
| Recharts | 2.10.3 | Graphiques |

**Port:** 3001

### Structure des fichiers

```
crypto-app/web/
├── app/
│   ├── layout.tsx              # Layout principal avec fonts
│   ├── page.tsx                # Page d'accueil / Dashboard
│   ├── globals.css             # Styles globaux Tailwind
│   └── coin/
│       └── [id]/
│           └── page.tsx        # Page détail d'une crypto
├── components/
│   ├── CryptoTable.tsx         # Tableau des cryptos
│   ├── GlobalStatsCards.tsx    # Cartes stats globales
│   ├── Sparkline.tsx           # Mini-graphique SVG
│   ├── CoinHistoryClient.tsx   # Historique avec sélecteur
│   ├── NewsSection.tsx         # Section actualités
│   └── layout/
│       ├── Header.tsx          # Header avec recherche
│       ├── Sidebar.tsx         # Navigation latérale
│       └── RightPanel.tsx      # Panel droit
├── lib/
│   └── api.ts                  # Client API + Types
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### Client API existant

**Fichier:** `lib/api.ts`

```typescript
// Configuration
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// Fonctions disponibles
export async function getGlobal(): Promise<GlobalStats>
export async function getCoins(limit?: number, page?: number): Promise<CoinSummary[]>
export async function getCoin(id: string): Promise<CoinSummary>
export async function getCoinHistory(id: string, days: number, interval: string): Promise<CoinHistoryResponse>
export async function getNews(limit?: number, source?: string, hours?: number): Promise<NewsResponse>
```

### Composants existants

#### CryptoTable

Tableau principal des cryptos.

**Props:**
```typescript
interface CryptoTableProps {
  data: Array<{
    rank: number;
    id: string;
    symbol: string;
    name: string;
    price: number;
    change_24h: number;
    change_7d: number;
    volume_24h: number;
    market_cap: number;
  }>;
  loading: boolean;
}
```

**Fonctionnalités:**
- Colonnes: Rank, Name, Price, 24h%, 7d%, Volume, Market Cap
- Lien vers `/coin/{id}`
- Loading skeleton
- Responsive (colonnes cachées sur mobile)

#### GlobalStatsCards

3 cartes de statistiques globales.

**Props:**
```typescript
interface GlobalStatsCardsProps {
  stats: GlobalStats | null;
  loading: boolean;
}
```

**Affiche:**
- Total Market Cap
- Total Volume 24h
- Market Cap Change 24h (avec couleur)

#### Sparkline

Mini-graphique SVG.

**Props:**
```typescript
interface SparklineProps {
  points: number[];
  width?: number;      // default: 120
  height?: number;     // default: 40
  stroke?: string;     // default: "#3b82f6"
  fill?: string;       // default: "rgba(59,130,246,0.2)"
}
```

#### NewsSection

Liste des actualités avec refresh automatique.

**Props:**
```typescript
interface NewsSectionProps {
  limit?: number;      // default: 10
  hours?: number;      // default: 24
}
```

**Fonctionnalités:**
- Refresh toutes les 5 minutes
- Temps relatif (5m ago, 2h ago)
- Badge coloré par source
- Liens externes

### Alias d'import

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

**Usage:**
```typescript
import { getCoins } from '@/lib/api';
import CryptoTable from '@/components/CryptoTable';
```

---

## 5. Données InfluxDB

### Configuration

| Paramètre | Valeur |
|-----------|--------|
| URL | `http://localhost:8086` |
| Organisation | `crypto-org` |
| Bucket | `crypto-data` |

### Measurements

#### `crypto_market` (principal)

**Tags:**
- `source`: coingecko, coinmarketcap
- `crypto_id`: bitcoin, ethereum, etc.
- `symbol`: BTC, ETH, etc.
- `name`: Bitcoin, Ethereum, etc.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `price_usd` | float | Prix en USD |
| `market_cap` | float | Capitalisation boursière |
| `market_cap_rank` | int | Rang |
| `volume_24h` | float | Volume 24h |
| `change_1h` | float | Variation 1h (%) |
| `change_24h` | float | Variation 24h (%) |
| `change_7d` | float | Variation 7j (%) |
| `ath` | float | All-Time High |
| `ath_change_pct` | float | % depuis ATH |
| `atl` | float | All-Time Low |
| `atl_change_pct` | float | % depuis ATL |
| `circulating_supply` | float | Supply en circulation |
| `total_supply` | float | Supply total |
| `max_supply` | float | Supply maximum |

#### `crypto_news`

**Tags:**
- `source`: coindesk, cointelegraph

**Fields:**
- `title` (string)
- `link` (string)
- `description` (string)
- `image_url` (string)

#### `fear_greed`

**Tags:**
- `source`: alternative.me

**Fields:**
- `value` (float): 0-100

### Cryptos collectées

```
bitcoin, ethereum, tether, binancecoin, solana,
ripple, usd-coin, cardano, avalanche-2, dogecoin,
polkadot, chainlink, dai, litecoin, shiba-inu,
uniswap, cosmos, stellar, monero, algorand
```

---

## 6. Configuration

### Variables d'environnement

#### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | URL de l'API backend |

#### Backend (référence)

| Variable | Default | Description |
|----------|---------|-------------|
| `INFLUX_URL` | `http://localhost:8086` | URL InfluxDB |
| `INFLUX_ORG` | `crypto-org` | Organisation |
| `INFLUX_BUCKET` | `crypto-data` | Bucket |
| `INFLUX_TOKEN` | - | Token auth |
| `CORS_ORIGINS` | `localhost:3000,3001` | Origins CORS |

### Lancement

```bash
# Prérequis: Docker services running
# (Kafka, InfluxDB, Grafana via docker-compose)

# Backend API
cd crypto-app/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend Web
cd crypto-app/web
npm install
npm run dev
# -> http://localhost:3001
```

---

## 7. Fonctionnalités Attendues

### Dashboard Principal (`/`)

**Implémenté:**
- [x] Stats globales (market cap, volume, variation)
- [x] Tableau des cryptos
- [x] Section actualités

**À implémenter:**
- [ ] Fear & Greed Index display (gauge ou indicateur)
- [ ] Recherche de crypto (input dans Header)
- [ ] Pagination du tableau
- [ ] Tri des colonnes (cliquables)
- [ ] Filtrage des news par source
- [ ] Auto-refresh des données

### Page Détail (`/coin/[id]`)

**Implémenté:**
- [x] Infos de base (nom, symbole, prix)
- [x] Graphique historique
- [x] Sélecteur de période (1D, 1W, 1M, 1Y)

**À implémenter:**
- [ ] Supply details (circulating, total, max)
- [ ] Variations détaillées (1h, 24h, 7d)
- [ ] ATH/ATL avec dates
- [ ] Sparkline dans le tableau principal

### Fonctionnalités transversales

- [ ] Mode sombre/clair (actuellement dark only)
- [ ] Responsive mobile
- [ ] Loading states cohérents
- [ ] Error boundaries
- [ ] Accessibilité (aria-labels, navigation clavier)

---

## 8. Guide Rapide

### Afficher la liste des cryptos

```typescript
import { getCoins, CoinSummary } from '@/lib/api';

// Dans un composant React
const [coins, setCoins] = useState<CoinSummary[]>([]);

useEffect(() => {
  getCoins(100, 1).then(setCoins);
}, []);
```

### Afficher les stats globales

```typescript
import { getGlobal, GlobalStats } from '@/lib/api';

const [stats, setStats] = useState<GlobalStats | null>(null);

useEffect(() => {
  getGlobal().then(setStats);
}, []);
```

### Afficher l'historique d'une crypto

```typescript
import { getCoinHistory } from '@/lib/api';

// 7 jours, intervalle 1h
const history = await getCoinHistory('bitcoin', 7, '1h');
// history.series = Array<{time: string, value: number}>
```

### Afficher les actualités

```typescript
import { getNews } from '@/lib/api';

// 20 articles des dernières 24h
const response = await getNews(20, undefined, 24);
// response.news = Array<NewsArticle>
```

### Formatage des prix

```typescript
function formatPrice(price: number): string {
  if (price < 0.01) return price.toFixed(8);
  if (price < 1) return price.toFixed(6);
  return price.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}
```

### Formatage des grands nombres

```typescript
function formatLargeNumber(num: number): string {
  if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
  return `$${num.toLocaleString()}`;
}
```

### Couleurs conditionnelles

```typescript
function getChangeColor(change: number): string {
  if (change > 0) return 'text-green-500';
  if (change < 0) return 'text-red-500';
  return 'text-gray-500';
}
```

### Design System

**Couleurs principales:**
- Background: `bg-gray-950`, `bg-gray-900`
- Cards: `bg-gray-800/50` avec backdrop-blur
- Accent: `blue-500`, `purple-500`, `pink-500`
- Success: `green-500`
- Error: `red-500`

**Effets:**
- Glassmorphism: `backdrop-blur-xl bg-opacity-50`
- Gradients: `bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950`
- Borders: `border border-gray-800/50`

---

## Notes importantes

1. **L'API retourne des données en temps réel** depuis InfluxDB, pas des données historiques complètes. Les données sont collectées toutes les 60-120 secondes.

2. **Les sparklines** ne sont pas encore implémentées côté API (`sparkline_7d` est toujours `null`). À implémenter si nécessaire.

3. **Le Fear & Greed Index** est disponible via `/fear-greed` mais pas encore affiché dans l'UI.

4. **CORS** est configuré pour accepter `localhost:3000` et `localhost:3001`.

5. **Les images des news** peuvent être null - prévoir un placeholder.

---

## Contact & Ressources

- **API Backend:** `crypto-app/api/`
- **Frontend:** `crypto-app/web/`
- **Infrastructure:** `crypto-monitoring/`
- **Grafana Dashboards:** `http://localhost:3000` (admin/admin)
- **InfluxDB UI:** `http://localhost:8086`
