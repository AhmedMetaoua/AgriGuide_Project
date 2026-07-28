# Shared

Code commun à tous les agents :
- Modèles Pydantic partagés (LandProfile, BusinessScenario, etc. — doivent
  correspondre exactement aux tables de `database/schema.sql`)
- Clients pour les APIs externes déjà utilisés par plusieurs agents
  (ex: source de prix RNM/FranceAgriMer utilisée par Business ET Marketplace)
- Connexion DB commune (pool PostgreSQL/PostGIS)
- Utilitaires d'authentification (JWT, dépendances FastAPI communes)
