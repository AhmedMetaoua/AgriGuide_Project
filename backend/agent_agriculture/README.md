# Agent Agriculture (Agricultural Advisor)

## Role
Feature 1 of the AgriAdvisor platform. Given a farmer's parcel, produces a
full land profile (soil, satellite, climate, RPG history) and a ranked
crop recommendation with fertilization, irrigation, and yield estimates.
Writes `land_profiles` and `crop_recommendations`.

## Pipeline

1. **Parcel resolution** (`parcel_service.py`) — cadastre → RPG → manual
   fallback, from a map click.
2. **Parallel external fetch**: SoilGrids (soil), Open-Meteo (climate),
   Sentinel-2/Copernicus (satellite), RPG (declared crop history).
3. **Crop scoring (ML)** — rule-based scorer on pH / temperature /
   nitrogen / CEC / precipitation / workability, weighted to 1.0.
   Produces the ranked 5-of-9-crop recommendation used downstream by
   Business.
4. **DL cross-check (not part of the score)** — a pretrained BreizhCrops
   TempCNN classifies observed land cover from a Sentinel-2 time series
   and is compared against the RPG-declared crop ("declared vs.
   observed" mismatch note). A small, capped, confidence-gated bonus
   (`_DL_MAX_BONUS = 0.06`) nudges the ML score for the 5 original crops
   only, when the DL prediction agrees with the candidate — logged
   transparently per-crop (`base_score_before_dl`, `dl_evidence_bonus`).
5. **Fertilization & irrigation** (`agro_calc_service.py`) — COMIFER-style
   nitrogen balance (with a legume branch) + FAO-56 irrigation need.
6. **Yield estimation** (`yield_service.py`) — base yield × suitability
   adjustment.
7. **RAG-grounded agronomic advice** — HAL corpus (fetch → ingest →
   chunk → embed), retrieved per-crop, with real citations backfilled
   (title + hal.science link) across the full corpus. `RAG_BACKEND`
   toggles Chroma/Qdrant with hybrid dense+sparse search.
8. **3D terrain viewer** — real IGN LiDAR HD elevation mesh with 5
   switchable modes: NDVI (vigor), NDWI (water), NDMI (moisture), Slope
   (topography, from the elevation gradient), Photo (IGN orthophoto).
   All three spectral indices come from one Sentinel-2 evalscript,
   masked to the actual parcel polygon. A simpler 2D NDVI-only heatmap
   also exists for the flat Leaflet map.
9. **Chatbot widget** — blends the RAG corpus, the selected parcel's
   full `/analyze` output, and (when logged in) the user's Postgres
   profile (equipment, terrains, past recommendations).

## Key endpoints
- `POST /analyze` — full pipeline, returns `AnalyzeResponse`
- `POST /chat` — chatbot widget
- `POST /parcel/resolve`, `POST /parcel/neighbors`, `POST /parcel/ndvi_heatmap`
- `POST /relief/grid`, `POST /relief/orthophoto` — 3D terrain data

## Known gaps
- `besoins_pesticides` is a hardcoded placeholder (no BSV module yet).
- `land_profiles.elevation_m` is never written, despite the LiDAR
  pipeline having real elevation data available.
- Only `test_endpoints.py` (offline) is ported into this monorepo; the
  standalone prototype's `check_yield.py` / `check_crop_scoring.py` /
  `check_retrieve.py` / `check_legume_nitrogen.py` were not carried over.
- `RAG_BACKEND=qdrant` push is a manual script, not wired into ingestion.
- No caching/rate-limiting on SoilGrids/Open-Meteo/Sentinel Hub calls.

## Run locally
```bash
cd backend/agent_agriculture
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```
