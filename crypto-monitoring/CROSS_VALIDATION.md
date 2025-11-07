# 🔄 Validation Croisée CoinGecko vs CoinMarketCap

## Vue d'ensemble

L'agent **CoinMarketCap** sert de source alternative pour valider les données de **CoinGecko**. Cette approche permet de :

- ✅ Détecter les anomalies de prix (divergence > 5%)
- ✅ Augmenter la fiabilité des données
- ✅ Identifier les problèmes d'API en temps réel
- ✅ Avoir une redondance en cas de panne

## Architecture

```
┌─────────────────┐      ┌─────────────────┐
│  CoinGecko API  │      │CoinMarketCap API│
│   (Free Tier)   │      │   (Free Tier)   │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │ 60s poll               │ 120s poll
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
         │ crypto-prices │  ← Même topic Kafka
         │  (Kafka Topic)│
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
         │   InfluxDB    │
         └───────────────┘
```

## Configuration

### 1. Obtenir une clé API CoinMarketCap (Gratuite)

1. Allez sur https://coinmarketcap.com/api/
2. Créez un compte gratuit
3. Copiez votre clé API

**Plan Gratuit:**
- ✅ 10,000 appels/mois
- ✅ Top 100 cryptos
- ✅ Données en temps réel

### 2. Configurer le `.env`

```bash
# API Keys
CMC_API_KEY=votre_cle_coinmarketcap_ici

# Polling intervals
COINGECKO_POLL_INTERVAL=60      # 1 minute
COINMARKETCAP_POLL_INTERVAL=120 # 2 minutes (économise les quotas)
```

## Utilisation

### Lancer l'agent CoinMarketCap

```bash
# Terminal 1 : CoinGecko (déjà lancé)
python run_coingecko_agent.py

# Terminal 2 : CoinMarketCap (nouveau)
python run_coinmarketcap_agent.py
```

### Analyser la validation croisée

```bash
# Écouter les messages pendant 60 secondes
python cross_validation.py 60
```

**Sortie attendue:**
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

[coingecko     ] ETH    = $    3,456.78
[coinmarketcap ] ETH    = $    3,612.34

⚠️  ETH - Divergence: 4.50%
   CoinGecko     : $3,456.78
   CoinMarketCap : $3,612.34
   Différence    : $155.56
```

## Détection d'Anomalies

L'agent CoinMarketCap inclut un système de détection d'anomalies :

### 1. Variation de prix excessive
- **Seuil**: 30% en 2 minutes
- **Action**: Flag `anomaly_detected=true` dans Kafka

```json
{
  "source": "coinmarketcap",
  "symbol": "BTC",
  "price_usd": 105000.0,
  "anomaly_detected": true,  ← Flag activé
  "timestamp": "2025-11-07T14:30:00Z"
}
```

### 2. Validation des données
- Prix <= 0 → Rejeté
- Market cap <= 0 → Rejeté
- Timestamp futur → Rejeté

## Prochaines Étapes

### Phase 1.2 : Data Quality Framework

Créer un **consumer Spark dédié** pour la validation croisée :

```python
# Pseudo-code du consumer de validation
def validate_prices(batch_df):
    """Compare CoinGecko vs CoinMarketCap"""
    
    # Joindre les deux sources sur symbol + fenêtre de 5min
    joined = coingecko_df.join(
        coinmarketcap_df,
        on=['symbol', 'window'],
        how='outer'
    )
    
    # Calculer divergence
    divergence = abs(cg_price - cmc_price) / cg_price * 100
    
    # Si divergence > 5% → Dead Letter Queue
    if divergence > 5.0:
        send_to_dlq(row)
    else:
        send_to_influx(row)
```

### Phase 1.3 : Binance WebSocket (Real-time)

Créer un agent pour les données temps réel :
- ✅ Trades en direct
- ✅ Order book
- ✅ Ticker updates

## Métriques de Performance

### Quotas API (Plan Gratuit)

| Source         | Quota Mensuel | Poll Interval | Messages/Jour |
|----------------|---------------|---------------|---------------|
| CoinGecko      | Illimité*     | 60s           | ~28,800       |
| CoinMarketCap  | 10,000/mois   | 120s          | ~14,400       |

\*CoinGecko limite à 10-50 req/min selon endpoint

### Coût Estimé (Upgrade Payant)

| Service        | Plan Pro         | Prix/Mois |
|----------------|------------------|-----------|
| CoinGecko      | 500 req/min      | $129      |
| CoinMarketCap  | 1M calls/mois    | $99       |

## Troubleshooting

### Erreur: "CMC_API_KEY non définie"

```bash
# Vérifier le .env
cat .env | grep CMC_API_KEY

# Recharger les variables
source .venv/bin/activate
python run_coinmarketcap_agent.py
```

### Erreur: "API rate limit exceeded"

**Symptôme:** HTTP 429

**Solution:**
```bash
# Augmenter l'intervalle de polling dans .env
COINMARKETCAP_POLL_INTERVAL=180  # 3 minutes au lieu de 2
```

### Divergence > 10% constante

**Causes possibles:**
1. API en maintenance
2. Différence de paire de trading (USD vs USDT)
3. Délai de mise à jour entre sources

**Action:**
```bash
# Vérifier la santé des APIs
curl "https://api.coingecko.com/api/v3/ping"
curl -H "X-CMC_PRO_API_KEY: $CMC_API_KEY" \
  "https://pro-api.coinmarketcap.com/v1/key/info"
```

## Références

- [CoinMarketCap API Docs](https://coinmarketcap.com/api/documentation/v1/)
- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [Kafka Best Practices](https://kafka.apache.org/documentation/#bestpractices)
