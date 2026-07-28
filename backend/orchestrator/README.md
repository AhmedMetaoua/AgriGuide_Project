# Orchestrateur (Agent superviseur)

**Rôle** : point d'entrée unique. Route chaque requête vers le bon
sous-agent selon l'intention détectée et l'état courant du farmer
(voir `docs/ARCHITECTURE.md` section 2 — state machine).

## Stack
LangGraph — un nœud "router" qui décide, plutôt qu'un menu manuel côté
frontend (même si le frontend garde aussi une navigation explicite par
onglets pour les utilisateurs qui préfèrent cliquer que discuter).

## Ne fait AUCUN traitement métier
Uniquement du routage + agrégation de contexte (terrain_id, état, historique
récent) à transmettre au sous-agent choisi.

## Endpoint principal
`POST /chat {user_id, terrain_id, message}` → détermine l'agent cible →
transmet → renvoie la réponse formatée au frontend.
