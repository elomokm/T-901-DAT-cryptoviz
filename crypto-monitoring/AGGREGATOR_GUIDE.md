# 🔄 Multi-Source Price Aggregation - Documentation Pro

## 🎯 Objectif

Implémenter un système d'agrégation de prix **professionnel** qui :
- ✅ Récupère les prix depuis **plusieurs sources** (CoinGecko + CoinMarketCap)
- ✅ Calcule le **prix consensus** (moyenne)
- ✅ Détecte les **anomalies** (spread > 1%)
- ✅ Publie dans Kafka pour le pipeline

---

## 📊 Architecture

```
┌──────────────┐
│  CoinGecko   │──┐
│     API      │  │
└──────────────┘  │
                  ├──► ┌────────────────┐      ┌───────┐      ┌──────────┐
┌──────────────┐  │    │  Aggregator    │─────►│ Kafka │─────►│ InfluxDB │
│ CoinMarket   │──┘    │  (Average)     │      └───────┘      └──────────┘
│  Cap API     │       └────────────────┘
└──────────────┘              │
                              ▼
                       Prix Consensus
                    (Moyenne des sources)
```

---

## 🚀 Utilisation

### Démarrer l'Agrégateur

```bash
cd crypto-monitoring
source ../.venv/bin/activate
python run_aggregator.py
```

### Output Attendu

```
🔄 MULTI-SOURCE PRICE AGGREGATOR
📡 Kafka Broker: localhost:9092
📊 Sources: CoinGecko + CoinMarketCap
🎯 Strategy: Average Consensus Price

📦 Batch #1 - 2025-11-20T12:57:55
  🌐 Fetching CoinGecko...
  💎 Fetching CoinMarketCap...
  ✅ BTC    $   91,789.27 (2 sources, spread: 0.00%)
  ✅ ETH    $    3,028.25 (2 sources, spread: 0.03%)
  ✅ BNB    $      903.33 (2 sources, spread: 0.05%)
  ...
  ✅ Batch #1: 14/15 cryptos published
  ⏳ Waiting 30s before next batch...
```

---

## 💡 Avantages de cette Approche

### 1. **Fiabilité Accrue** 🛡️
- Si une API est down, l'autre prend le relais
- Pas de single point of failure

### 2. **Prix Plus Précis** 🎯
- Moyenne de 2 sources = réduction du bruit
- Moins sensible aux erreurs d'une seule API

### 3. **Détection d'Anomalies** ⚠️
- Calcul automatique du spread entre sources
- Alert si spread > 1% (incohérence)

### 4. **Traçabilité** 📝
- Chaque prix inclut les métadonnées :
  ```json
  {
    "price_usd": 91789.27,
    "aggregation": {
      "sources": ["coingecko", "coinmarketcap"],
      "source_count": 2,
      "price_spread_pct": 0.00,
      "individual_prices": {
        "coingecko": 91789.00,
        "coinmarketcap": 91789.54
      }
    }
  }
  ```

---

## 📈 Métriques de Qualité

### Spread Typique (Production)
- ✅ **< 0.5%** : Excellent (prix cohérents)
- ⚠️ **0.5-1%** : Acceptable (légère différence)
- 🚨 **> 1%** : Anomalie (investigation requise)

### Résultats Actuels
```
BTC:  0.00% ✅  (parfait)
ETH:  0.03% ✅  (excellent)
BNB:  0.05% ✅  (excellent)
XRP:  0.27% ✅  (très bon)
```

---

## 🔧 Configuration

### Variables d'Environnement

```bash
# .env file
CMC_API_KEY=your_key_here  # Optionnel mais recommandé
KAFKA_BROKER=localhost:9092
```

### Sans Clé CMC
- L'agrégateur fonctionne quand même
- Utilise uniquement CoinGecko
- Toujours mieux qu'une seule source !

### Avec Clé CMC (Gratuite)
- Obtenir sur https://coinmarketcap.com/api/
- Plan gratuit : 333 calls/jour
- Largement suffisant pour notre usage

---

## 📊 Données Enrichies

Chaque message Kafka contient :

