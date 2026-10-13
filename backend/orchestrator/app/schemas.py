from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """Mirrors app.models.schemas.Coordinate in agent_agriculture."""
    lat: float
    lon: float


class JourneyScenariosRequest(BaseModel):
    """
    Input for POST /orchestrator/journey/scenarios — the relay this service
    exists to remove from the frontend: resolve the parcel + get crop
    recommendations from Agriculture, then generate financial scenarios
    from Business, in one call.

    terrain_id is required here (unlike Agriculture's own /analyze, where
    it's optional) because Business's /scenarios needs it for the
    server-side ownership/area check — a journey call with no terrain_id
    can't reach Business meaningfully anyway.
    """

    point: Coordinate
    manual_geojson: Optional[dict] = None
    terrain_id: str
    yield_objective_q_ha: Optional[float] = None

    budget_input: float = Field(gt=0)
    date_plantation_prevue: date
    nb_scenarios: int = Field(default=3, ge=1, le=5)


class JourneyScenariosResponse(BaseModel):
    """
    Both sub-agent responses passed through unmodified (as dicts, not
    re-declared field-for-field) so this file doesn't drift out of sync
    with app.models.schemas.AnalyzeResponse / BusinessAdvisorResponse in
    their respective services every time either one changes.
    """

    analysis: dict
    scenarios: dict


class LocationInput(BaseModel):
    """Mirrors app.models.schemas.LocationInput in agent_monitoring."""
    latitude: float
    longitude: float
    label: Optional[str] = None


class JourneyMonitoringRequest(BaseModel):
    """
    Input for POST /orchestrator/journey/monitoring — relaie la décision
    Business confirmée vers Monitoring, sans que le frontend ait à lire
    `decision.allocations` et reconstruire `crops[]` lui-même (voir
    frontend/src/routes/aujourd-hui.tsx, useEffect qui fait exactement ça
    aujourd'hui côté client).

    farmer_name / location / hardware_inventory restent fournis par le
    frontend plutôt que re-récupérés via Auth ici : ce sont des données du
    profil que le client a déjà en mémoire (contexte utilisateur chargé au
    login), donc un aller-retour serveur supplémentaire n'apporterait rien
    — contrairement à la décision Business, qui elle est le vrai relais
    inter-agents à déplacer côté serveur.
    """

    terrain_id: str
    farmer_name: str
    location: LocationInput
    hardware_inventory: list[str] = Field(default_factory=list)


class TerrainStatus(BaseModel):
    found: bool
    nom: Optional[str] = None
    superficie_ha: Optional[float] = None


class AnalysisStatus(BaseModel):
    found: bool
    date_generation: Optional[str] = None
    top_crop: Optional[str] = None


class DecisionStatus(BaseModel):
    found: bool
    decision_id: Optional[str] = None
    created_at: Optional[str] = None
    allocations: Optional[list[dict]] = None


class JourneyStatusResponse(BaseModel):
    """
    État réel du parcours d'un terrain, agrégé depuis les trois services
    qui en détiennent chacun un morceau — aucun état nouveau n'est
    inventé ou persisté ici, cet endpoint ne fait que lire ce qui existe
    déjà : Auth (le terrain existe et appartient à ce user), Agriculture
    (a-t-il déjà été analysé, via le nouvel endpoint
    GET /agriculture/land-profile/{terrain_id}), Business (une décision
    est-elle confirmée, réutilise le même client que le relais
    /journey/monitoring).
    """

    terrain: TerrainStatus
    analysis: AnalysisStatus
    decision: DecisionStatus


class JourneyMonitoringResponse(BaseModel):
    """Passthrough de AnalyzeResponse (agent_monitoring), même raison que
    JourneyScenariosResponse ci-dessus : éviter la re-déclaration champ à
    champ d'un schéma qui vit dans un autre service."""

    decision: dict
    briefing: dict
