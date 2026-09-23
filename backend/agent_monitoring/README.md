# Agent Monitoring (Suivi quotidien)

**Status: ✅ Backend works as scoped, but scoped very small — no
persistence at all. ⚠️ The page's most visible feature (budget
tracking) isn't backed by this agent or any API.**

## Role
Once a crop decision is confirmed, gives the farmer a daily operational
briefing: weather, irrigation advice, alerts, and tasks.

## Pipeline — 2-node LangGraph, single endpoint
```
POST /monitoring/analyze
```
1. **`fetch_weather`** — calls Open-Meteo directly (lat/lon, no
   caching/DB). Fails soft: any error returns a `WeatherSummary` with
   just a `note`, rather than crashing the pipeline.
2. **`mistral_reasoning`** — `mistral-medium-latest`,
   `response_format=json_object`. Strictly grounded: `has_alert` must
   be based only on numeric weather values, `water_saving_technique`
   may only reference equipment actually in `hardware_inventory` (no
   invented gear). Returns `has_alert`, `alert_message`,
   `daily_advice`, `water_saving_technique`, `tasks[]`, `crop_alerts[]`.

Request is real-context-only (no mock DB): `farmer_name`, `location`,
`crops[]`, `hardware_inventory[]`, optional `terrain_id` — all supplied
by the frontend. **Nothing is fetched server-side from Postgres, and
nothing is written back to it.** No auth, no tests, no persistence —
confirmed by the full file tree (`config.py`, `main.py`,
`routers/monitoring.py`, `agent/graph.py`,
`services/{weather,mistral}_service.py`).

## Frontend does the real cross-agent stitching (`aujourd-hui.tsx`)
- Pulls the farmer's confirmed Business decision, builds `crops[]`
  from `decision.allocations`, computes a campaign timeline from
  `decision.created_at` to the latest crop's maturity date, and derives
  a planned-spend-per-month baseline from `decision.cout_final`.
- Pulls `location` from the terrain polygon's centroid, and
  `hardware_inventory` from the user's declared equipment.
- **Budget tracking ("real vs. planned" spend, `CostVsPlannedChart`) is
  100% client-side `localStorage`** (`spendTracking.ts`, keyed by
  `decision_id`). It doesn't sync across devices and isn't in Postgres
  — even though a `cost_tracking` table exists in the schema
  specifically for this.

## Explicitly deferred (per the project's own design, not a bug)
Harvest-window → marketplace suggestion, Celery Beat cron jobs, `alerts`
table persistence, BSV phytosanitary data, direct Postgres read of
`farmer_decisions`.

## To do
- Wire `spendTracking.ts` to a real `cost_tracking`-backed endpoint.
- Add basic test coverage (currently none).
- Persist daily briefings to `monitoring_logs`/`alerts` so history
  survives a page reload.

## Run locally
```bash
cd backend/agent_monitoring
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```
