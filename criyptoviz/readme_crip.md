##  Démarrer le projet

```bash
# Démarrer Colima (ou lancer Docker Desktop)
colima start --cpu 4 --memory 8 --arch x86_64

# Vérifier le contexte Docker
docker context use colima   # ou "default" si Docker Desktop
docker info

# Aller dans le dossier infra
cd infra

# Builder et lancer tous les services
docker compose up --build
```

Accès :

* **Backend** : [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Frontend** : [http://127.0.0.1:3000](http://127.0.0.1:3000)

---

## Commandes Docker utiles

### Gestion des conteneurs

```bash
# Lister les conteneurs en cours d’exécution
docker ps

# Arrêter les services
docker compose down

# Relancer sans rebuild
docker compose up
```

### Logs

```bash
# Suivre les logs en direct
docker compose logs -f

# Logs d’un service spécifique (ex : backend)
docker compose logs -f backend
```

### Accès aux conteneurs

```bash
# Ouvrir un shell dans le backend
docker exec -it cryptoviz_backend bash

# Ouvrir un shell dans la DB (ex : Postgres)
docker exec -it cryptoviz_db psql -U <user> -d <database>
```

### Nettoyage

```bash
# Supprimer conteneurs arrêtés, images inutiles, volumes orphelins
docker system prune -af --volumes
```

---

## Raccourcis Colima

```bash
# Vérifier le statut de Colima
colima status

# Arrêter Colima
colima stop

# Redémarrer Colima
colima restart
```




cryptoviz/
  scraper/
  analytics/
  viewer/
  infra/
  docs/
