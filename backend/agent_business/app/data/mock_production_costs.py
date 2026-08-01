"""
Barème simulé des coûts de production par hectare et par culture (hors coût
de mitigation du risque, déjà géré séparément dans `mock_risks.py`).
"""

_MOCK_PRODUCTION_COSTS: dict[str, float] = {
    "tomate": 9500.0,
    "pomme_de_terre": 4200.0,
    "ble": 950.0,
    "mais": 1400.0,
    "tournesol": 650.0,
}

_DEFAULT_PRODUCTION_COST_EUR_PAR_HA = 1000.0


def get_mock_production_cost_per_ha(culture: str) -> float:
    """Retourne le coût de production par ha pour une culture (fallback générique si inconnue)."""
    return _MOCK_PRODUCTION_COSTS.get(culture, _DEFAULT_PRODUCTION_COST_EUR_PAR_HA)
