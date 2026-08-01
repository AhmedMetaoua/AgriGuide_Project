"""
Simule la source RNM / FranceAgriMer (prix de marché + rendement moyen par
culture). À remplacer par un vrai appel API — voir README.md du module,
section "Prochaines étapes".
"""

_MOCK_MARKET_PRICES: dict[str, dict] = {
    "tomate": {
        "prix_moyen_eur_par_kg": 0.85,
        "rendement_moyen_kg_par_ha": 65000,
        "tendance": 0.10,
        "source": "RNM/FranceAgriMer (simulé)",
    },
    "pomme_de_terre": {
        "prix_moyen_eur_par_kg": 0.28,
        "rendement_moyen_kg_par_ha": 38000,
        "tendance": -0.05,
        "source": "RNM/FranceAgriMer (simulé)",
    },
    "ble": {
        "prix_moyen_eur_par_kg": 0.22,
        "rendement_moyen_kg_par_ha": 7200,
        "tendance": 0.03,
        "source": "RNM/FranceAgriMer (simulé)",
    },
    "mais": {
        "prix_moyen_eur_par_kg": 0.19,
        "rendement_moyen_kg_par_ha": 9500,
        "tendance": -0.08,
        "source": "RNM/FranceAgriMer (simulé)",
    },
    "tournesol": {
        "prix_moyen_eur_par_kg": 0.48,
        "rendement_moyen_kg_par_ha": 2800,
        "tendance": 0.12,
        "source": "RNM/FranceAgriMer (simulé)",
    },
}

_DEFAULT_MARKET_PRICE = {
    "prix_moyen_eur_par_kg": 0.30,
    "rendement_moyen_kg_par_ha": 5000,
    "tendance": 0.0,
    "source": "RNM/FranceAgriMer (estimation générique)",
}


def get_mock_market_price(culture: str) -> dict:
    """Retourne prix/rendement/tendance pour une culture (fallback générique si inconnue)."""
    return dict(_MOCK_MARKET_PRICES.get(culture, _DEFAULT_MARKET_PRICE))
