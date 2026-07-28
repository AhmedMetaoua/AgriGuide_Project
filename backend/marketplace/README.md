# Module Marketplace (économie circulaire)

**Rôle** : petites annonces pour récoltes et déchets agricoles valorisables.
Pas de paiement, pas de livraison — juste description + prix/quantité +
contact.

## Ce n'est PAS un agent
CRUD classique FastAPI. Le seul appel LLM (Mistral) sert à :
- suggérer une description d'utilité pour un déchet (via `dechets_reference`
  comme base fiable, le LLM reformule/complète)
- rédiger le titre/description d'une annonce à partir des champs structurés

## Déclenchement
L'agent Monitoring détecte la fenêtre de récolte et appelle ce module pour
préparer une suggestion d'annonce (prix suggéré via la même source RNM que
l'agent Business, quantité déduite de `decision_allocations`).

## Endpoints principaux
- `POST /annonces` — créer une annonce (récolte ou déchet)
- `GET /annonces?type=&region=&culture=` — parcourir/filtrer
- `PATCH /annonces/{id}/statut` — disponible → réservé → expiré
- `GET /dechets_reference?culture=` — utilités suggérées pour une culture

## Modération minimale
Seuls les farmers authentifiés (terrain vérifié) peuvent publier — pas de
post anonyme, pas de compte non lié à un terrain.
