# Monitoring Agent (Daily Follow-up)

**Status: ✅ Works as scoped — a stateless daily-briefing service. No persistence yet.**

## Role
Once a crop decision is confirmed, gives the farmer a daily operational
briefing: weather, irrigation advice, alerts and tasks.

## Pipeline — 2-node LangGraph, one endpoint
```
POST /monitoring/analyze
```
1. **`fetch_weather`** — calls Open-Meteo directly. Fails soft: any error
   produces a weather summary with just a `note` instead of crashing the run.
2. **`mistral_reasoning`** — Mistral (`MISTRAL_MODEL`, default
   `mistral-large-latest`) in JSON mode. Strictly grounded: `has_alert` must
   rest on numeric weather values, and `water_saving_technique` may only
   reference equipment actually present in `hardware_inventory`. Returns
   `has_alert`, `alert_message`, `daily_advice`, `water_saving_technique`,
   `tasks[]` and `crop_alerts[]` (one entry per crop with a low/medium/high
   risk).

The request carries all its own context — `farmer_name`, `location`,
`crops[]`, `hardware_inventory[]`, optional `terrain_id`. **Nothing is read
from or written to Postgres by this service.**

## Endpoints
| Method | Route | Description |
|---|---|---|
| `POST` | `/monitoring/analyze` | Daily briefing from weather + crop + equipment context |
| `GET` | `/health` | Health check |

## How the frontend uses it (`aujourd-hui.tsx`)
- Loads the farmer's confirmed Business decision, builds `crops[]` from
  `decision.allocations`, computes a campaign timeline up to the latest crop's
  maturity date, and derives a planned monthly spend from `decision.cout_final`.
- Takes `location` from the terrain polygon's centroid and
  `hardware_inventory` from the farmer's declared equipment.
- The orchestrator's `POST /orchestrator/journey/monitoring` performs the
  decision → `crops[]` translation server-side; the page does not use it yet.
- **Spend tracking ("real vs. planned") is client-side only** (`localStorage`,
  `spendTracking.ts`, keyed by decision id). It does not sync across devices.
  The schema already has a `cost_tracking` table meant for this.

## Known limitations / roadmap
- No authentication, no tests.
- No persistence of briefings (`monitoring_logs` / `alerts` tables exist but
  are unused), so history is lost on reload.
- Wire spend tracking to a `cost_tracking`-backed endpoint.
- Deferred by design: scheduled runs (Celery Beat), plant-health bulletin
  (BSV) data, harvest-window → marketplace suggestion.

## Run locally
```bash
cd backend/agent_monitoring
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```
Needs `MISTRAL_API_KEY` (and optionally `MISTRAL_MODEL`) in the root `.env`.
