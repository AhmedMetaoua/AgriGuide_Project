"""
Politique d'auth de agent_business : décodage via agriment_shared (voir ce
module pour la justification — mécanisme partagé, politique locale à
chaque service). Le bypass BUSINESS_AUTH_DISABLED reste ici, inchangé :
c'est une politique propre à ce service (dev-only), pas au mécanisme.
"""
from __future__ import annotations

import os

from agriment_shared.auth import InvalidToken, decode_access_token, split_bearer
from fastapi import Header, HTTPException


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    if os.getenv("BUSINESS_AUTH_DISABLED", "0").lower() in {"1", "true", "yes"}:
        return "00000000-0000-0000-0000-000000000000"
    token = split_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    try:
        return decode_access_token(token)
    except InvalidToken:
        raise HTTPException(status_code=401, detail="Session invalide, reconnectez-vous.")
