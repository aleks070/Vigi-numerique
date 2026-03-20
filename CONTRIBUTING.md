# Guide technique — Vigi Numérique

Ce document est destiné aux membres de l'équipe. Il couvre l'architecture, la stack, et les commandes utiles au quotidien.

> Pour l'installation et le démarrage, voir le [README.md](./README.md).

---

## Architecture du projet

```
Vigi-numerique/
├── backend/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── requirements.txt           # Dépendances Python
│   ├── Dockerfile                 # Image Docker backend
│   ├── init.sql                   # Schéma PostgreSQL (8 tables)
│   ├── seed.sql                   # Données de référence (lignes, stations)
│   └── app/
│       ├── core/
│       │   └── config.py          # Variables d'environnement
│       ├── db/
│       │   ├── database.py        # Connexion SQLAlchemy async
│       │   └── models.py          # Modèles ORM (8 tables)
│       ├── api/
│       │   ├── network.py         # GET /network/status
│       │   ├── events.py          # GET /events, POST /events/{id}/qualify
│       │   ├── lines.py           # GET /lines
│       │   ├── stations.py        # GET /stations
│       │   └── map_layers.py      # GET /map/layers
│       ├── ingestion/
│       │   ├── prim_client.py     # Connecteur API PRIM (IDFM)
│       │   └── persistence.py     # Sauvegarde en PostgreSQL
│       └── scheduler.py           # Collecte toutes les 60s
├── frontend/
│   ├── Dockerfile                 # Image Docker frontend
│   └── src/
│       ├── App.jsx                # Routing React
│       ├── index.css              # Design system
│       ├── components/
│       │   └── Layout.jsx         # Sidebar + topbar
│       └── pages/
│           ├── Dashboard.jsx      # Vue supervision principale
│           ├── Events.jsx         # Page événements
│           └── Map.jsx            # Carte réseau
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.11 + FastAPI |
| Base de données | PostgreSQL 16 + PostGIS |
| Cache | Redis 7 |
| Scheduler | APScheduler |
| Source de données | API PRIM (IDFM) |
| Frontend | React 18 + Vite |
| Conteneurisation | Docker + Docker Compose |

---

## Accès au frontend

Il y a deux façons d'accéder au frontend selon le contexte :

| Mode | URL | Usage |
|------|-----|-------|
| Via Docker | http://localhost:3000 | Environnement complet, comme en prod |
| Via Vite (dev) | http://localhost:5173 | Développement frontend uniquement, hot reload plus rapide |

Pour le dev frontend isolé (sans Docker) :
```bash
cd frontend
npm install
npm run dev
```

---

## API PRIM — Endpoints utilisés

| Endpoint | Usage | Paramètres obligatoires |
|----------|-------|------------------------|
| `/general-message` | Perturbations officielles | `LineRef` |
| `/stop-monitoring` | Passages temps réel | `MonitoringRef` |
| `/line-timetable` | Horaires théoriques | `LineRef` + `MonitoringRef` |

> ⚠️ Limite : **1500 requêtes / 24h** — l'intervalle minimum est 60 secondes. Ne pas réduire `ALERT_POLL_INTERVAL` en dessous de 60.

---

## Endpoints backend

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Santé de l'API |
| GET | `/network/status` | État global du réseau |
| GET | `/events` | Liste des événements (filtres: line_id, status, severity) |
| GET | `/events/{id}` | Détail d'un événement |
| POST | `/events/{id}/qualify` | Qualification agent |
| GET | `/lines` | Référentiel lignes |
| GET | `/stations` | Référentiel stations |
| GET | `/map/layers` | Données GeoJSON pour la carte |

Documentation interactive disponible sur http://localhost:8000/docs

---

## Commandes Docker utiles

```bash
# Voir les logs en temps réel
docker-compose logs -f backend
docker-compose logs -f frontend

# Redémarrer un service
docker-compose restart backend

# Accéder à PostgreSQL
docker exec -it vigi_postgres psql -U vigi_user -d vigi

# Vérifier les données en base
docker exec -it vigi_postgres psql -U vigi_user -d vigi \
  -c "SELECT incident_id, line_id FROM official_incidents;"

# Arrêter tous les services
docker-compose down

# Reset complet (supprime les volumes et données)
docker-compose down -v
```

---

## Répartition de l'équipe

| Membre | Rôle |
|--------|------|
| À compléter | Backend / Ingestion PRIM |
| À compléter | Algorithmes de détection / Scoring |
| À compléter | Frontend / Dashboard |
| À compléter | Cybersécurité / Snowflake |