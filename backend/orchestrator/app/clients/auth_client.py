"""Client HTTP pour le service auth (port 8001 en local)."""
from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.config import AUTH_URL, SUB_AGENT_TIMEOUT_S


async def me(bearer_token: str) -> dict:
    """
    Appelle GET /auth/me. Renvoie UserOut (incl. `terrains[]`) pour
    l'utilisateur propriétaire du token — jamais les terrains d'un autre
    utilisateur, donc un terrain_id absent de la réponse signifie soit
    qu'il n'existe pas, soit qu'il n'appartient pas à ce user. Les deux
    cas sont traités pareil par l'appelant (voir journey.py::journey_status) :
    aucune fuite d'information sur l'existence d'un terrain d'autrui.
    """
    url = f"{AUTH_URL}/auth/me"
    headers = {"Authorization": bearer_token}
    try:
        async with httpx.AsyncClient(timeout=SUB_AGENT_TIMEOUT_S) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Service Auth injoignable ({url}). Vérifiez qu'il tourne. Détail : {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Service Auth a refusé la requête : {response.text}",
        )
    return response.json()
