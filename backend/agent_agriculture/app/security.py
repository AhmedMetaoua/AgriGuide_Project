"""
Politique d'auth de agent_agriculture : décodage via agriment_shared (voir
ce module pour la justification — mécanisme partagé, politique locale à
chaque service). L'auth reste optionnelle ici, inchangé : c'est une
politique propre à ce service (l'analyse d'une parcelle ne nécessite pas
de compte, seule sa persistance contre un terrain_id en profiterait).
"""
from __future__ import annotations

from agriment_shared.auth import InvalidToken, decode_access_token, split_bearer
from fastapi import Header, HTTPException


def get_optional_user_id(authorization: str | None = Header(default=None)) -> str | None:
    """Renvoie le user_id si un Bearer token valide est présent, None si absent.

    Un token invalide/expiré lève quand même 401 — une session périmée
    n'est pas silencieusement traitée comme anonyme.
    """
    if not authorization:
        return None
    token = split_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="En-tête Authorization invalide.")
    try:
        return decode_access_token(token)
    except InvalidToken:
        raise HTTPException(status_code=401, detail="Session invalide, reconnectez-vous.")
