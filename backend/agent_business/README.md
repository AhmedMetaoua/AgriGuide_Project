# Business Advisor

**Status: ✅ Real — financial scenarios, market intelligence and persisted decisions.**

## Role
Takes the real `crop_recommendations` produced by the Agriculture agent plus
the farmer's budget, and returns **three financially detailed scenarios**. It
records the scenario the farmer confirms and exposes that decision as the
crop context for the Monitoring agent.

## Scoring is deterministic
```text
score = 35% profitability + 20% risk control + 20% budget fit
      + 25% agronomic compatibility (from Agriculture)
```
The LLM only summarizes market documents (demand, competition, justification).
It never computes finances and never influences the ranking score.

## Market intelligence pipeline
```
data/
  FDS_IPPAP_*.csv        → Agreste price-index trends (pandas)
  FranceAgriMer_*.pdf    → market bulletins (local vector index + Mistral)
        ↓
market_intelligence.provider.get_market_price()
        ↓
market_study.estimer_marche() → Business scenarios
```

| Signal | Source |
|---|---|
| Price trend | Agreste IPPAP (CSV) |
| Demand / competition / justification | FranceAgriMer PDFs via RAG + Mistral |
| Price €/kg | Absolute price scale adjusted by the real IPPAP trend (IPPAP is an index, not €) |
| Yield | FAOSTAT history, explicit fallback scale |
| Costs | Operator CSV, or input costs computed from Agriculture's needs, explicit fallback |
| Risk | Agronomic compatibility + market + volatility + cost-data quality |

RAG turns on automatically when the local vector index exists and
`MISTRAL_API_KEY` is set; force it off with `MARKET_RAG_ENABLED=0`.
Each scenario reports gross revenue, total cost, profit, margin, ROI,
break-even thresholds, budget gap, risk explanations and a data-confidence
level. Scenarios whose costs came from the fallback scale are flagged
`cout_fallback`.

> The market data folder (`FDS_IPPAP_*.csv`, `FranceAgriMer_*.pdf`) is not
> committed. Without it the service still runs but falls back to its explicit
> reference baselines and reports lower data confidence.

## Endpoints
| Method | Route | Description |
|---|---|---|
| `POST` | `/business/scenarios` | Generate the 3 scenarios for a terrain |
| `POST` | `/business/decision` | Confirm the farmer's chosen scenario (human-in-the-loop) |
| `GET` | `/business/decisions/{terrain_id}/latest` | Latest confirmed decision — consumed by Monitoring |
| `GET` | `/health` | Status + market diagnostics (`market.rag_active`) |

All business routes require the Bearer JWT issued by Auth (decoded through
[`agriment_shared`](../shared/README.md)). Terrain existence and ownership are
checked server-side, and the area stored in PostgreSQL is used instead of any
value sent by the browser. Scenarios and decisions are persisted
(`business_scenarios`, `farmer_decisions`, `decision_allocations`).

## Run locally
```bash
cd backend/agent_business
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# One-time (or after adding files to data/): index the PDFs + CSVs
python -m app.market_intelligence.rag.ingest

# Port 8006, not 8000 — 8000 belongs to the orchestrator
uvicorn app.main:app --reload --port 8006
```
Embeddings use `mistral-embed`, so `MISTRAL_API_KEY` must be in the root
`.env`. For an already-created database, apply once:
```bash
psql "$DATABASE_URL" -f database/migration_business_financials.sql
psql "$DATABASE_URL" -f database/migration_decision_allocations_scenario_cascade.sql
```

## Configuration
| Variable | Purpose |
|---|---|
| `MISTRAL_API_KEY`, `MISTRAL_MODEL` | LLM for market summaries / crop ranking (default `mistral-large-latest`) |
| `MARKET_DATA_DIR` | Folder with the IPPAP CSVs and FranceAgriMer PDFs (default: `./data` at repo root) |
| `MARKET_RAG_ENABLED` | `0` to disable RAG |
| `BUSINESS_FAO_YIELD_CSV` | Override the bundled FAOSTAT yield CSV |
| `BUSINESS_COST_DATA_CSV` | Cost table; accepts `culture`/`crop`, `cost_per_ha_eur`/`cout_eur_par_ha`, optional `source`, `year` |
| `BUSINESS_PERSISTENCE_MODE=memory` | Run without PostgreSQL (tests) |
| `BUSINESS_AUTH_DISABLED=1` | **Dev/test only** — skips JWT checks |

## Tests
```bash
python -m pytest backend/agent_business/app/tests
```
The suite runs in `memory` persistence mode with auth disabled.

## Next steps
1. Live RNM price feed for €/kg
2. Real BSV (plant-health bulletin) data for risk
3. PDF planning export after scenario confirmation
