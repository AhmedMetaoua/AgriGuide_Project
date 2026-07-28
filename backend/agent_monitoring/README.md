# Agent Monitoring (Suivi quotidien)

**Rôle** : accompagner le farmer une fois la décision confirmée — alertes,
carnet de bord, suivi financier, et déclenchement des suggestions marketplace.

## Fonctionnement
Tâches Celery Beat (cron), pas des réponses à une question directe :
- Vérification météo quotidienne par culture active → recommandations
  irrigation → `alerts`
- Croisement des bulletins phytosanitaires régionaux (BSV) avec les cultures
  actives → `alerts` (niveau_urgence selon gravité)
- Rappels d'échéances administratives (lié à `dossiers_administratifs`)
- Détection de la fenêtre de récolte via
  `decision_allocations.date_maturite_prevue` → déclenche une suggestion
  d'annonce marketplace (voir `backend/marketplace/README.md`)

## Sortie
- `monitoring_logs` (carnet de bord)
- `alerts`
- `cost_tracking` (comparaison budget réel vs. estimé)
- Notifications envoyées via le canal choisi (`notification_preferences`)

## Ne PAS faire ici
Pas de nouvel agent conversationnel — ce module est piloté par des jobs
planifiés, pas par des requêtes utilisateur en direct (celles-ci passent par
l'orchestrateur vers les autres agents).
