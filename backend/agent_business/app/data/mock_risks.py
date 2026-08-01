"""
Simule le croisement avec le Bulletin de Santé du Végétal (BSV) régional.
À remplacer par les vrais BSV régionaux — voir README.md du module.
"""

_MOCK_CROP_RISKS: dict[str, dict] = {
    "tomate": {
        "risque_principal": "Mildiou",
        "description": "Risque fongique élevé en conditions humides, favorisé par une irrigation par aspersion.",
        "probabilite": 0.35,
        "impact": 0.60,
        "solution_mitigation": "Traitement préventif fongicide + passage en irrigation goutte-à-goutte",
        "cout_mitigation_eur_par_ha": 320.0,
    },
    "pomme_de_terre": {
        "risque_principal": "Mildiou de la pomme de terre",
        "description": "Maladie fongique majeure, surveillée par le BSV régional en période humide.",
        "probabilite": 0.40,
        "impact": 0.55,
        "solution_mitigation": "Traitement fongicide ciblé selon les alertes BSV",
        "cout_mitigation_eur_par_ha": 280.0,
    },
    "ble": {
        "risque_principal": "Rouille jaune",
        "description": "Risque fongique modéré, fortement dépendant du climat printanier.",
        "probabilite": 0.25,
        "impact": 0.40,
        "solution_mitigation": "Variétés résistantes + traitement fongicide léger",
        "cout_mitigation_eur_par_ha": 90.0,
    },
    "mais": {
        "risque_principal": "Pyrale du maïs",
        "description": "Ravageur courant, impact modéré sur le rendement en l'absence de traitement.",
        "probabilite": 0.30,
        "impact": 0.45,
        "solution_mitigation": "Lutte biologique (trichogrammes) ou insecticide ciblé",
        "cout_mitigation_eur_par_ha": 110.0,
    },
    "tournesol": {
        "risque_principal": "Dégâts d'oiseaux",
        "description": "Risque faible à modéré en phase de levée et à maturité.",
        "probabilite": 0.20,
        "impact": 0.30,
        "solution_mitigation": "Effaroucheurs et surveillance renforcée",
        "cout_mitigation_eur_par_ha": 40.0,
    },
}

_DEFAULT_CROP_RISK = {
    "risque_principal": "Risque générique",
    "description": "Aucune donnée de risque spécifique disponible pour cette culture.",
    "probabilite": 0.25,
    "impact": 0.40,
    "solution_mitigation": "Suivi phytosanitaire standard",
    "cout_mitigation_eur_par_ha": 100.0,
}


def get_mock_crop_risk(culture: str) -> dict:
    """Retourne le risque principal pour une culture (fallback générique si inconnue)."""
    return dict(_MOCK_CROP_RISKS.get(culture, _DEFAULT_CROP_RISK))
