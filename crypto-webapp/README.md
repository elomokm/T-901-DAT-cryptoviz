# CryptoViz Web Application

Application web complète pour le monitoring de crypto-monnaies avec backend FastAPI et frontend Next.js.

## Structure

```
crypto-webapp/
├── api/          # Backend FastAPI
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── influx_client.py
│       ├── models.py
│       └── routers/
└── web/          # Frontend Next.js
    ├── app/
    ├── components/
    ├── lib/
    └── types/
```

## Installation

### Backend (API)

```bash
cd api
pip install -r requirements.txt
```

### Frontend (Web)

```bash
cd web
npm install
```

## Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine de crypto-webapp :

```env
INFLUX_TOKEN=votre_token_influxdb
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## Démarrage

### Backend

```bash
cd api
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd web
npm run dev
```

L'application sera disponible sur :
- Frontend : http://localhost:3000
- API : http://localhost:8000
- API Docs : http://localhost:8000/docs

## Endpoints API

| Endpoint | Description |
|----------|-------------|
| GET /health | Health check |
| GET /global | Stats globales du marché |
| GET /coins | Liste des cryptos |
| GET /coins/{id} | Détails d'une crypto |
| GET /coins/{id}/history | Historique des prix |
| GET /news | Actualités |
| GET /news/sources | Sources disponibles |
| GET /fear-greed | Index Fear & Greed |

## Fonctionnalités

- Dashboard avec stats globales
- Tableau des cryptos avec tri et pagination
- Graphique Fear & Greed
- Actualités crypto en temps réel
- Page détail avec graphique historique
- Thème sombre avec design glassmorphism
- Auto-refresh des données
