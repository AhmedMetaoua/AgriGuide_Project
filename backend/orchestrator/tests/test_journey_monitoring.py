"""
Tests du relais /orchestrator/journey/monitoring et de la dérivation de
water_sensitivity. Lancer depuis backend/orchestrator :

    JWT_SECRET_KEY=test python -m pytest tests -q

Aucun réseau : les clients sous-agents sont remplacés par des doubles.
"""
import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

import base64
import hashlib
import hmac
import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import graph
from app.main import app
from app.water_sensitivity import classify_water_sensitivity

client = TestClient(app)

DECISION = {
    "decision_id": "d1",
    "created_at": "2026-10-01T00:00:00",
    "allocations": [
        {"culture": "ble_tendre", "hectares_alloues": 3.0},
        {"culture": "mais", "hectares_alloues": 1.5},
        {"culture": "colza", "hectares_alloues": 0.5},
    ],
}
PROFILE = {
    "crop_recommendations": [
        {"culture": "ble_tendre", "besoins_irrigation": {"irrigation_need_mm": 8.0, "irrigation_window_days": 16}},   # 0.5 -> low
        {"culture": "mais", "besoins_irrigation": {"irrigation_need_mm": 48.0, "irrigation_window_days": 16}},        # 3.0 -> high
        {"culture": "colza", "besoins_irrigation": {"warning": "Aucun coefficient cultural"}},                        # None
    ]
}
BODY = {
    "terrain_id": "t1",
    "farmer_name": "Bara",
    "location": {"latitude": 36.8, "longitude": 10.1},
    "hardware_inventory": ["Goutte-à-goutte"],
}


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _headers():
    # JWT HS256 signé à la main (stdlib) : aucune dépendance de test supplémentaire.
    signing_input = (
        _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        + "."
        + _b64(json.dumps({"sub": "u1", "exp": 4102444800}).encode())
    )
    signature = hmac.new(b"test-secret", signing_input.encode(), hashlib.sha256).digest()
    return {"Authorization": f"Bearer {signing_input}.{_b64(signature)}"}


@pytest.mark.parametrize(
    "need,window,expected",
    [
        (0.0, 16, "low"),
        (15.9, 16, "low"),       # 0.99 mm/j
        (16.0, 16, "moderate"),  # 1.0 mm/j
        (39.9, 16, "moderate"),  # 2.49 mm/j
        (40.0, 16, "high"),      # 2.5 mm/j
        (80.0, 7, "high"),
    ],
)
def test_classify_thresholds(need, window, expected):
    assert classify_water_sensitivity({"irrigation_need_mm": need, "irrigation_window_days": window}) == expected


@pytest.mark.parametrize(
    "bad",
    [None, {}, "x", {"irrigation_need_mm": 5}, {"irrigation_need_mm": 5, "irrigation_window_days": 0},
     {"irrigation_need_mm": "5", "irrigation_window_days": 16}, {"warning": "no kc"}],
)
def test_classify_missing_or_invalid_returns_none(bad):
    assert classify_water_sensitivity(bad) is None


def _patch(monkeypatch, profile):
    captured = {}

    async def fake_decision(terrain_id, token):
        return DECISION

    async def fake_profile(terrain_id):
        if isinstance(profile, Exception):
            raise profile
        return profile

    async def fake_analyze(payload):
        captured["payload"] = payload
        return {"analysis": {}, "weather_summary": {}, "crops": payload["crops"]}

    monkeypatch.setattr(graph.business_client, "derniere_decision", fake_decision)
    monkeypatch.setattr(graph.agriculture_client, "get_land_profile", fake_profile)
    monkeypatch.setattr(graph.monitoring_client, "analyze", fake_analyze)
    return captured


def test_monitoring_relay_adds_water_sensitivity(monkeypatch):
    captured = _patch(monkeypatch, PROFILE)
    r = client.post("/orchestrator/journey/monitoring", json=BODY, headers=_headers())
    assert r.status_code == 200
    crops = {c["crop_name"]: c for c in captured["payload"]["crops"]}
    assert crops["ble_tendre"]["water_sensitivity"] == "low"
    assert crops["mais"]["water_sensitivity"] == "high"
    assert "water_sensitivity" not in crops["colza"]          # donnée absente -> pas de valeur inventée
    assert crops["mais"]["hectares"] == 1.5
    assert r.json()["decision"]["decision_id"] == "d1"


@pytest.mark.parametrize("profile", [None, HTTPException(status_code=503, detail="down"), RuntimeError("boom")])
def test_monitoring_relay_survives_missing_profile(monkeypatch, profile):
    captured = _patch(monkeypatch, profile)
    r = client.post("/orchestrator/journey/monitoring", json=BODY, headers=_headers())
    assert r.status_code == 200
    assert all("water_sensitivity" not in c for c in captured["payload"]["crops"])


def test_monitoring_requires_auth():
    assert client.post("/orchestrator/journey/monitoring", json=BODY).status_code == 401
