# Orchestrator (Supervisor Agent)

**Status: ✅ Built and tested — 3 journey endpoints, not yet consumed by the frontend.**

## Role
Single entry point for the **sequential steps of the farmer journey**:
`analysis → scenarios → decision → monitoring`. It relays requests between
agents so the client no longer has to hand-carry payloads from one agent to the
next, and it aggregates read-only state about a parcel's progress.

## Design: hybrid, not a total proxy
Only journey-critical steps go through the orchestrator. Plain CRUD (Auth
sign-up/sign-in, terrain editing) and free-form search (Regulation, Waste)
stay direct frontend → agent calls. The orchestrator holds **no business
logic** — no financial, agronomic or scoring computation lives here; that stays
in the owning agent.

```
Frontend ──► Orchestrator ──┬──► Auth         (terrain ownership)
                            ├──► Agriculture  (/analyze, /land-profile)
                            ├──► Business     (/scenarios, /decisions)
                            └──► Monitoring   (/analyze)
```

## Endpoints

| Method | Route | What it does |
|---|---|---|
| `POST` | `/orchestrator/journey/scenarios` | Runs Agriculture `/analyze`, then Business `/scenarios`, in one call (LangGraph, 2 nodes). Crop recommendations pass through unchanged; `superficie_disponible_ha` is derived from the parcel area Agriculture returns. |
| `POST` | `/orchestrator/journey/monitoring` | Fetches the farmer's latest confirmed Business decision, derives each crop's water sensitivity from the persisted irrigation data (Agriculture `land-profile`), and relays everything to Monitoring `/analyze`, translating `allocations[]` into `crops[]`. Returns `{decision, briefing}`. |
| `GET` | `/orchestrator/journey/status/{terrain_id}` | Read-only journey state for a parcel: does the terrain exist and belong to this user (Auth), has it been analyzed (Agriculture `land-profile`), is a decision confirmed (Business). Each lookup degrades independently — an unreachable Business does not hide that the terrain exists. |
| `GET` | `/health` | Liveness + the configured sub-agent URLs. |

All journey routes require the Bearer JWT issued by Auth (validated through the
[shared package](../shared/README.md), **no dev bypass**). The token is
forwarded to downstream agents, which re-check ownership themselves.

### Error handling
Sub-agent failures keep their real status code instead of being flattened into
a generic 502 (`JourneyError` in `app/graph.py`): `404` "no confirmed decision
yet" stays distinguishable from `422` (inconsistent payload) and `503`
(service unreachable).

### Water sensitivity
`app/water_sensitivity.py` turns Agriculture's persisted `besoins_irrigation`
into `low | moderate | high` per crop. The net irrigation need over the
forecast window is normalised to mm/day:

| mm/day | Level |
|---|---|
| `< 1.0` | `low` |
| `1.0 – 2.5` | `moderate` |
| `≥ 2.5` | `high` |

These are starting thresholds (a product decision, not an agronomic standard)
and can be tuned without code changes via `WATER_SENSITIVITY_LOW_MAX_MM_DAY` and
`WATER_SENSITIVITY_HIGH_MIN_MM_DAY`. The lookup is best-effort: if the terrain
was never analyzed, or Agriculture is unreachable, the field is simply omitted
and the briefing is produced without it — it never fails the relay.
`frontend/src/lib/waterSensitivity.ts` mirrors the same thresholds.

## Known limitations
- **Only the monitoring relay is used by the UI.** The Today page
  (`aujourd-hui.tsx`) calls `/journey/monitoring` and falls back to calling
  Monitoring directly when the orchestrator can't serve the request (dev
  auth bypass, service down, expired session, or a decision known only
  locally). `/journey/scenarios` and `/journey/status` are not consumed yet;
  `/scenarios` does not map cleanly onto the two-page Agriculture → Business
  flow.
- **No intent router yet.** Current graphs are fixed pipelines. A
  `POST /chat` node that picks the target agent from a free-text message is the
  intended next step.
- **Journey state machine only partly enforced.** `farmer_decisions.statut`
  defines `pending / confirmed / monitoring`, but only `confirmed` is written
  in practice; the ownership and "decision exists" invariants are enforced by
  Business on each write.
- **Marketplace trigger** (`date_maturite_prevue` → sale suggestion) is not
  built; it depends on the Marketplace service.

## Tests
```bash
cd backend/orchestrator
JWT_SECRET_KEY=test-secret python -m pytest tests -q
```
Sub-agent clients are replaced by test doubles, so no network or database is
needed. They cover the water-sensitivity thresholds and invalid input, the
monitoring relay with and without a persisted profile, and the auth gate.

## Run locally
```bash
cd backend/orchestrator
pip install -r requirements.txt     # the root venv also installs ../shared
uvicorn app.main:app --reload --port 8000
```
Check: `GET http://127.0.0.1:8000/health`.

| Variable | Default | Notes |
|---|---|---|
| `JWT_SECRET_KEY` | — | must match Auth |
| `AGENT_AUTH_URL` | `http://localhost:8001` | |
| `AGENT_AGRICULTURE_URL` | `http://localhost:8002` | |
| `AGENT_MONITORING_URL` | `http://localhost:8003` | |
| `AGENT_WASTE_URL` | `http://localhost:8004` | |
| `AGENT_REGULATION_URL` | `http://localhost:8005` | |
| `AGENT_BUSINESS_URL` | `http://localhost:8006` | not 8000 — that port is the orchestrator's |
| `ORCHESTRATOR_SUB_AGENT_TIMEOUT_S` | `45` | Agriculture `/analyze` is the slowest call |

In Docker the image is built from the **repo root** so it can copy
`backend/shared` (see `docker-compose.yml`).

## Stack
FastAPI · LangGraph · httpx
