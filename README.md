# 🚦 Vigi Numérique

> Real-time detection of disruptions on the Île-de-France transit network — early alert system for SNCF, RATP & other agents.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📌 Contexte

Dans le cadre de l'ouverture à la concurrence du réseau Île-de-France Mobilités, les opérateurs de transport (SNCF, RATP et futurs entrants) ont besoin d'outils capables de détecter les situations perturbées **avant** qu'elles ne soient officiellement déclarées.

**Vigi Numérique** est une plateforme de supervision en temps réel qui ingère les flux de données live IDFM, les compare au plan de transport théorique, et génère des alertes précoces à destination des agents de production.

---

## 🎯 Objectifs

- Récupérer les données de transport en temps réel via les APIs IDFM (GTFS-RT, PRIM)
- Comparer les données théoriques aux données réelles pour identifier les dérives
- Détecter automatiquement les anomalies : retards, suppressions, écarts de fréquence
- Alerter les agents via un dashboard interactif et un agent conversationnel
- Permettre une orientation proactive du réseau pour limiter l'impact client

---

## 🏗️ Architecture

```
vigi-numerique/
├── backend/
│   ├── api/                  # Routes FastAPI
│   ├── ingestion/            # Connecteurs APIs IDFM (GTFS-RT, PRIM)
│   ├── detection/            # Algorithmes de détection d'anomalies
│   ├── alerts/               # Moteur d'alertes et scoring
│   └── models/               # Schémas de données (Pydantic)
├── frontend/
│   ├── src/
│   │   ├── components/       # Composants React
│   │   ├── pages/            # Dashboard, carte réseau, alertes
│   │   └── hooks/            # WebSocket, polling live data
│   └── public/
├── data/
│   └── gtfs/                 # Données statiques GTFS (plan théorique)
├── security/
│   └── auth/                 # Authentification agents, RBAC
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔌 Sources de données

| API | Contenu | Fréquence |
|-----|---------|-----------|
| [GTFS-RT IDFM](https://prim.iledefrance-mobilites.fr/) | Positions trains, retards en temps réel | 30 secondes |
| [PRIM](https://prim.iledefrance-mobilites.fr/) | Horaires théoriques, informations trafic | Temps réel |
| [SIRI / Disruptions](https://prim.iledefrance-mobilites.fr/) | Incidents officiellement déclarés | Temps réel |

---

## 📊 KPIs de détection

Les alertes sont générées à partir des indicateurs suivants :

- **Retard moyen** — écart entre l'heure théorique et l'heure réelle sur une ligne
- **Taux de suppression** — pourcentage de trains/bus supprimés sur une fenêtre glissante
- **Écart de fréquence** — intervalle entre passages anormalement long
- **Score d'anomalie global** — score composite pondéré par ligne, permettant la priorisation
- **Propagation réseau** — détection de l'impact potentiel sur les lignes interconnectées

---

## ⚙️ Stack technique

**Backend**
- Python 3.11 + FastAPI
- Redis (cache temps réel + pub/sub alertes)
- PostgreSQL (historique, plan de transport théorique)
- Celery ou APScheduler (tâches périodiques d'ingestion)

**Frontend**
- React 18 + Vite
- WebSockets pour le temps réel
- Leaflet ou Mapbox (carte du réseau)
- Recharts / Chart.js (KPIs)

**Infrastructure**
- Docker + Docker Compose
- Nginx (reverse proxy)
- GitHub Actions (CI/CD)

**Sécurité**
- Authentification JWT pour les agents
- RBAC (différents niveaux d'accès : opérateur, superviseur, admin)
- HTTPS obligatoire, secrets via variables d'environnement
- Audit trail des alertes et actions

---

## 🚀 Installation

### Prérequis

- Docker & Docker Compose
- Clé API IDFM (à obtenir sur [prim.iledefrance-mobilites.fr](https://prim.iledefrance-mobilites.fr/))
- Python 3.11+ (pour le développement local)
- Node.js 20+ (pour le frontend)

### Lancement rapide (Docker)

```bash
# 1. Cloner le repo
git clone https://github.com/aleks070/Vigi-numerique.git
cd Vigi-numerique

# 2. Configurer les variables d'environnement
cp .env.example .env
# → Renseigner IDFM_API_KEY et les autres variables dans .env

# 3. Lancer les services
docker-compose up --build

# L'application est disponible sur http://localhost:3000
# L'API backend sur http://localhost:8000
# La doc API (Swagger) sur http://localhost:8000/docs
```

### Développement local (sans Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (dans un autre terminal)
cd frontend
npm install
npm run dev
```

---

## 🔐 Variables d'environnement

Copier `.env.example` en `.env` et renseigner les valeurs :

```env
# API IDFM
IDFM_API_KEY=your_api_key_here

# Base de données
POSTGRES_URL=postgresql://user:password@localhost:5432/vigi
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET=your_secret_key
JWT_EXPIRY=3600

# Config
ALERT_POLL_INTERVAL=30        # Intervalle d'ingestion en secondes
DELAY_THRESHOLD_SECONDS=180   # Seuil de retard pour déclencher une alerte
SUPPRESSION_THRESHOLD=0.2     # Taux de suppression (20%)
```

---

## 👥 Équipe

| Membre | Rôle |
|--------|------|
| À compléter | Backend / Data pipeline |
| À compléter | Algorithmes de détection |
| À compléter | Frontend / Dashboard |
| À compléter | Cybersécurité / DevOps |

---

## 📅 Roadmap

- [x] Définition de l'architecture
- [ ] Pipeline d'ingestion GTFS-RT
- [ ] Algorithmes de détection et scoring
- [ ] Dashboard temps réel
- [ ] Agent conversationnel
- [ ] Tests end-to-end
- [ ] Documentation technique finale

---

## 📄 Licence

Université Paris 8 — Hackhathon, groupe 5 SNCF — mars 2026
