# Avancement du projet — Vigi Numérique

Dernière mise à jour : 20 mars 2026

---

## ✅ Réalisé

### Infrastructure
- [x] Repository GitHub initialisé avec arborescence complète
- [x] Docker Compose — PostgreSQL, Redis, Backend, Frontend
- [x] Variables d'environnement (`.env.example`)
- [x] `.gitignore` propre (secrets exclus)

### Base de données
- [x] Schéma PostgreSQL — 8 tables opérationnelles avec index et foreign keys
- [x] Extension PostGIS activée
- [x] Données de référence — 19 lignes (RER + Métro), 26 stations RER A

### Backend FastAPI
- [x] Tous les endpoints du cahier des charges implémentés
- [x] Modèles ORM SQLAlchemy pour les 8 tables
- [x] Configuration centralisée via `.env`

### Pipeline PRIM
- [x] Connecteur PRIM async (perturbations, passages temps réel, horaires théoriques)
- [x] Normalisation des réponses SIRI
- [x] Scheduler — collecte toutes les 60 secondes
- [x] Persistence en PostgreSQL — incidents officiels sauvegardés ✓
- [x] Respect de la limite API (1500 req/24h)

### Frontend
- [x] React + Vite initialisé avec Dockerfile
- [x] Design system complet (CSS variables, typographie DM Sans)
- [x] Layout sidebar + topbar horloge live
- [x] Dashboard de supervision — KPIs, table événements, panneau détail + qualification
- [x] Pages placeholder Events et Map

---

## 🚧 À faire

### Backend — Priorité haute
- [ ] **Moteur de détection** (`backend/app/detection/`)
  - Calcul KPIs : ponctualité, régularité, taux de suppression
  - Score d'anomalie composite
  - Inférence état réseau (nominal → incident majeur)
  - Génération automatique d'événements
- [ ] Endpoint `/network/status` — calcul réel du score global
- [ ] Persistence passages temps réel — brancher les vrais stop_ref
- [ ] Intégration Snowflake

### Frontend — Priorité haute
- [ ] Brancher les vraies données API (remplacer les mocks)
- [ ] Page Carte — Leaflet + stations colorées par état
- [ ] Page Événements — filtres ligne / gravité / statut
- [ ] Qualification agent — connecter au `POST /events/{id}/qualify`

### Cybersécurité
- [ ] Authentification JWT
- [ ] RBAC (opérateur / superviseur / admin)
- [ ] Audit trail des qualifications

---

## 📅 Planning restant

| Jour | Objectif |
|------|----------|
| **Ven 20** ✅ | Infrastructure + Pipeline PRIM + Dashboard |
| **Sam 21** | Moteur de détection + Score d'anomalie + Carte Leaflet |
| **Dim 22** | Brancher front sur back + Qualification + Snowflake |
| **Lun 23** | Tests, stabilisation |
| **Mar 24** | Vérifications, répetitions speech |
| **Mer 25** | Présentation jury |

---

## ⚠️ Points d'attention

- **Limite API PRIM** : 1500 req/24h → ne pas descendre sous 60s d'intervalle
- **Jeton PRIM** : dans `.env` uniquement — ne jamais commiter
- **Snowflake** : compte disponible — intégration à planifier en équipe