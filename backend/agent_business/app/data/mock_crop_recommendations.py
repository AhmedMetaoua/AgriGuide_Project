"""
Simule la sortie de l'agent Agriculture (`crop_recommendations`).

Tant que `backend/agent_agriculture` n'expose pas encore de vrai endpoint,
l'agent Business (et son pipeline de démo/tests) consomme ces données
factices. Le format respecte exactement `CropRecommendation` dans
`app/models/schemas.py`, donc brancher le vrai agent plus tard ne demandera
que de remplacer l'appel à `get_mock_crop_recommendations()` par un appel
HTTP — aucun autre service n'a besoin de changer.
"""

from datetime import date

MOCK_TERRAIN_ID = "11111111-1111-1111-1111-111111111111"
MOCK_TERRAIN_SUPERFICIE_HA = 12.0
MOCK_DATE_PLANTATION = date(2026, 3, 15)

_MOCK_CROP_RECOMMENDATIONS: list[dict] = [
    {
        "rang": 1,
        "culture": "tomate",
        "score_compatibilite": 92.0,
        "cycle_jours": 90,
        "besoins_irrigation": {"niveau": "eleve", "mm_par_semaine": 35},
        "besoins_engrais": {"azote_kg_ha": 120, "phosphore_kg_ha": 60, "potassium_kg_ha": 150},
        "besoins_pesticides": {"traitements_par_saison": 4, "type": "fongicide + insecticide"},
        "feature_importance": {
            "sol_ph": 0.32,
            "ensoleillement": 0.28,
            "temperature_moyenne": 0.24,
            "historique_rpg": 0.16,
        },
    },
    {
        "rang": 2,
        "culture": "pomme_de_terre",
        "score_compatibilite": 87.0,
        "cycle_jours": 110,
        "besoins_irrigation": {"niveau": "modere", "mm_par_semaine": 25},
        "besoins_engrais": {"azote_kg_ha": 150, "phosphore_kg_ha": 80, "potassium_kg_ha": 200},
        "besoins_pesticides": {"traitements_par_saison": 3, "type": "fongicide (mildiou)"},
        "feature_importance": {
            "sol_texture": 0.35,
            "drainage": 0.30,
            "temperature_moyenne": 0.20,
            "historique_rpg": 0.15,
        },
    },
    {
        "rang": 3,
        "culture": "ble",
        "score_compatibilite": 81.0,
        "cycle_jours": 240,
        "besoins_irrigation": {"niveau": "faible", "mm_par_semaine": 10},
        "besoins_engrais": {"azote_kg_ha": 180, "phosphore_kg_ha": 50, "potassium_kg_ha": 60},
        "besoins_pesticides": {"traitements_par_saison": 2, "type": "fongicide leger"},
        "feature_importance": {
            "sol_ph": 0.30,
            "historique_rpg": 0.30,
            "ensoleillement": 0.22,
            "temperature_moyenne": 0.18,
        },
    },
    {
        "rang": 4,
        "culture": "mais",
        "score_compatibilite": 76.0,
        "cycle_jours": 150,
        "besoins_irrigation": {"niveau": "eleve", "mm_par_semaine": 30},
        "besoins_engrais": {"azote_kg_ha": 200, "phosphore_kg_ha": 70, "potassium_kg_ha": 100},
        "besoins_pesticides": {"traitements_par_saison": 2, "type": "herbicide + insecticide"},
        "feature_importance": {
            "temperature_moyenne": 0.34,
            "sol_texture": 0.28,
            "ensoleillement": 0.20,
            "historique_rpg": 0.18,
        },
    },
    {
        "rang": 5,
        "culture": "tournesol",
        "score_compatibilite": 70.0,
        "cycle_jours": 130,
        "besoins_irrigation": {"niveau": "faible", "mm_par_semaine": 8},
        "besoins_engrais": {"azote_kg_ha": 60, "phosphore_kg_ha": 40, "potassium_kg_ha": 50},
        "besoins_pesticides": {"traitements_par_saison": 1, "type": "surveillance oiseaux"},
        "feature_importance": {
            "ensoleillement": 0.40,
            "sol_ph": 0.25,
            "temperature_moyenne": 0.20,
            "historique_rpg": 0.15,
        },
    },
]


def get_mock_crop_recommendations() -> list[dict]:
    """Retourne une copie pour éviter toute mutation accidentelle par l'appelant."""
    return [dict(c) for c in _MOCK_CROP_RECOMMENDATIONS]
