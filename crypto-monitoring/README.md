
## Crypto Monitoring Pipeline (Kafka → Spark → InfluxDB → Grafana)

Pipeline temps réel pour collecter des prix crypto (CoinGecko), les publier dans Kafka, les traiter avec Spark Structured Streaming, et les stocker dans InfluxDB pour visualisation.

### Vue d'ensemble
- Producteur Python (kafka-python) → Topic Kafka `crypto-prices`
- Consommateur Spark (foreachBatch) → InfluxDB 2.x (measurement `crypto_price`)
- Tags/fields:
	- tag: `crypto`
	- fields: `price_usd`, `price_eur`, `change_24h`, `market_cap`, `volume_24h`
- Grafana (optionnel) branché sur InfluxDB pour dashboards

---

## Prérequis
- macOS (zsh)
- Docker Desktop ou Colima
- Python 3.11+ (venv)
- Java 17 (Spark 3.5)

Astuce Java 17 sur macOS:
```bash
brew install openjdk@17
export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
```

---

## Démarrer l'infrastructure

Le `docker-compose.yml` fournit: Zookeeper, Kafka, InfluxDB (org=bucket préconfigurés), Grafana.

```bash
cd crypto-monitoring
docker compose up -d
```

Accès rapides:
- Kafka broker: `localhost:9092`
- InfluxDB UI: http://localhost:8086 (user: `admin`, pass: `adminpassword`)
- Influx org: `crypto-org`, bucket: `crypto-data`
- Influx token (init): défini dans `docker-compose.yml` (DOCKER_INFLUXDB_INIT_ADMIN_TOKEN)
- Grafana: http://localhost:3000 (admin/admin)

Notes Kafka (déjà configuré):
- `KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092`
- `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092`

---

## Environnement Python

```bash
cd crypto-monitoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Lancer le Producteur (Kafka)

Env variables utiles (déjà gérées dans `run_producer.sh`):
- `SEND_EVERY_POLL=1` (envoi à chaque poll, même si prix identiques)
- `POLL_INTERVAL_SEC=10`

Lancer:
```bash
./run_producer.sh
```

Journal attendu (extraits):
- "Producer Kafka connecté avec succès!"
- "Envoi de 5 messages… → Flush took 0.0Xs → partition=0 offset=…"

Vérifier le topic (optionnel):
```bash
docker exec -it kafka kafka-run-class kafka.tools.GetOffsetShell \
	--broker-list localhost:9092 \
	--topic crypto-prices \
	--time -1
```

---

## Lancer le Consommateur (Spark → InfluxDB)

Le script `run_consumer.sh` prépare l’environnement (JAVA_HOME=17, PySpark avec venv) et les variables Influx:
- `INFLUX_URL=http://localhost:8086`
- `INFLUX_TOKEN=<token du docker-compose>`
- `INFLUX_ORG=crypto-org`
- `INFLUX_BUCKET=crypto-data`

Lancer:
```bash
./run_consumer.sh
```

Journal attendu (extraits):
- `Batch N stats => rows=5, min_event_ts=…`
- tableau par crypto (count)
- `Batch N: écrit 5 points dans InfluxDB (org=crypto-org, bucket=crypto-data)`

Checkpointing:
- Emplacement: `./checkpoints/crypto_consumer`
- Au redémarrage, le consumer reprend là où il s’est arrêté (rattrapage rapide des messages en retard).

---

## Vérifier dans InfluxDB UI

URL: http://localhost:8086 → login admin/adminpassword → Data Explorer

Guides rapides:
- Mesure: `crypto_price`
- Tag: `crypto` (bitcoin, ethereum, cardano, solana, polkadot)
- Fields: `price_usd` (principal), `price_eur`, etc.
- Choisir une fenêtre de temps couvrant l’activité (ex: Last 1h/3h).

Exemples Flux (Data Explorer → Script):
```flux
from(bucket: "crypto-data")
	|> range(start: -3h)
	|> filter(fn: (r) => r["_measurement"] == "crypto_price")
	|> filter(fn: (r) => r["_field"] == "price_usd")
	|> filter(fn: (r) => r.crypto =~ /^(bitcoin|ethereum|cardano|solana|polkadot)$/)
	|> aggregateWindow(every: 1m, fn: last, createEmpty: false)
	|> yield(name: "price_usd")
```

Astuce visibilité:
- Si le consumer a été arrêté un moment, il n’y a pas de points pendant la pause. Au redémarrage, un rattrapage écrit d’un coup les points manquants: élargir la fenêtre de temps pour les voir.

---

## Dépannage

- Producer bloque/timeout:
	- Vérifier Kafka up, port 9092 exposé, et `acks` est bien un entier (1) dans les env vars.
	- Relancer le producer via `run_producer.sh` qui nettoie les variables d’env conflictuelles.

- Consumer erreurs Java/Hadoop:
	- Utiliser Java 17: `export JAVA_HOME="$(/usr/libexec/java_home -v 17)"`
	- Flags de compat: `-Djava.security.manager=allow` (déjà ajoutés dans `run_consumer.sh`).

- Influx 401 / pas de points:
	- Vérifier `INFLUX_TOKEN`, `INFLUX_ORG`, `INFLUX_BUCKET` (identiques au docker-compose).
	- Regarder les logs consumer: `… écrit N points (org=…, bucket=…)`.

- Influx UI "No Results":
	- Ajuster la fenêtre de temps (Last 1h/3h) et sélectionner le bon field (`price_usd`).
	- Éviter d’inclure d’éventuelles séries de test (`/^test_/`).

- Offsets Kafka (sanity check):
	- GetOffsetShell (commande ci-dessus) pour voir l’avancement.

---

## Sécurité & Production
- Le token Influx actuel est un token d’init de dev. Pour la prod: créer un token dédié et retirer le token du compose.
- Mettre à jour les variables d’env via secrets/CI/CD.

---

## Étapes suivantes (suggestions)
- Nettoyer d’anciennes séries de test dans Influx.
- Créer un dashboard Grafana (BTC/ETH/SOL) sur `price_usd`.
- Ajouter un service Streamlit pour une UI légère.
- Alerting basique (seuils de variation 24h) via Influx Tasks ou un microservice Python.

---

## Référence fichiers
- `crypto_producer.py` — Producteur Kafka (CoinGecko → Kafka `crypto-prices`)
- `crypto_consumer_spark.py` — Consommateur Spark (Kafka → InfluxDB `crypto_price`)
- `docker-compose.yml` — Kafka, InfluxDB, Grafana
- `run_producer.sh` / `run_consumer.sh` — Scripts de lancement (macOS zsh)
- `requirements.txt` — Dépendances Python