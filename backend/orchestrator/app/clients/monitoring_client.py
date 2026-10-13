"""Client HTTP pour agent_monitoring (port 8003 en local)."""
from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.config import MONITORING_URL, SUB_AGENT_TIMEOUT_S


async def analyze(payload: dict) -> dict:
    """
    Appelle POST /monitoring/analyze. Pas de JWT à transmettre : ce
    endpoint n'a pas de dépendance d'auth côté agent_monitoring (service
    entièrement stateless, voir son README — aucune vérification d'auth
    nulle part dans ce backend).
    """
    url = f"{MONITORING_URL}/monitoring/analyze"
    try:
        async with httpx.AsyncClient(timeout=SUB_AGENT_TIMEOUT_S) as client:
            response = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent Monitoring injoignable ({url}). Vérifiez qu'il tourne. Détail : {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Agent Monitoring a refusé la requête : {response.text}",
        )
    return response.json()
