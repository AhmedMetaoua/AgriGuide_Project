from fastapi import APIRouter, Depends, HTTPException

from app.clients import agriculture_client, auth_client, business_client
from app.graph import JourneyError, run_journey_monitoring, run_journey_scenarios
from app.schemas import (
    AnalysisStatus,
    DecisionStatus,
    JourneyMonitoringRequest,
    JourneyMonitoringResponse,
    JourneyScenariosRequest,
    JourneyScenariosResponse,
    JourneyStatusResponse,
    TerrainStatus,
)
from app.security import bearer_token, get_current_user_id

router = APIRouter(prefix="/orchestrator/journey", tags=["journey"])


@router.post("/scenarios", response_model=JourneyScenariosResponse)
async def journey_scenarios(
    req: JourneyScenariosRequest,
    user_id: str = Depends(get_current_user_id),
    token: str = Depends(bearer_token),
):
    """
    Relais Agriculture -> Business en un seul appel.

    Remplace ce que le frontend fait aujourd'hui à la main (appeler
    /agriculture/analyze, lire crop_recommendations, puis rappeler
    /business/scenarios avec cette liste) — voir
    backend/orchestrator/app/graph.py pour le détail du relais.

    user_id n'est pas encore utilisé pour de la logique métier ici : il
    sert seulement à garantir qu'aucun appel ne passe sans JWT valide.
    Une vérification d'ownership terrain_id <-> user_id, si souhaitée en
    plus de celle déjà faite côté Business, viendrait ici.
    """
    agriculture_payload = {
        "point": req.point.model_dump(),
        "manual_geojson": req.manual_geojson,
        "terrain_id": req.terrain_id,
        "yield_objective_q_ha": req.yield_objective_q_ha,
    }
    business_payload_base = {
        "terrain_id": req.terrain_id,
        "budget_input": req.budget_input,
        "date_plantation_prevue": req.date_plantation_prevue.isoformat(),
        "nb_scenarios": req.nb_scenarios,
    }

    try:
        result = await run_journey_scenarios(
            agriculture_payload, business_payload_base, token
        )
    except JourneyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return JourneyScenariosResponse(**result)


@router.post("/monitoring", response_model=JourneyMonitoringResponse)
async def journey_monitoring(
    req: JourneyMonitoringRequest,
    user_id: str = Depends(get_current_user_id),
    token: str = Depends(bearer_token),
):
    """
    Relais Business (décision confirmée) -> Monitoring (briefing du jour)
    en un seul appel.

    Remplace ce que fait aujourd'hui frontend/src/routes/aujourd-hui.tsx à
    la main : lire GET /business/decisions/{terrain_id}/latest, puis
    reconstruire crops[] depuis decision.allocations avant d'appeler
    POST /monitoring/analyze. Voir app/graph.py pour le détail du relais,
    et JourneyMonitoringRequest pour ce qui reste côté frontend
    (farmer_name/location/hardware_inventory — déjà en mémoire client,
    pas la peine de re-router via l'orchestrateur).
    """
    monitoring_payload_base = {
        "farmer_name": req.farmer_name,
        "terrain_id": req.terrain_id,
        "location": req.location.model_dump(),
        "hardware_inventory": req.hardware_inventory,
    }

    try:
        result = await run_journey_monitoring(
            req.terrain_id, monitoring_payload_base, token
        )
    except JourneyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return JourneyMonitoringResponse(**result)


@router.get("/status/{terrain_id}", response_model=JourneyStatusResponse)
async def journey_status(
    terrain_id: str,
    user_id: str = Depends(get_current_user_id),
    token: str = Depends(bearer_token),
):
    """
    État réel du parcours pour ce terrain, agrégé depuis Auth (le terrain
    existe-t-il et appartient-il à ce user), Agriculture (a-t-il déjà été
    analysé — via le nouvel endpoint GET /agriculture/land-profile/{id})
    et Business (une décision est-elle confirmée).

    Aucun état n'est inventé ou persisté ici : chaque champ reflète une
    lecture directe d'un service existant, au moment de l'appel. Les
    trois lectures sont indépendantes (pas de dépendance entre elles,
    contrairement aux relais /scenarios et /monitoring), donc chacune
    dégrade séparément plutôt que de faire échouer les deux autres :
    un Business injoignable ne doit pas cacher que le terrain existe et
    a été analysé.
    """
    terrain_status = TerrainStatus(found=False)
    try:
        me = await auth_client.me(token)
        match = next((t for t in me.get("terrains", []) if t.get("id") == terrain_id), None)
        if match:
            terrain_status = TerrainStatus(
                found=True, nom=match.get("nom"), superficie_ha=match.get("superficie_ha")
            )
    except HTTPException:
        pass  # Auth injoignable/en erreur -> terrain_status reste found=False, pas un 500 pour le status entier

    analysis_status = AnalysisStatus(found=False)
    try:
        profile = await agriculture_client.get_land_profile(terrain_id)
        if profile:
            top = next(iter(profile.get("crop_recommendations") or []), None)
            analysis_status = AnalysisStatus(
                found=True,
                date_generation=profile.get("date_generation"),
                top_crop=top.get("culture") if top else None,
            )
    except HTTPException:
        pass

    decision_status = DecisionStatus(found=False)
    try:
        decision = await business_client.derniere_decision(terrain_id, token)
        decision_status = DecisionStatus(
            found=True,
            decision_id=decision.get("decision_id"),
            created_at=decision.get("created_at"),
            allocations=decision.get("allocations"),
        )
    except HTTPException:
        pass  # Inclut le 404 normal "pas encore de décision confirmée"

    return JourneyStatusResponse(
        terrain=terrain_status, analysis=analysis_status, decision=decision_status
    )
