"""
Classification de la sensibilité hydrique d'une culture (low | moderate | high)
à partir du besoin d'irrigation persisté par l'agent Agriculture.

Source : `besoins_irrigation` (voir agent_agriculture `estimate_irrigation`) :
    irrigation_need_mm     = max(0, ETc - pluie efficace) sur la fenêtre de prévision
    irrigation_window_days = longueur de cette fenêtre (jours de prévision Open-Meteo)

On normalise en mm/jour pour que le seuil ne dépende pas de la longueur de la
fenêtre de prévision :

    mm/jour <  LOW_MAX   -> "low"
    mm/jour <  HIGH_MIN  -> "moderate"
    mm/jour >= HIGH_MIN  -> "high"

⚠️ Seuils de départ (décision produit, pas une norme agronomique) : ils portent
sur un besoin net sur ~16 jours de prévision, pas sur un bilan de saison. Ils
sont surchargeables par variables d'environnement pour pouvoir les recaler sans
toucher au code. Une donnée absente ou incohérente renvoie None (champ
optionnel côté Monitoring) plutôt qu'une valeur inventée.

Garder les mêmes seuils que frontend/src/lib/waterSensitivity.ts.
"""
from __future__ import annotations

import os
from typing import Any, Optional

LOW_MAX_MM_PER_DAY: float = float(os.getenv("WATER_SENSITIVITY_LOW_MAX_MM_DAY", "1.0"))
HIGH_MIN_MM_PER_DAY: float = float(os.getenv("WATER_SENSITIVITY_HIGH_MIN_MM_DAY", "2.5"))


def classify_water_sensitivity(besoins_irrigation: Optional[dict[str, Any]]) -> Optional[str]:
    if not isinstance(besoins_irrigation, dict):
        return None
    need = besoins_irrigation.get("irrigation_need_mm")
    window = besoins_irrigation.get("irrigation_window_days")
    if not isinstance(need, (int, float)) or isinstance(need, bool):
        return None
    if not isinstance(window, (int, float)) or isinstance(window, bool) or window <= 0:
        return None
    per_day = float(need) / float(window)
    if per_day < LOW_MAX_MM_PER_DAY:
        return "low"
    if per_day < HIGH_MIN_MM_PER_DAY:
        return "moderate"
    return "high"
