"""
Validation HS256 des JWT émis par le service Auth.

Historique : ce module existait en deux copies identiques
(backend/agent_business/app/security.py et
backend/orchestrator/app/security.py) — voir l'audit du monorepo,
"duplicated/could drift". Ce package en fait la seule source de vérité
pour le *mécanisme* de décodage.

Ce module n'expose délibérément PAS de dépendance FastAPI `get_current_user_id`
toute faite : chaque service garde sa propre *politique* d'accès autour du
même décodage (ex. `BUSINESS_AUTH_DISABLED` côté agent_business, un
bypass dev qui n'a pas de sens côté orchestrateur — voir son propre
security.py). Mécanisme partagé, politique locale à chaque service.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me-in-production")


class InvalidToken(ValueError):
    """Levée pour toute raison de rejet (signature, expiration, format...).

    Sous-classe de ValueError : le code existant qui fait
    `except ValueError` (agent_business, orchestrator) continue de
    fonctionner sans modification.
    """


def _decode_segment(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def decode_access_token(token: str) -> str:
    """Vérifie signature + expiration + claim `sub`, renvoie le user_id.

    Lève InvalidToken (ValueError) si le token est invalide, expiré, ou
    mal formé — jamais d'autre type d'exception.
    """
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signed = f"{header_segment}.{payload_segment}".encode()
        expected = hmac.new(JWT_SECRET_KEY.encode(), signed, hashlib.sha256).digest()
        actual = _decode_segment(signature_segment)
        if not hmac.compare_digest(expected, actual):
            raise InvalidToken("signature")
        header = json.loads(_decode_segment(header_segment))
        payload = json.loads(_decode_segment(payload_segment))
        if header.get("alg") != "HS256":
            raise InvalidToken("algorithm")
        if payload.get("exp") is not None and float(payload["exp"]) < time.time():
            raise InvalidToken("expired")
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidToken("subject")
        return str(user_id)
    except InvalidToken:
        raise
    except Exception as exc:
        raise InvalidToken("Token invalide ou expiré") from exc


def split_bearer(authorization: str | None) -> str | None:
    """Extrait le token brut d'un header `Authorization: Bearer <token>`.

    Renvoie None si le header est absent ou mal formé (pas de levée
    d'exception ici — chaque service décide comment réagir à None, avec
    son propre message/status HTTP).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1]
