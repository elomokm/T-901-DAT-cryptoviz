# Guide Producer/Consumer - CryptoViz Pipeline

Documentation complète du développement du pipeline Kafka → Spark → InfluxDB pour le projet CryptoViz.

---

## Table des matières
1. [Architecture finale](#architecture-finale)
2. [Problèmes rencontrés et solutions](#problèmes-rencontrés-et-solutions)
3. [Configuration du Producer](#configuration-du-producer)
4. [Configuration du Consumer](#configuration-du-consumer)
5. [Commandes utiles](#commandes-utiles)
6. [Tests et validation](#tests-et-validation)

---

## Architecture finale

```
CoinGecko API → Producer (Python/kafka-python) → Kafka → Consumer (Spark Streaming) → InfluxDB → Grafana/API
```

### Stack technique
- **Producer**: Python 3.11, kafka-python, requests
- **Message Broker**: Apache Kafka 7.4.0 (Confluent)
- **Consumer**: PySpark 3.5.0, Structured Streaming
- **Base de données**: InfluxDB 2.7 (time-series)
- **Visualisation**: Grafana 10.0.0
- **API/Web**: FastAPI + Next.js 14

### Cryptos surveillés
- bitcoin
- cardano
- ethereum
- polkadot
- solana

---

## Problèmes rencontrés et solutions

### 1. ❌ Producer ne pouvait pas envoyer de messages

**Symptôme:**
```
NoBrokersAvailable: NoBrokersAvailable
```

**Causes:**
1. Kafka n'était pas correctement démarré
2. Mauvaise configuration des listeners Kafka
3. Type du paramètre `acks` incorrect

**Solutions:**
```yaml
# docker-compose.yml - Configuration Kafka corrigée
environment:
  KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092  # ✅ Écoute sur toutes les interfaces
  KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```

```python
# crypto_producer.py - Configuration producer corrigée
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=1,  # ✅ Type int, pas string 'all'
    retries=3,
    linger_ms=0,
    batch_size=16384
)
```

**Méthode de flush optimisée:**
```python
# ✅ Flush AVANT l'envoi pour garantir la livraison
producer.flush()
for crypto in CRYPTOS:
    data = fetch_crypto_data(crypto)
    future = producer.send(TOPIC, value=data)
    # Pas de flush ici, déjà fait avant
```

---

### 2. ❌ Consumer n'écrivait pas dans InfluxDB

**Symptôme:**
```
Batch 123 processed: 5 rows
# Mais rien dans InfluxDB
```

**Causes:**
1. Écriture asynchrone qui ne finalisait pas
2. Pas de gestion d'erreur visible
3. Mode foreachBatch mal configuré

**Solutions:**

```python
# crypto_consumer_spark.py - Écriture synchrone forcée
def write_batch_to_influx(batch_df, batch_id):
    rows = batch_df.collect()
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)  # ✅ Mode synchrone
    
    for row in rows:
        point = Point("crypto_price") \
            .tag("crypto", row.crypto) \
            .field("price_usd", float(row.price_usd)) \
            .field("price_eur", float(row.price_eur)) \
            .field("change_24h", float(row.change_24h)) \
            .field("market_cap", float(row.market_cap)) \
            .field("volume_24h", float(row.volume_24h)) \
            .time(datetime.utcnow(), WritePrecision.NS)
        
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    
    write_api.close()
    client.close()
    print(f"✅ Batch {batch_id} écrit: {len(rows)} points dans InfluxDB")
```

**Diagnostics ajoutés:**
```python
# Vérification en temps réel
print(f"📊 Batch {batch_id} reçu: {batch_df.count()} lignes")
batch_df.show(5, truncate=False)  # Affiche les données
```

---

### 3. ❌ Offsets Kafka ne progressaient pas

**Symptôme:**
```bash
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 --topic crypto-prices --time -1
# Toujours crypto-prices:0:0
```

**Causes:**
1. Producer n'envoyait pas réellement (flush manquant)
2. Configuration `acks` incorrecte
3. Kafka venait de redémarrer

**Solutions:**
```python
# Pattern flush-first
producer.flush()  # ✅ Vide le buffer d'abord
for crypto in CRYPTOS:
    future = producer.send(TOPIC, value=data)
    try:
        record_metadata = future.get(timeout=10)
        print(f"✅ {crypto}: partition {record_metadata.partition}, offset {record_metadata.offset}")
    except Exception as e:
        print(f"❌ Erreur envoi {crypto}: {e}")
```

**Validation:**
```bash
# Vérifier les offsets après chaque poll
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 --topic crypto-prices --time -1
# ✅ crypto-prices:0:1234 (nombre qui augmente)
```

---

### 4. ❌ Incompatibilité Java 17 avec Spark

**Symptôme:**
```
java.lang.IllegalAccessError: class org.apache.spark...
```

**Cause:**
Spark 3.5 nécessite Java 17 (pas Java 8)

**Solution:**
```bash
# macOS
brew install openjdk@17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Vérification
java -version
# openjdk version "17.0.x"
```

**Configuration Spark:**
```python
spark = SparkSession.builder \
    .appName("CryptoConsumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()
```

---

### 5. ❌ Données visibles dans InfluxDB UI mais pas dans Grafana

**Symptôme:**
- Data Explorer InfluxDB: ✅ Données présentes
- Grafana: ❌ "No data"

**Causes:**
1. Mauvais filtre de temps (range trop court)
2. Regex variable mal configuré
3. Pas d'aggregateWindow

**Solutions:**

**Query Flux corrigée:**
```flux
from(bucket: "crypto-data")
  |> range(start: -24h)  # ✅ Assez large pour voir des données
  |> filter(fn: (r) => r._measurement == "crypto_price")
  |> filter(fn: (r) => r._field == "price_usd")
  |> filter(fn: (r) => r.crypto =~ /^${crypto:regex}$/)  # ✅ Regex anchored
  |> aggregateWindow(every: 5m, fn: last, createEmpty: false)  # ✅ Réduit les points
```

**Variable Grafana:**
```json
{
  "name": "crypto",
  "type": "query",
  "query": "import \"influxdata/influxdb/schema\"\nschema.tagValues(bucket: \"crypto-data\", tag: \"crypto\", predicate: (r) => r._measurement == \"crypto_price\", start: -90d)",
  "regex": "^(bitcoin|cardano|ethereum|polkadot|solana)$",  // ✅ Restreint aux 5 cryptos
  "allValue": "^(bitcoin|cardano|ethereum|polkadot|solana)$",  // ✅ All = regex complet
  "multi": true,
  "includeAll": true
}
```

---

## Configuration du Producer

### Fichier: `crypto_producer.py`

**Paramètres clés:**
```python
CRYPTOS = ["bitcoin", "ethereum", "cardano", "solana", "polkadot"]
TOPIC = "crypto-prices"
KAFKA_BROKER = "localhost:9092"

# Configuration optimale
PRODUCER_CONFIG = {
    'bootstrap_servers': KAFKA_BROKER,
    'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
    'acks': 1,  # Balance entre performance et fiabilité
    'retries': 3,
    'linger_ms': 0,  # Pas de batching, envoi immédiat
    'batch_size': 16384,
    'compression_type': None
}
```

**Variables d'environnement (optionnelles):**
```bash
export SEND_EVERY_POLL=1          # 1=flush avant chaque poll, 0=flush après
export POLL_INTERVAL_SEC=10       # Intervalle entre les polls API (secondes)
export PRODUCER_ACKS=1            # 0, 1, ou 'all'
export PRODUCER_LINGER_MS=0       # Délai d'attente avant envoi
export PRODUCER_BATCH_SIZE=16384  # Taille max du batch
export PRODUCER_COMPRESSION=none  # none, gzip, snappy, lz4
```

**Structure des messages Kafka:**
```json
{
  "crypto": "bitcoin",
  "price_usd": 109724.5,
  "price_eur": 98432.1,
  "change_24h": 2.34,
  "market_cap": 2186543028396,
  "volume_24h": 45123456789,
  "timestamp": "2025-10-31T10:30:45.123456"
}
```

**Lancement:**
```bash
cd crypto-monitoring
source .venv/bin/activate

# Méthode 1: Script
./run_producer.sh

# Méthode 2: Manuel
export SEND_EVERY_POLL=1
export POLL_INTERVAL_SEC=10
python3 crypto_producer.py
```

---

## Configuration du Consumer

### Fichier: `crypto_consumer_spark.py`

**Configuration Spark:**
```python
spark = SparkSession.builder \
    .appName("CryptoConsumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

# Kafka source
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "crypto-prices") \
    .option("startingOffsets", "earliest") \
    .load()
```

**Schéma de parsing:**
```python
schema = StructType([
    StructField("crypto", StringType(), True),
    StructField("price_usd", DoubleType(), True),
    StructField("price_eur", DoubleType(), True),
    StructField("change_24h", DoubleType(), True),
    StructField("market_cap", DoubleType(), True),
    StructField("volume_24h", DoubleType(), True),
    StructField("timestamp", StringType(), True)
])
```

**Écriture InfluxDB (SYNCHRONE):**
```python
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def write_batch_to_influx(batch_df, batch_id):
    rows = batch_df.collect()
    if len(rows) == 0:
        return
    
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    for row in rows:
        point = Point("crypto_price") \
            .tag("crypto", row.crypto) \
            .field("price_usd", float(row.price_usd)) \
            .field("price_eur", float(row.price_eur)) \
            .field("change_24h", float(row.change_24h)) \
            .field("market_cap", float(row.market_cap)) \
            .field("volume_24h", float(row.volume_24h)) \
            .time(datetime.utcnow(), WritePrecision.NS)
        
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    
    write_api.close()
    client.close()
```

**Lancement:**
```bash
cd crypto-monitoring
source .venv/bin/activate

# Méthode 1: Script
./run_consumer.sh

# Méthode 2: Manuel avec Java 17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  crypto_consumer_spark.py
```

---

## Commandes utiles

### Docker & Kafka

```bash
# Démarrer les services
cd crypto-monitoring
docker compose up -d

# Vérifier les services
docker ps
docker compose logs -f kafka

# Vérifier que Kafka est prêt
docker exec -it kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Lister les topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# Voir les offsets (progression)
docker exec -it kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic crypto-prices \
  --time -1

# Consommer des messages (debug)
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto-prices \
  --from-beginning \
  --max-messages 5

# Réinitialiser les offsets (si besoin)
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group crypto-consumer-group \
  --reset-offsets \
  --to-earliest \
  --topic crypto-prices \
  --execute
```

### InfluxDB

```bash
# Accès UI
open http://localhost:8086
# User: admin / Pass: adminpassword
# Org: crypto-org
# Bucket: crypto-data

# CLI: Lister les measurements
docker exec -it influxdb influx query \
  'from(bucket:"crypto-data") |> range(start:-1h) |> group(columns:["_measurement"]) |> distinct(column:"_measurement")'

# Compter les points par crypto
docker exec -it influxdb influx query \
  'from(bucket:"crypto-data") |> range(start:-24h) |> filter(fn:(r)=>r._measurement=="crypto_price") |> group(columns:["crypto"]) |> count()'

# Supprimer les séries de test
python3 influx_delete_test_series.py
```

### Grafana

```bash
# Accès UI
open http://localhost:3000
# User: admin / Pass: admin

# Redémarrer pour recharger les dashboards
docker compose restart grafana

# Vérifier les dashboards provisionnés
docker exec -it grafana ls /var/lib/grafana/dashboards
```

### Python environments

```bash
# Créer le venv (première fois)
cd crypto-monitoring
python3 -m venv .venv

# Activer
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Vérifier les packages
pip list | grep -E 'kafka|spark|influx'
```

---

## Tests et validation

### Test end-to-end complet

```bash
# 1. Services Docker
cd crypto-monitoring
docker compose up -d
sleep 30  # Attendre Kafka

# 2. Vérifier Kafka prêt
docker exec -it kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# 3. Lancer le producer
source .venv/bin/activate
export SEND_EVERY_POLL=1
export POLL_INTERVAL_SEC=10
python3 crypto_producer.py &
PRODUCER_PID=$!

# 4. Vérifier les messages Kafka
sleep 15
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto-prices \
  --from-beginning \
  --max-messages 2

# 5. Lancer le consumer
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 crypto_consumer_spark.py &
CONSUMER_PID=$!

# 6. Attendre quelques batchs
sleep 60

# 7. Vérifier InfluxDB
open http://localhost:8086
# Data Explorer:
# - FROM crypto-data
# - FILTER _measurement = crypto_price
# - FILTER crypto = bitcoin
# - FIELD price_usd
# - RANGE last 1h
# ✅ Doit afficher des points

# 8. Vérifier Grafana
open http://localhost:3000/d/crypto-core/crypto-core
# ✅ Les graphiques doivent afficher des données

# 9. Nettoyer
kill $PRODUCER_PID $CONSUMER_PID
```

### Validation des données

**Vérifier la structure dans InfluxDB:**
```flux
from(bucket: "crypto-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "crypto_price")
  |> filter(fn: (r) => r.crypto == "bitcoin")
  |> limit(n: 5)
```

**Attendu:**
```
_time                    _measurement   crypto   _field       _value
2025-10-31T10:30:45Z    crypto_price   bitcoin  price_usd    109724.5
2025-10-31T10:30:45Z    crypto_price   bitcoin  price_eur    98432.1
2025-10-31T10:30:45Z    crypto_price   bitcoin  change_24h   2.34
2025-10-31T10:30:45Z    crypto_price   bitcoin  market_cap   2186543028396
2025-10-31T10:30:45Z    crypto_price   bitcoin  volume_24h   45123456789
```

---

## Troubleshooting rapide

| Problème | Vérification | Solution |
|----------|--------------|----------|
| Producer: NoBrokersAvailable | `docker ps \| grep kafka` | `docker compose restart kafka`, attendre 30s |
| Consumer: No data | Logs Spark | Vérifier `write_batch_to_influx` appelé, mode SYNCHRONOUS |
| Grafana: No data | InfluxDB UI | Vérifier range, regex variable, aggregateWindow |
| Offsets bloqués à 0 | GetOffsetShell | Producer flush-first pattern, vérifier acks |
| Java IllegalAccessError | `java -version` | Installer Java 17, `export JAVA_HOME` |

---

## Résumé des leçons apprises

1. **Kafka Producer:**
   - ✅ `acks=1` (int) pas `'all'` (string)
   - ✅ Flush AVANT l'envoi pour garantir livraison
   - ✅ Vérifier `future.get()` pour confirmer envoi

2. **Spark Consumer:**
   - ✅ Mode SYNCHRONOUS obligatoire pour InfluxDB
   - ✅ Java 17 requis pour Spark 3.5
   - ✅ foreachBatch avec diagnostics print()

3. **InfluxDB:**
   - ✅ WritePrecision.NS pour timestamp précis
   - ✅ Tag = crypto, Fields = metrics numériques
   - ✅ Data Explorer pour debug rapide

4. **Grafana:**
   - ✅ Flux avec aggregateWindow pour performance
   - ✅ Regex anchored `^...$` pour variables
   - ✅ fill(usePrevious) pour éviter les gaps

5. **Debugging:**
   - ✅ Toujours vérifier bout à bout: Kafka offsets → InfluxDB UI → Grafana
   - ✅ Logs verbose essentiels (print batch_id, count)
   - ✅ Scripts de run avec env vars pour reproductibilité

---

## Fichiers importants

```
crypto-monitoring/
├── crypto_producer.py              # Producer Kafka
├── crypto_consumer_spark.py        # Consumer Spark → InfluxDB
├── run_producer.sh                 # Script lancement producer
├── run_consumer.sh                 # Script lancement consumer
├── docker-compose.yml              # Kafka/Zookeeper/InfluxDB/Grafana
├── requirements.txt                # Dépendances Python
├── influx_delete_test_series.py   # Nettoyage séries test
└── grafana/
    ├── provisioning/
    │   ├── datasources/influxdb.yml
    │   └── dashboards/dashboard.yml
    └── dashboards/
        ├── crypto_core.json
        └── comparisons.json
```

---

**Dernière mise à jour:** 31 octobre 2025  
**Auteur:** Développement itératif avec GitHub Copilot  
**Stack:** Kafka 7.4 + Spark 3.5 + InfluxDB 2.7 + Grafana 10.0
