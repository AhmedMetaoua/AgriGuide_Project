# Agent Business

**Rôle** : à partir des crop_recommendations + budget, proposer 3 scénarios
chiffrés (quantité/ha, profit estimé, risque, solution au risque).

## Entrée
- `crop_recommendations` (top 5 + besoins) du terrain
- `budget_input` fourni par le farmer

## Calcul du matching score (formule explicite, PAS le LLM)
```
score = w1 * profit_normalise + w2 * (1 - risque_normalise) + w3 * fit_budget
```
Les poids w1/w2/w3 sont à calibrer et documenter ici une fois fixés.
Le LLM (Mistral) sert uniquement à rédiger la narration/explication du
scénario, jamais à calculer le score lui-même.

## Sources de données
Prix de marché réels via RNM / FranceAgriMer (pas une pure estimation LLM).

## Sortie (écrit en base)
- `business_scenarios` : 3 scénarios par culture retenue
- Après confirmation du farmer (human-in-the-loop) :
  `farmer_decisions` + `decision_allocations`
  (inclut `date_maturite_prevue`, utilisée plus tard par l'agent Monitoring)
