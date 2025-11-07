# 🔧 Troubleshooting Guide - Crypto Monitoring Pipeline

## ❌ Problème : Données écrites mais invisibles dans InfluxDB

### Symptômes
```bash
# Consumer affiche succès
✅ Batch 117: 20 point(s) écrit(s) avec succès !
   Measurement: crypto_market
   Bucket: crypto-data

# Mais query InfluxDB retourne vide
docker exec -it influxdb influx query 'from(bucket: "crypto-data") |> range(start: 0) ...'
# → Aucun résultat
```

### Cause racine
**Problème de timestamp Spark → InfluxDB**

Quand on parse un timestamp ISO 8601 avec `col("timestamp").cast("timestamp")` dans Spark, puis qu'on l'envoie à InfluxDB via `.time(row.event_ts)`, **InfluxDB peut rejeter silencieusement les données** si :

1. **Le timestamp est dans le futur** (> now + quelques minutes)
2. **Le timestamp a un format/timezone incompatible**
3. **Le timestamp est trop ancien** (selon la retention policy)

### Pourquoi c'est sournois ?
- ✅ `write_api.write()` retourne **succès** (pas d'exception levée)
- ✅ Les logs affichent "X points écrits"
- ❌ Mais InfluxDB **ignore silencieusement** les points invalides
- ❌ Aucun message d'erreur visible

---

## ✅ Solution 1 : Laisser InfluxDB gérer le timestamp

**Le plus simple et le plus fiable** :

```python
# ❌ AVANT (problématique)
if row.event_ts is not None:
    p = p.time(row.event_ts)

# ✅ APRÈS (solution)
# Ne pas spécifier de timestamp → InfluxDB utilise l'heure d'arrivée
points.append(p)
```

**Avantages** :
- ✅ Timestamp toujours valide (heure serveur)
- ✅ Pas de problème de timezone
- ✅ Pas de risque de timestamps futurs

**Inconvénients** :
- ⚠️ Perte de la précision du timestamp original de l'API
- ⚠️ Décalage possible entre l'événement et son enregistrement

---

## ✅ Solution 2 : Forcer le timestamp en Python datetime naif

Si tu veux **vraiment** utiliser le timestamp de l'agent :

```python
from datetime import datetime, timezone

# Dans write_to_influx()
for row in batch.toLocalIterator():
    p = Point("crypto_market")
    # ... tags et fields ...
    
    # Convertir event_ts en datetime Python UTC
    if row.event_ts is not None:
        # Spark timestamp → Python datetime
        dt = row.event_ts.replace(tzinfo=timezone.utc)
        p = p.time(dt)
    
    points.append(p)
```

**Avantages** :
- ✅ Conserve le timestamp original de l'API
- ✅ Contrôle explicite sur le timezone (UTC)

**Inconvénients** :
- ⚠️ Plus complexe
- ⚠️ Risque de bugs si mal géré

---

## 🔍 Debugging : Comment vérifier si c'est un problème de timestamp ?

### 1. Tester avec timestamp auto (solution actuelle)
```python
# Désactiver temporairement le timestamp custom
# p = p.time(row.event_ts)  # Commenter cette ligne
```

Relancer consumer → Si données apparaissent → **C'est le timestamp !**

### 2. Vérifier les timestamps dans les logs
```python
# Ajouter un print debug
for row in batch.toLocalIterator():
    print(f"DEBUG: crypto_id={row.crypto_id}, event_ts={row.event_ts}, type={type(row.event_ts)}")
```

Cherche :
- ❌ `event_ts=None` → Parsing failed
- ❌ `event_ts=2025-11-07 25:99:99` → Timestamp invalide
- ❌ `event_ts=2026-01-01` → Timestamp dans le futur

### 3. Query avec range(start: 0)
```bash
# Voir TOUTES les données sans filtre temporel
docker exec -it influxdb influx query 'from(bucket: "crypto-data")
  |> range(start: 0)
  |> filter(fn: (r) => r["_measurement"] == "crypto_market")
  |> limit(n: 5)'
```

Si vide → **Les données ne sont PAS écrites** (problème plus profond que timestamp)

---

## 📊 Vérification de la configuration InfluxDB

### Vérifier organisation et bucket
```bash
# Lister les organisations
docker exec -it influxdb influx org list
# Résultat attendu : crypto-org

# Lister les buckets
docker exec -it influxdb influx bucket list
# Résultat attendu : crypto-data avec org ID correspondant
```

### Vérifier le token et permissions
```bash
docker exec -it influxdb influx auth list
```

Cherche ton token (premiers 10 caractères) et vérifie :
- ✅ `read:orgs/.../buckets`
- ✅ `write:orgs/.../buckets`

---

## 🎯 Checklist de debugging

Quand les données n'apparaissent pas dans InfluxDB :

1. ✅ **Consumer tourne ?** → Vérifier logs Spark
2. ✅ **Messages Kafka arrivent ?** → Vérifier "Batch X: Y ligne(s) reçue(s)"
3. ✅ **Écriture InfluxDB réussit ?** → Vérifier "✅ X point(s) écrit(s)"
4. ✅ **Bucket/Org corrects ?** → `docker exec influx org list` + `bucket list`
5. ✅ **Token valide ?** → `docker exec influx auth list`
6. ✅ **Timestamp valide ?** → Tester sans `.time()` (solution 1)
7. ✅ **Données vraiment absentes ?** → Query avec `range(start: 0)`

---

## 📝 Leçons apprises

### 🔑 Principe clé : InfluxDB est silencieux sur les erreurs de timestamp

**Contrairement à PostgreSQL ou MongoDB**, InfluxDB ne lève **PAS d'exception** si :
- Timestamp invalide
- Timestamp hors de la fenêtre de retention
- Timestamp dans le futur (> 5min)

→ **Les données sont juste ignorées silencieusement**

### 🎯 Best practice : Timestamp management

Pour un pipeline de production :

1. **Dev/Debug** : Pas de timestamp custom → Utiliser heure serveur
2. **Prod** : Timestamp custom **MAIS** avec validation :
   ```python
   now = datetime.now(timezone.utc)
   if abs((dt - now).total_seconds()) > 300:  # > 5 min
       print(f"⚠️  Timestamp suspect : {dt}, utilisation de now()")
       dt = now
   ```

---

## 🚀 Solution finale appliquée

**Fichier** : `consumer_prices.py` ligne ~223

```python
# TIMESTAMP - DÉSACTIVÉ (InfluxDB utilise heure d'arrivée)
# Raison : Évite les rejets silencieux de données
# Si besoin du timestamp original : implémenter solution 2 avec validation
# if row.event_ts is not None:
#     p = p.time(row.event_ts)

points.append(p)
```

**Résultat** :
- ✅ 20 cryptos visibles dans InfluxDB
- ✅ Timestamps automatiques = heure d'écriture (acceptable pour ce use case)
- ✅ Pas de perte de données silencieuse

---

## 📚 Références

- [InfluxDB Python Client - Time precision](https://influxdb-client.readthedocs.io/en/stable/usage.html#time-precision)
- [InfluxDB Best Practices - Timestamp handling](https://docs.influxdata.com/influxdb/v2.7/write-data/best-practices/schema-design/#timestamps)
- [PySpark Timestamp Handling](https://spark.apache.org/docs/latest/sql-ref-datetime-pattern.html)

---

**Créé le** : 7 novembre 2025  
**Contexte** : Pipeline CoinGeckoAgent → Kafka → Spark → InfluxDB  
**Mainteneur** : @elomokm
