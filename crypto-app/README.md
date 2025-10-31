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
- GET `/overview/market-cap?cryptos=bitcoin,cardano,ethereum,polkadot,solana` → latest market cap per crypto + total
- GET `/overview/prices?cryptos=bitcoin,cardano,ethereum,polkadot,solana&range=24h&interval=30m` → price series per crypto

## Notes
- The API connects to Influx at `INFLUX_URL` (defaults to host.docker.internal:8086 from inside the container; localhost:8086 from host).
- The web app fetches from the browser to `NEXT_PUBLIC_API_BASE` (default http://localhost:8000), avoiding server-side connectivity issues.
- Scope is restricted to: bitcoin, cardano, ethereum, polkadot, solana.
