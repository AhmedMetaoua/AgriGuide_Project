"""
Graphes LangGraph des relais de parcours (pas encore de routage par
intention — voir backend/orchestrator/README.md pour la cible : un nœud
"router" qui choisit l'agent selon le message + l'état
farmer_decisions.statut). Ces graphes sont une première tranche de ce
routeur : la partie déterministe des relais (aucune classification
d'intention nécessaire, juste un passage propre de données entre agents).

Style calqué sur backend/agent_monitoring/app/agent/graph.py.
"""
from typing import Any, Optional, TypedDict

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from app.clients import agriculture_client, business_client, monitoring_client
from app.water_sensitivity import classify_water_sensitivity


def _error_state(exc: Exception, prefix: str) -> dict:
    """
    Construit {"error", "error_status"} à partir d'une exception levée par
    un client sous-agent. Si c'est une HTTPException (le cas normal — voir
    clients/*.py, qui lèvent toujours ça pour un statut >= 400 ou un
    service injoignable), le status_code d'origine est conservé : un 404
    "aucune décision confirmée" doit rester un 404 pour le frontend, pas
    devenir un 502 générique indiscernable d'une vraie panne.
    """
    if isinstance(exc, HTTPException):
        return {"error": f"{prefix} : {exc.detail}", "error_status": exc.status_code}
    return {"error": f"{prefix} : {exc}", "error_status": 502}


class JourneyError(RuntimeError):
    """Porte le status_code d'origine jusqu'au routeur FastAPI."""

    def __init__(self, detail: str, status_code: int = 502):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Graphe Agriculture -> Business : analyse de parcelle puis scénarios
# financiers, sans transformation manuelle côté frontend.
# ---------------------------------------------------------------------------


class JourneyState(TypedDict):
    agriculture_payload: dict
    business_payload_base: dict  # tout sauf crop_recommendations, ajouté après l'appel Agriculture
    bearer_token: str
    analysis: Optional[dict]
    scenarios: Optional[dict]
    error: Optional[str]
    error_status: Optional[int]


async def call_agriculture_node(state: JourneyState) -> JourneyState:
    if state.get("error"):
        return state
    try:
        analysis = await agriculture_client.analyze(state["agriculture_payload"])
        return {**state, "analysis": analysis}
    except Exception as exc:  # noqa: BLE001 — surfaced as journey error
        return {**state, **_error_state(exc, "Étape Agriculture échouée")}


async def call_business_node(state: JourneyState) -> JourneyState:
    if state.get("error"):
        return state
    analysis = state["analysis"]
    if not analysis:
        return {**state, "error": "Aucune analyse Agriculture disponible.", "error_status": 502}

    crop_recommendations = analysis.get("crop_recommendations")
    if not crop_recommendations:
        return {
            **state,
            "error": (
                "L'agent Agriculture n'a renvoyé aucune culture recommandée "
                "pour ce terrain — impossible de générer des scénarios."
            ),
            "error_status": 422,
        }

    area_ha = (analysis.get("parcel") or {}).get("area_ha")
    if not area_ha or area_ha <= 0:
        return {
            **state,
            "error": (
                "La parcelle analysée n'a pas de surface résolue "
                "(cadastre/RPG/manuel) — impossible de calculer des scénarios "
                "sans superficie_disponible_ha."
            ),
            "error_status": 422,
        }

    # Passage direct sans transformation : CropRecommendationOut (Agriculture)
    # et CropRecommendation (Business) ont exactement les mêmes champs
    # (rang, culture, score_compatibilite, cycle_jours, besoins_irrigation,
    # besoins_engrais, besoins_pesticides, feature_importance).
    # superficie_disponible_ha vient de la résolution de parcelle Agriculture ;
    # Business la re-vérifie de toute façon server-side contre `terrains`
    # (ownership + surface authoritative), donc cette valeur n'a besoin
    # d'être qu'un point de départ cohérent, pas la source de vérité finale.
    business_payload = {
        **state["business_payload_base"],
        "superficie_disponible_ha": area_ha,
        "crop_recommendations": crop_recommendations,
    }
    try:
        scenarios = await business_client.obtenir_scenarios(
            business_payload, state["bearer_token"]
        )
        return {**state, "scenarios": scenarios}
    except Exception as exc:  # noqa: BLE001
        return {**state, **_error_state(exc, "Étape Business échouée")}


def build_journey_graph():
    workflow = StateGraph(JourneyState)
    workflow.add_node("call_agriculture", call_agriculture_node)
    workflow.add_node("call_business", call_business_node)
    workflow.add_edge(START, "call_agriculture")
    workflow.add_edge("call_agriculture", "call_business")
    workflow.add_edge("call_business", END)
    return workflow.compile()


journey_graph = build_journey_graph()


async def run_journey_scenarios(
    agriculture_payload: dict, business_payload_base: dict, bearer_token: str
) -> dict:
    initial: JourneyState = {
        "agriculture_payload": agriculture_payload,
        "business_payload_base": business_payload_base,
        "bearer_token": bearer_token,
        "analysis": None,
        "scenarios": None,
        "error": None,
        "error_status": None,
    }
    result: dict[str, Any] = await journey_graph.ainvoke(initial)
    if result.get("error"):
        raise JourneyError(result["error"], result.get("error_status") or 502)
    return {"analysis": result["analysis"], "scenarios": result["scenarios"]}