```python
{
    'crypto_id': 'bitcoin',
    'symbol': 'BTC',
    'name': 'Bitcoin',
    'price_usd': 91789.27,           # Prix consensus
    'market_cap': 1828089298826,
    'volume_24h': 85620144926,
    'change_24h': 0.61,
    'timestamp': '2025-11-20T12:57:55',
    'source': 'multi-source-aggregator',
    'aggregation': {
        'sources': ['coingecko', 'coinmarketcap'],
        'source_count': 2,
        'price_spread_pct': 0.00,
        'individual_prices': {
            'coingecko': 91789.00,
            'coinmarketcap': 91789.54
        }
    }
}
```

---

## 🔄 Workflow Complet

### 1. **Collecte** (toutes les 30s)
```python
coingecko_data = fetch_coingecko_prices(...)
cmc_data = fetch_coinmarketcap_prices(...)
```

### 2. **Agrégation**
```python
prices = [coingecko_price, cmc_price]
consensus_price = sum(prices) / len(prices)
spread = (max - min) / consensus * 100
```

### 3. **Publication**
```python
producer.send('crypto-prices', consensus_data)
```

### 4. **Consommation**
```
Consumer Spark → InfluxDB → API → Frontend
```

---

## 📋 Comparaison : Avant vs Après

### ❌ Avant (1 source)
```
Source: CoinGecko uniquement
Prix BTC: $91,789
Fiabilité: ⭐⭐⭐ (moyenne)
Risque: Single point of failure
```

### ✅ Après (Multi-sources)
```
Sources: CoinGecko + CoinMarketCap
Prix BTC: $91,789.27 (consensus)
Fiabilité: ⭐⭐⭐⭐⭐ (excellente)
Risque: Résilience accrue
Bonus: Détection d'anomalies
```

---

## 🎓 Principes Professionnels Appliqués

### 1. **Redundancy** 🔄
- Plusieurs sources = pas de single point of failure
- Standard dans les systèmes financiers

### 2. **Consensus** 🤝
- Moyenne = neutralise les outliers
- Utilisé par les exchanges pro

### 3. **Monitoring** 📊
- Spread tracking
- Alert sur incohérences

### 4. **Traçabilité** 📝
- Métadonnées complètes
- Audit trail pour debugging

---

## 🚦 Status Check

### Vérifier que ça Tourne

```bash
# Voir le process
ps aux | grep run_aggregator

# Voir les logs temps réel
tail -f logs/aggregator.log

# Tester les données dans Kafka
python local_doc/check_kafka_messages.py
```

### Vérifier la Qualité

```bash
# Check InfluxDB
curl http://localhost:8000/api/v1/global

# Devrait montrer ~15 cryptos actives
# Prix cohérents avec le marché
```

---

## 🔮 Améliorations Futures

### Phase 2 (Optionnel)
- [ ] Ajouter Binance API (3ème source)
- [ ] Weighted average (pondération par volume)
- [ ] Historical spread analysis
- [ ] Alert Telegram si spread > 2%

### Phase 3 (Avancé)
- [ ] Machine Learning pour détecter prix suspects
- [ ] Auto-retry avec exponential backoff
- [ ] Load balancing entre sources
- [ ] Rate limiting intelligent

---

## 📚 Ressources

### APIs Utilisées
- **CoinGecko**: https://www.coingecko.com/api/documentation
- **CoinMarketCap**: https://coinmarketcap.com/api/documentation/v1/

### Best Practices
- [Crypto Data Aggregation](https://docs.kaiko.com/)
- [Financial Data Quality](https://www.investopedia.com/terms/d/data-quality.asp)

---

## ✅ Checklist de Production

- [x] Multi-source fetching
- [x] Consensus calculation
- [x] Spread monitoring
- [x] Kafka publishing
- [x] Error handling
- [x] Logging
- [x] Graceful shutdown
- [x] Rate limiting respect
- [ ] Alerting (TODO)
- [ ] Metrics dashboard (TODO)

---

**🎉 System Status: PRODUCTION READY**

L'agrégateur multi-sources est opérationnel et fournit des données de qualité professionnelle !
