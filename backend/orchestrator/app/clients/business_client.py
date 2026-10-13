"""Client HTTP pour agent_business (port 8006 en local, cf. config.py)."""
from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.config import BUSINESS_URL, SUB_AGENT_TIMEOUT_S


async def obtenir_scenarios(payload: dict, bearer_token: str) -> dict:
    """
    Appelle POST /business/scenarios. Le JWT du farmer est transmis tel
    quel : agent_business fait sa propre vérification d'ownership du
    terrain (voir app/routers/business.py::_authoritative_area) et
    l'orchestrateur ne doit pas contourner ça.
    """
    url = f"{BUSINESS_URL}/business/scenarios"
    headers = {"Authorization": bearer_token}
    try:
        async with httpx.AsyncClient(timeout=SUB_AGENT_TIMEOUT_S) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent Business injoignable ({url}). Vérifiez qu'il tourne. Détail : {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Agent Business a refusé la requête : {response.text}",
        )
    return response.json()


async def derniere_decision(terrain_id: str, bearer_token: str) -> dict:
    """
    Appelle GET /business/decisions/{terrain_id}/latest. Son propre
    docstring côté agent_business dit explicitement : "Contexte persistant
    consommable par l'agent Monitoring" — c'est exactement ce relais.
    404 si aucune décision confirmée pour ce terrain (pas encore passé par
    /scenarios + /decision) ou si le terrain n'appartient pas à ce user.
    """
    url = f"{BUSINESS_URL}/business/decisions/{terrain_id}/latest"
    headers = {"Authorization": bearer_token}
    try:
        async with httpx.AsyncClient(timeout=SUB_AGENT_TIMEOUT_S) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent Business injoignable ({url}). Vérifiez qu'il tourne. Détail : {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Agent Business a refusé la requête : {response.text}",
        )
    return response.json()
