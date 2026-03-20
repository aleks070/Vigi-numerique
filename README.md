# 🚦 Vigi Numérique

> Détection précoce de situations perturbées sur le réseau Île-de-France — outil de supervision en quasi temps réel pour les agents SNCF & RATP.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)

---

## Contexte

Dans le cadre de l'ouverture à la concurrence du réseau Île-de-France Mobilités, les opérateurs ont besoin de détecter les situations perturbées **avant** qu'elles soient officiellement déclarées. Vigi Numérique ingère les flux live PRIM, les compare au plan de transport théorique, et génère des alertes précoces à destination des agents de production.

---

## Démarrage rapide

### Prérequis
- Docker Desktop installé et lancé
- Un jeton API IDFM (PRIM) — à demander à l'équipe

### Lancement

```bash
# 1. Cloner
git clone https://github.com/aleks070/Vigi-numerique.git
cd Vigi-numerique

# 2. Configurer
#cp .env.example .env

# → Renseigner IDFM_API_KEY dans .env

# 3. Lancer
docker-compose up --build
```

### Accès

| Service | URL |
|---------|-----|
| Dashboard (frontend) | http://localhost:3000 |
| API backend | http://localhost:8000 |
| Documentation API | http://localhost:8000/docs |

### Première utilisation (une seule fois)

```bash
docker exec -i vigi_postgres psql -U vigi_user -d vigi < backend/seed.sql
```

---

## Documentation

| Fichier | Contenu |
|---------|---------|
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Architecture, stack, commandes utiles |
| [PROGRESS.md](./PROGRESS.md) | Avancement et tâches restantes |

---

## Équipe

Université Paris 8 — Hackhathon, groupe 5 SNCF — mars 2026
- Aleksandar Mihajlovic
- Ousmane Abdoulaye Souley
- Guedalia Loubaton
- Amina Lekkam
