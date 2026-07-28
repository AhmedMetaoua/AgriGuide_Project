# Agent Agriculture

**Rôle** : analyser un terrain (géo/sol/climat) et recommander les 5 meilleures cultures.

## Réutilise le projet existant
Ce module reprend directement le pipeline déjà développé : FastAPI qui
interroge Sentinel-2, SoilGrids, NASA POWER, Open-Meteo, Open-Elevation,
réduit le tout en `LandProfile` JSON, puis passe au RandomForest entraîné.

## Entrée
`terrain_id` (géométrie déjà enregistrée dans `terrains`)

## Sortie (écrit en base)
- `land_profiles` : sol, satellite, RPG, climat, élévation
- `crop_recommendations` : top 5 cultures avec score + besoins (pesticides,
  engrais, irrigation) + feature_importance pour l'explicabilité

## À ajouter par rapport à l'existant
- Module BSV (Bulletin de Santé du Végétal) : croiser les données climatiques
  régionales avec les risques phytosanitaires connus (scarabée japonais,
  charançon rouge...) — anticiper le problème n°2 dès cette étape.
- Endpoint stub minimal pour débloquer les autres lots pendant le dev :
  `POST /agriculture/analyze {terrain_id}` → renvoie un LandProfile factice
  respectant le schéma.