# ---------------------------------------------------------------------------
# Graphe Business -> Monitoring : relaie la décision confirmée vers le
# briefing du jour (voir JourneyMonitoringRequest dans app/schemas.py pour
# le détail de ce qui reste côté frontend vs ce qui passe ici).
# ---------------------------------------------------------------------------


class MonitoringJourneyState(TypedDict):
    terrain_id: str
    monitoring_payload_base: dict  # farmer_name, location, hardware_inventory, terrain_id
    bearer_token: str
    decision: Optional[dict]
    water_by_crop: dict  # culture -> "low" | "moderate" | "high" (vide si indisponible)
    briefing: Optional[dict]
    error: Optional[str]
    error_status: Optional[int]


def _crops_from_allocations(
    allocations: list[dict], water_by_crop: Optional[dict] = None
) -> list[dict]:
    """
    Traduit decision.allocations (Business) vers crops[] (Monitoring) :
    culture -> crop_name, hectares_alloues -> hectares.

    `water_sensitivity` est ajouté quand il a pu être dérivé du besoin
    d'irrigation persisté par Agriculture (voir fetch_water_node et
    app/water_sensitivity.py). Champ optionnel côté Monitoring : absent
    si le terrain n'a jamais été analysé ou si Agriculture est injoignable.
    """
    water_by_crop = water_by_crop or {}
    crops = []
    for a in allocations:
        crop = {"crop_name": a["culture"], "hectares": a["hectares_alloues"]}
        water = water_by_crop.get(a["culture"])
        if water:
            crop["water_sensitivity"] = water
        crops.append(crop)
    return crops


async def fetch_decision_node(state: MonitoringJourneyState) -> MonitoringJourneyState:
    if state.get("error"):
        return state
    try:
        decision = await business_client.derniere_decision(
            state["terrain_id"], state["bearer_token"]
        )
        return {**state, "decision": decision}
    except Exception as exc:  # noqa: BLE001
        return {**state, **_error_state(exc, "Étape Business (décision) échouée")}


async def fetch_water_node(state: MonitoringJourneyState) -> MonitoringJourneyState:
    """
    Best-effort : lit le land_profile persisté (GET /agriculture/land-profile)
    et dérive la sensibilité hydrique par culture. N'échoue JAMAIS le relais :
    sans donnée, le briefing est simplement un peu moins précis.
    """
    if state.get("error"):
        return state
    water: dict = {}
    try:
        profile = await agriculture_client.get_land_profile(state["terrain_id"])
        for rec in (profile or {}).get("crop_recommendations") or []:
            level = classify_water_sensitivity(rec.get("besoins_irrigation"))
            if level and rec.get("culture"):
                water[rec["culture"]] = level
    except Exception:  # noqa: BLE001 - dégradation volontaire, voir docstring
        water = {}
    return {**state, "water_by_crop": water}


async def call_monitoring_node(state: MonitoringJourneyState) -> MonitoringJourneyState:
    if state.get("error"):
        return state
    decision = state["decision"]
    if not decision:
        return {**state, "error": "Aucune décision Business disponible.", "error_status": 502}

    allocations = decision.get("allocations") or []
    if not allocations:
        return {
            **state,
            "error": "La décision confirmée ne contient aucune allocation de culture.",
            "error_status": 422,
        }

    monitoring_payload = {
        **state["monitoring_payload_base"],
        "crops": _crops_from_allocations(allocations, state.get("water_by_crop")),
    }
    try:
        briefing = await monitoring_client.analyze(monitoring_payload)
        return {**state, "briefing": briefing}
    except Exception as exc:  # noqa: BLE001
        return {**state, **_error_state(exc, "Étape Monitoring échouée")}


def build_monitoring_journey_graph():
    workflow = StateGraph(MonitoringJourneyState)
    workflow.add_node("fetch_decision", fetch_decision_node)
    workflow.add_node("fetch_water", fetch_water_node)
    workflow.add_node("call_monitoring", call_monitoring_node)
    workflow.add_edge(START, "fetch_decision")
    workflow.add_edge("fetch_decision", "fetch_water")
    workflow.add_edge("fetch_water", "call_monitoring")
    workflow.add_edge("call_monitoring", END)
    return workflow.compile()


monitoring_journey_graph = build_monitoring_journey_graph()


async def run_journey_monitoring(
    terrain_id: str, monitoring_payload_base: dict, bearer_token: str
) -> dict:
    initial: MonitoringJourneyState = {
        "terrain_id": terrain_id,
        "monitoring_payload_base": monitoring_payload_base,
        "bearer_token": bearer_token,
        "decision": None,
        "water_by_crop": {},
        "briefing": None,
        "error": None,
        "error_status": None,
    }
    result: dict[str, Any] = await monitoring_journey_graph.ainvoke(initial)
    if result.get("error"):
        raise JourneyError(result["error"], result.get("error_status") or 502)
    return {"decision": result["decision"], "briefing": result["briefing"]}
