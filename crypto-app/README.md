# Crypto App (Option A)

Next.js frontend + FastAPI backend wired to existing InfluxDB/Kafka stack.

## Services
- api (FastAPI): http://localhost:8000
- web (Next.js): http://localhost:3001

## Prerequisites
- Docker & Docker Compose
- Existing InfluxDB from `crypto-monitoring/docker-compose.yml` (exposed at http://localhost:8086)

## Quick start

```sh
# From repo root
cd crypto-app
# (Optional) override env
# export INFLUX_URL=http://localhost:8086
# export INFLUX_ORG=crypto-org
# export INFLUX_BUCKET=crypto-data
# export INFLUX_TOKEN=...  # if changed from crypto-monitoring compose
# export DEFAULT_CRYPTOS=bitcoin,cardano,ethereum,polkadot,solana
# export NEXT_PUBLIC_API_BASE=http://localhost:8000

# Launch web + api
docker compose up -d --build

# Check health
curl http://localhost:8000/health
# Open http://localhost:3001
```

## API endpoints
- GET `/health` → `{ status: "ok" }`
- NEW GET `/coins?limit=50&page=1` → latest snapshot list (price_usd, market_cap, volume_24h, change_1h/24h/7d, supplies)
- NEW GET `/global` → aggregate totals (total_market_cap, total_volume_24h, weighted market_cap_change_24h, count)
- (Legacy) GET `/overview/market-cap?cryptos=bitcoin,cardano,ethereum,polkadot,solana` → latest market cap per crypto + total
- (Legacy) GET `/overview/prices?cryptos=bitcoin,cardano,ethereum,polkadot,solana&range=24h&interval=30m` → price series per crypto

## Notes
- The API connects to Influx at `INFLUX_URL` (defaults to host.docker.internal:8086 from inside the container; localhost:8086 from host).
- The web app fetches from the browser to `NEXT_PUBLIC_API_BASE` (default http://localhost:8000), avoiding server-side connectivity issues.
- Initial scope examples restricted to: bitcoin, cardano, ethereum, polkadot, solana; `/coins` now lists all recent cryptos persisted.

### Data mapping
Measurement: `crypto_market` (env override: `INFLUX_MEASUREMENT`)
Tags: `source`, `crypto_id`, `symbol`, `name`
Fields consumed: `price_usd`, `market_cap`, `market_cap_rank`, `volume_24h`, `change_1h`, `change_24h`, `change_7d`, `ath`, `ath_change_pct`, `atl`, `atl_change_pct`, `circulating_supply`, `total_supply`, `max_supply`

### Roadmap
1. `/coins/{id}` detail endpoint (full profile + sparkline 7d)
2. `/coins/{id}/history?days=7&interval=30m` time-series from Influx
3. `/fear-greed` endpoint once index points are written
4. Front components: GlobalStatsCards, CoinTable, CoinDetail
5. Sparkline caching (Redis or in-memory) to reduce query cost
