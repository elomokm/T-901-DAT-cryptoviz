# Status – 31/10/2025

Ce document résume l’essentiel depuis le dernier commit et fixe la suite immédiate.

## Ce qui a changé récemment

- Grafana – Dashboard Crypto Core
  - Ajout des KPI globaux et conversion en graphiques:
    - Global Market Cap (somme agrégée au fil du temps)
    - Global 24h Volume (somme agrégée au fil du temps)
  - Robustesse des requêtes Flux:
    - Utilisation de `fill(usePrevious: true)` pour éviter les trous
    - Variable `crypto` – All simplifié à `.*` pour éviter les regex cassantes
    - Filtre crypto homogène et exclusion `test_*` et `None`
  - Change 24h: calculé à partir de `price_usd` (t vs t-24h) pour plus de fiabilité

- Grafana – Dashboard Comparisons
  - “Top movers 24h” (table) avec unités et tri corrects
  - Correlation vs BTC (30d): panneau ajouté (table) pour ETH, SOL, XRP, BNB
  - Variable `crypto` – `allValue` passé à `.*`

- Pipeline données
  - Producer/Consumer/Influx stables; writes synchrones confirmés
  - Nettoyage de séries `test_*` côté Influx et filtres côté dashboards

## Points d’attention

- Si un panneau global affiche “No data”, vérifier la période et la présence de `volume_24h` dans la fenêtre; fallback d’agrégation déjà en place (1m/5m + fill)
- Marché réel: certaines mesures peuvent être creuses sur de très courtes fenêtres; élargir (ex: 2d/7d) si nécessaire

## Décision produit validée

- Option retenue: Option A – Front Next.js + API FastAPI + InfluxDB/Kafka
- Périmètre cryptos (5) pour l’app: `bitcoin`, `ethereum`, `solana`, `binancecoin`, `ripple`

## Prochaines étapes (immédiates)

1) Scaffolding de l’application “façon CoinGecko”
   - Front: Next.js (TypeScript, Tailwind, shadcn/ui, charts ECharts/Recharts)
   - API: FastAPI (endpoints overview, comparisons/correlation, risk)
   - Docker Compose: services `web`, `api` (reuse Influx/Kafka existants)
2) Pages V1
   - Overview (Global MK/Vol, Movers, Dominance, Norm=100)
   - Comparisons (Norm=100, Dominance, Corrélation 30d)
   - Risk & Momentum (Vol 7/30j, Drawdown, RSI/MACD)
   - Coin detail (fiche par crypto)
3) (Optionnel) Scraper news + builder sentiment (Kafka → Influx)

## Commandes opérées (opérationnel)

- Redémarrages Grafana pour recharger provisioning après modifs JSON

## Annexes

- Dashboards modifiés: `crypto-monitoring/grafana/dashboards/crypto_core.json`, `crypto-monitoring/grafana/dashboards/comparisons.json`
- Datasource: Influx 2.x (Flux) – UID `influxdb-crypto`