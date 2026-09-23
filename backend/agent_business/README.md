# Agent Business (Business Advisor)

**Status: ✅ Production-real.**

## Role
Consumes Agriculture's `crop_recommendations`, turns each candidate crop
into a fully costed, scored scenario, and runs a human-in-the-loop
confirmation flow. Writes `business_scenarios`, `farmer_decisions`,
`decision_allocations`.

## Scoring (deterministic — the LLM never sets the score)
```
score = 0.35·profit_normalisé + 0.20·(1−risque_normalisé)
      + 0.20·fit_budget + 0.25·compatibilité_agronomique
```
Weights are named constants in `scoring.py`, easy to recalibrate.

## Pipeline per candidate crop (`scenario_generator.py`)
1. **Market study** — price × yield, price adjusted ±15% by a real
   Agreste IPPAP trend (`price_trends.py`, pandas over real CSVs).
2. **Cost estimate** (`financial_service.py`) — 3-tier: operator CSV →
   bottom-up from Agriculture's N/P/K + irrigation + pesticide needs →
   hardcoded fallback. Each tier stamped with a confidence (0.30–0.95)
   and `is_fallback` flag. **No capex/opex split** — one flat
   `cout_production_eur_par_ha` blending fixed seed/machinery cost with
   N/P/K, irrigation, and pesticide cost.
3. **Risk study** (`risk_study.py`) — `risque = probabilité × impact`,
   probability blending agronomic incompatibility (45%), market
   downside (25%), yield volatility (20%), cost uncertainty (10%);
   auto-generates a named risk + mitigation text + mitigation cost.
4. **Financial indicators** — revenue, cost, profit, margin, ROI,
   break-even price/yield, budget gap — all formula-derived and
   returned with full `detail_calcul` (formulas + values + sources)
   for an in-app "Details" view.
5. **Market intelligence RAG** (`rank_crops.py`) — retrieves
   FranceAgriMer PDF bulletins from a hand-rolled numpy+JSON vector
   store (`local_store.py` — not actually Chroma, despite the naming;
   built to dodge chromadb/hnswlib native-build issues on Windows),
   blends with the Agreste trend, and asks Mistral for a strict-JSON
   verdict — explicitly forbidden from setting the ranking score.

## Human-in-the-loop
- `POST /business/scenarios` → up to 3 ranked scenarios.
- `POST /business/decision` → validates allocation ≤ available ha, no
  duplicate scenario reuse, allocation ≤ advised area, final cost ≤
  budget; persists to Postgres; returns `date_maturite_prevue` per
  crop (feeds Monitoring/Marketplace downstream).
- The backend schema (`FarmerDecisionRequest`) supports **splitting one
  terrain across several scenarios/crops** in one decision, but the
  current frontend (`business.tsx`) only ever sends **one** allocation
  at a time, at the scenario's full advised area — no partial-area or
  multi-crop split UI yet.
- Terrain ownership/area is re-verified server-side against Auth's
  `terrains` table on every call — the client-supplied area is never
  trusted.

## Known gaps
- README (pre-revision) still listed "Postgres persistence of
  decisions" as a future step — it's already fully implemented.
- No capex/opex distinction (see above) if that split is ever needed.
- Test coverage is strong for endpoints/decision logic but thin on the
  RAG ranking path.

## Run locally
```bash
cd backend/agent_business
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
