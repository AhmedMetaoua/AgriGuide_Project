"""Client HTTP pour agent_agriculture (port 8002 en local)."""
from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.config import AGRICULTURE_URL, SUB_AGENT_TIMEOUT_S


async def analyze(payload: dict) -> dict:
    """
    Appelle POST /agriculture/analyze. Pas de JWT à transmettre : ce endpoint
    n'a pas de dépendance d'auth côté agent_agriculture (voir
    backend/agent_agriculture/app/routers/agriculture.py::analyze).
    """
    url = f"{AGRICULTURE_URL}/agriculture/analyze"
    try:
        async with httpx.AsyncClient(timeout=SUB_AGENT_TIMEOUT_S) as client:
            response = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent Agriculture injoignable ({url}). Vérifiez qu'il tourne. Détail : {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Agent Agriculture a refusé la requête : {response.text}",
        )
    return response.json()


async def get_land_profile(terrain_id: str) -> dict | None:
    """
    Appelle GET /agriculture/land-profile/{terrain_id}. Contrairement à
    analyze(), un 404 est un état normal attendu ici ("jamais analysé"),
    pas une erreur — donc il est intercepté et renvoie None, au lieu de
    lever une HTTPException comme le reste de ce fichier. Toute autre
    erreur (503, 500...) continue de lever normalement.
    """
    url = f"{AGRICULTURE_URL}/agriculture/land-profile/{terrain_id}"
    try:
        async with httpx.AsyncClient(timeout=SUB_AGENT_TIMEOUT_S) as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent Agriculture injoignable ({url}). Vérifiez qu'il tourne. Détail : {exc}",
        ) from exc

    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Agent Agriculture a refusé la requête : {response.text}",
        )
    return response.json()
