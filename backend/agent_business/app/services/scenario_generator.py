"""
Service Scenario Generator — orchestre market_study + risk_study + scoring
pour produire les N scénarios finaux (3 par défaut), triés par matching_score.

C'est ce service que le endpoint FastAPI appelle directement.
"""

from app.data.mock_production_costs import get_mock_production_cost_per_ha
from app.models.schemas import BusinessAdvisorRequest, BusinessScenario, CropRecommendation
from app.services.market_study import estimer_marche
from app.services.risk_study import evaluer_risque
from app.services.scoring import CandidatScoring, calculer_matching_scores


def _construire_candidat(
    crop: CropRecommendation,
    date_plantation,
    budget_input: float,
) -> tuple[CandidatScoring, dict]:
    """
    Calcule toutes les données intermédiaires pour une culture, et retourne :
    - le candidat prêt pour le scoring
    - un dict de données brutes réutilisées pour construire le scénario final
    """
    etude_marche = estimer_marche(crop, date_plantation)
    etude_risque = evaluer_risque(crop)

    cout_production_par_ha = get_mock_production_cost_per_ha(crop.culture)
    cout_total_par_ha = cout_production_par_ha + etude_risque.cout_mitigation_eur_par_ha

    profit_net_par_ha = etude_marche.profit_brut_par_ha - cout_total_par_ha
    superficie_max_financable_ha = round(budget_input / cout_total_par_ha, 2)

    candidat = CandidatScoring(
        culture=crop.culture,
        profit_net_par_ha=profit_net_par_ha,
        risque_normalise=etude_risque.risque_score_normalise,
        superficie_max_financable_ha=superficie_max_financable_ha,
    )

    donnees_brutes = {
        "etude_marche": etude_marche,
        "etude_risque": etude_risque,
        "cout_total_par_ha": cout_total_par_ha,
        "profit_net_par_ha": profit_net_par_ha,
        "superficie_max_financable_ha": superficie_max_financable_ha,
    }

    return candidat, donnees_brutes


def generer_scenarios(request: BusinessAdvisorRequest) -> list[BusinessScenario]:
    candidats: list[CandidatScoring] = []
    donnees_par_culture: dict[str, dict] = {}

    for crop in request.crop_recommendations:
        candidat, donnees = _construire_candidat(
            crop, request.date_plantation_prevue, request.budget_input
        )
        candidats.append(candidat)
        donnees_par_culture[crop.culture] = donnees

    scores = calculer_matching_scores(candidats, request.superficie_disponible_ha)

    # Tri par matching_score décroissant, on garde les N meilleurs
    cultures_triees = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_cultures = cultures_triees[: request.nb_scenarios]

    scenarios: list[BusinessScenario] = []
    for culture, score in top_cultures:
        donnees = donnees_par_culture[culture]
        etude_marche = donnees["etude_marche"]
        etude_risque = donnees["etude_risque"]

        superficie_conseillee_ha = round(
            min(request.superficie_disponible_ha, donnees["superficie_max_financable_ha"]), 2
        )
        profit_estime = round(donnees["profit_net_par_ha"] * superficie_conseillee_ha, 2)

        scenarios.append(
            BusinessScenario(
                terrain_id=request.terrain_id,
                budget_input=request.budget_input,
                culture=culture,
                quantite_par_ha=etude_marche.rendement_estime_kg_par_ha,
                profit_estime=profit_estime,
                risque_score=etude_risque.risque_score_normalise,
                risque_description=f"{etude_risque.risque_principal} — {etude_risque.description}",
                solution_risque=etude_risque.solution_mitigation,
                matching_score=score,
                etude_marche=etude_marche.model_dump(mode="json"),
                superficie_max_financable_ha=donnees["superficie_max_financable_ha"],
                superficie_conseillee_ha=superficie_conseillee_ha,
            )
        )

    return scenarios
