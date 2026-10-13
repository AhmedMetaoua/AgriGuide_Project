"""
Politique d'auth de l'orchestrateur : décodage via agriment_shared, pas de
bypass dev possible ici (voir agriment_shared.auth pour la justification —
mécanisme partagé, politique locale à chaque service).
"""
from __future__ import annotations

from agriment_shared.auth import InvalidToken, decode_access_token, split_bearer
from fastapi import Header, HTTPException


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """Valide le JWT entrant et renvoie le user_id (`sub`).

    Aucun bypass type BUSINESS_AUTH_DISABLED ici, volontairement : l'orchestrateur
    est le point d'entrée de chaque appel de parcours, donc ce contrôle ne
    doit jamais être court-circuitable, même en dev.
    """
    token = split_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    try:
        return decode_access_token(token)
    except InvalidToken:
        raise HTTPException(status_code=401, detail="Session invalide, reconnectez-vous.")


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    """Renvoie le header `Bearer <token>` brut, pour le transmettre tel
    quel aux sous-agents (Business, Monitoring) qui le valident eux-mêmes."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    return authorization
