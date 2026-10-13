# Agriculture Advisor

**Status: ✅ Real — the most complete agent; multi-source analysis, scoring, sourced report, chat and 3D view.**

**Role**: analyze a plot of land (geo/soil/climate/satellite) and recommend
the crops best suited to the farm, with a sourced AI report, a contextual
chat assistant, and a 3D terrain view.

This module is the first link in the **AgriMent** platform — *"Think Smart.
Farm Smarter."* — the agent every farmer meets first, before the business or
regulatory side even comes into play.

## Business Objective

A young farmer (or an agricultural investor) taking on a new plot of land
faces a question that's simple to ask but costly to get wrong: **which crop
actually makes sense here, this season?** Guessing wrong costs an entire
season's revenue, and the data needed to answer well — soil composition,
climate history, what's actually growing on neighboring parcels, real-time
vegetation vigor — is scattered across a dozen public sources that few
farmers have the time or expertise to cross-reference themselves.

This agent does that cross-referencing for them, in seconds, and documents
every recommendation instead of returning a black box: each proposed crop
comes with a score, an explanation of what drove it up the ranking
(`feature_importance`), the resulting irrigation/fertilizer needs, and a
report that cites its sources. It's the foundation that then feeds the
Business Advisor (profitability scenarios on those same crops), the Waste
Valorization agent (residue valorization once a crop is chosen), and — via
the Today dashboard — the parcel's ongoing daily monitoring.

## Features

### Parcel resolution & context
- Resolves a point clicked on the map against the IGN cadastre and the RPG
  (French land parcel registry), with no need to declare the parcel
  beforehand.
- Neighboring-crop context within a configurable radius, to situate a
  recommendation against what's actually growing nearby.

### Multi-source analysis
- **Soil** — composition (SoilGrids).
- **Weather** — historical and forecast (Open-Meteo).
- **Vegetation** — real-time NDVI (Sentinel Hub / Copernicus Data Space),
  with a pixel-by-pixel NDVI map available directly (not just an aggregated
  average).
- **Satellite observation** — current land-cover classification via a deep
  learning model (TempCNN pre-trained on BreizhCrops, fine-tuned), used as
  supplementary field evidence — never as a second opinion that recalculates
  the soil/climate score (see the DL Classifier section).

### Crop recommendation
- Scores nine crops (soft wheat, corn, rapeseed, barley, sunflower, potato,
  sugar beet, soybean, protein peas) with a **documented rule-based scorer**
  (agronomic tolerance ranges for pH, temperature, nitrogen, CEC, rainfall —
  not an LLM black box, and not yet a trained model; see Known Limitations),
  plus explicit formulas for nitrogen/irrigation/pesticide needs and yield
  estimation.
- `feature_importance` returned for every recommended crop, so the farmer
  understands *why* it ranked where it did.

### Sourced AI report
- Generated in French via Mistral, grounded (RAG) in a corpus of scientific
  literature (HAL/INRAE) and regulatory documents, with citations and a
  two-stage anti-hallucination audit.
- Configurable vector-search backend (`RAG_BACKEND`):
  - `chroma` (**default**) — local store, zero external dependency beyond
    the Mistral API.
  - `qdrant` — optional, queries a Qdrant Cloud collection pre-loaded by
    `scripts/push_to_qdrant.py` (hybrid dense+sparse), for deployments that
    want to decouple the vector store from the service's local disk.

### Chat assistant
- Grounded on three sources at once: the document corpus (RAG), the parcel
  currently being viewed if one exists, and the logged-in farmer's own
  profile (their terrains, their equipment) when a valid token is provided —
  never hallucinating context it hasn't actually received.

### 3D terrain view
- 3D mesh generated from IGN LiDAR HD data, cached locally on demand so it
  isn't re-downloaded on every visit.

## Input

- `terrain_id` (a geometry already saved in `terrains`, created by the
  `auth` service at sign-up or via `POST /auth/me/terrains`), **or**
- a point clicked on the map (`point`), resolved live against the
  cadastre/RPG — lets a farmer explore a specific parcel without having
  declared it as a terrain beforehand.

## Output

- Returned directly in the HTTP response (`POST /agriculture/analyze`), and
  — if `terrain_id` is provided — written to the database (and readable back
  later through `GET /agriculture/land-profile/{terrain_id}`):
  - `land_profiles`: soil, satellite, RPG, climate
  - `crop_recommendations`: scored crops with needs (pesticides, fertilizer,
    irrigation), cycle length (`cycle_jours`), and `feature_importance` for
    explainability

## Endpoints

| Method | Route                              | Description                                                                     |
|--------|--------------------------------------|-------------------------------------------------------------------------------------|
| POST   | `/agriculture/parcel/resolve`       | Resolves a GPS point into a cadastral/RPG parcel (preview only, not persisted).      |
| POST   | `/agriculture/parcel/neighbors`     | Neighboring declared crops within a given radius around a point.                    |
| POST   | `/agriculture/parcel/ndvi_heatmap`  | Pixel-by-pixel NDVI map (PNG) for a given parcel.                                   |
| POST   | `/agriculture/analyze`              | Full pipeline: soil/weather/satellite/DL + scoring + AI report + persistence.       |
| GET    | `/agriculture/land-profile/{terrain_id}` | Latest persisted land profile + crop recommendations for a terrain, without re-running the analysis. `404` if it was never analyzed (a normal state, not an error). |
| POST   | `/agriculture/chat`                 | Chat assistant (RAG + parcel context + farmer profile).                             |
| POST   | `/agriculture/relief/grid`          | 3D terrain mesh (IGN LiDAR HD) for a given parcel.                                  |
| POST   | `/agriculture/relief/orthophoto`    | Orthophoto overlay for the 3D mesh.                                                 |
| GET    | `/health`                            | Health check.                                                                        |

## Running the Server (local dev)

```bash
cd backend/agent_agriculture
python -m venv .venv
# macOS/Linux: source .venv/bin/activate — Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

On Linux/macOS/Docker, `pip install -r requirements.txt` installs everything
in one shot with no issue. **On Windows**, `chromadb==0.5.15` depends on
`chroma-hnswlib==0.7.6`, which has no precompiled wheel for Windows/Python
3.12 (source only, requiring MSVC Build Tools to compile). If
`pip install -r requirements.txt` fails on `chroma-hnswlib` with
`Microsoft Visual C++ 14.0 or greater is required`, install in this order
instead (same venv):

```powershell
pip install chroma-hnswlib==0.7.5   # has a cp312-win_amd64 wheel; API-compatible with 0.7.6
pip install chromadb==0.5.15 --no-deps
# install the rest of requirements.txt WITHOUT re-triggering chromadb's own
# dependency resolution (which would retry 0.7.6). Also filter out comments
# and blank lines — otherwise pip receives lines like `# numpy<2` as invalid
# requirements:
$pkgs = Get-Content requirements.txt | Where-Object {
  $_ -match '\S' -and $_ -notmatch '^\s*#' -and $_ -notmatch '^chromadb=='
}
pip install @pkgs
```

`chromadb --no-deps` also skips its real runtime dependencies (not just
`chroma-hnswlib`) — install these by hand if missing: `overrides`, `posthog`,
`pypika`, `typer`, `rich`, `importlib-resources`, `kubernetes`, `build`, the
`opentelemetry-*` stack (api/sdk/exporter-otlp-proto-grpc/
instrumentation-fastapi). `pip` will print a warning `chromadb ... requires
chroma-hnswlib==0.7.6, but you have chroma-hnswlib 0.7.5` — harmless (patch
version, identical API).

Port `8002` by convention (`8000` = orchestrator, `8001` = auth, `8003` =
monitoring, `8004` = waste, `8005` = regulation, `8006` = business) so multiple agents can run locally at
once without collisions. The frontend targets it via `VITE_AGENT_AGRICULTURE_URL` (default
`http://localhost:8002`, see `frontend/.env.example`).

Environment variables used (all in the repo-root `.env` — see
`.env.example`):

- `DATABASE_URL` — Postgres/PostGIS, required to persist `land_profiles` /
  `crop_recommendations` (optional if you're only using the clicked map
  point, without `terrain_id`).
- `MISTRAL_API_KEY` — required for the AI report (RAG + synthesis) and the
  chat assistant. `MISTRAL_MODEL` (default `mistral-large-latest`) selects the
  model for both. Without a key, `/agriculture/analyze` still works
  (real soil/weather/satellite/scoring) but `report` comes back `null` with
  a warning in `warnings`.
- `SENTINEL_HUB_CLIENT_ID` / `SENTINEL_HUB_CLIENT_SECRET` — free account at
  [dataspace.copernicus.eu](https://dataspace.copernicus.eu), required for
  NDVI and the DL classifier. Without these keys, `vegetation`/
  `dl_observation` come back with `source: "unavailable"`.
- `JWT_SECRET_KEY` — same secret as the `auth` service; required for the
  chat assistant to recognize a logged-in farmer and personalize its
  answers with their profile. Tokens are decoded through the shared
  `agriment_shared` package, and auth stays **optional** here: anonymous
  analysis is allowed, but an invalid or expired token is still a 401.
- `RAG_BACKEND` — `chroma` (default) or `qdrant`. `QDRANT_URL` /
  `QDRANT_API_KEY` only required if `RAG_BACKEND=qdrant`.

Every other source (IGN cadastre, RPG WFS, SoilGrids, Open-Meteo, HAL, IGN
LiDAR HD) is public, free, and requires no key.

## Feeding the RAG Corpus

```bash
cd backend/agent_agriculture
python -m scripts.fetch_hal_documents --query "ble tendre fertilisation" --coll INRAE --rows 30 --out ./corpus
python -m scripts.ingest_rag_corpus --input ./corpus --crop ble_tendre --topic fertilisation
python -m scripts.dedupe_chroma --apply   # one-off dedup cleanup
```

`chroma_store/` (vector store persistence) is mounted as a Docker volume
(see `docker-compose.yml`) so it survives container restarts. To push that
same corpus to Qdrant Cloud (only useful if `RAG_BACKEND=qdrant`):

```bash
python -m scripts.push_to_qdrant
python -m scripts.push_to_qdrant --dry-run   # preview without writing
```

**On Windows**, `python -m scripts.ingest_rag_corpus` must be run with the
venv's `python` (`.venv\Scripts\python.exe`, not the global `python`) since
`unstructured[pdf]` (and its `pdfminer.six` dependency, see
`requirements.txt`) are only installed in the project's venv. The script
also works around two Windows pitfalls on its own:

- **No `libmagic`** (the C library isn't present by default on Windows):
  `unstructured` falls back on it (via `python-magic`) for MIME detection
  when no `content_type` is supplied, which used to crash with
  `ImportError: failed to find libmagic`. The script now passes an explicit
  `content_type` (derived from the file extension) to avoid that path.
- **cp1252 console**: the old messages with emoji (`⚠️`, `❌`, `⏭️`) used to
  raise a `UnicodeEncodeError` when printed to a default Windows terminal,
  masking the real error. Replaced with ASCII tags (`[ATTENTION]`,
  `[ERREUR]`, `[SKIP]`).

PDF parsing via `pdfminer` stays slow for long theses/papers (several
minutes for 20-30 PDFs) — that's expected; the script keeps going
file-by-file in the background without crashing on a problematic document.

## DL Classifier (optional, Phase B)

Satellite observation of what's *currently* growing on the parcel (see
`app/services/dl_service.py`), used in the pipeline in two deliberately
narrow and capped ways — never as a second opinion recalculating the
soil/climate score, only as supplementary field evidence, and only when the
model's confidence and the number of satellite acquisitions are sufficient
(otherwise unchanged behavior, bonus/credit = 0):

1. **Crop scoring** (`ml_service._dl_evidence_bonus`): a small capped
   additive bonus (+0.06 max, weighted by model confidence) when the
   classifier confirms a candidate crop is already actually growing on
   *this* parcel — independent field evidence from the soil/climate model,
   not a duplicate of the same signal.
2. **Nitrogen fertilization** (`agro_calc_service._dl_prairie_n_credit`): a
   nitrogen credit (25-40 kg N/ha) when the classifier observes the parcel
   currently under permanent/temporary grassland — plowing under grassland
   releases mineralized organic nitrogen over 1-2 seasons (a published
   agronomic effect, COMIFER reference), a use that matches what the DL
   actually observes (current ground cover), not a future yield prediction.

NDVI and `yield_service.py` deliberately continue to ignore the DL (and
NDVI) as a future yield/suitability signal — see their respective
docstrings for the reasoning.

```bash
pip install breizhcrops
python -m scripts.finetune_dl_service --datapath ./breizhcrops_dataset --epochs 8 --out ./dl_checkpoints/tempcnn_finetuned.pth
```

With no checkpoint present at `DL_CHECKPOINT_PATH`, `dl_observation` comes
back with `source: "unavailable"` — a clean degrade, not a blocking error.

## Tests

```bash
cd backend/agent_agriculture
python -m app.tests.test_endpoints   # fast, no network (scoring/agro-calc + /health)
```

Network integrations (cadastre/RPG/SoilGrids/Open-Meteo/Sentinel
Hub/Mistral/LiDAR HD) are tested manually against a locally running server —
see the routes above with a real point (e.g. `48.8566, 2.3522` covers
central Paris, which is mostly urban; prefer a known rural point to get a
real RPG match).

## Known Limitations

- **Crop scoring**: rules and weights documented in
  `app/services/ml_service.py` — a rule-based scorer, not a model trained on
  real RPG data. It is built to be swapped for a real
  `RandomForestClassifier` once a labeled dataset is available (same output
  shape, no changes elsewhere in the pipeline). The only learned component
  today is the optional TempCNN satellite classifier.
- **Ownership**: the service has no notion of terrain ownership; callers (the
  orchestrator, Business) enforce it. `land-profile` is therefore unchecked
  here.
- **Fertilizer/irrigation**: COMIFER/FAO-56 approximations documented in
  `app/services/agro_calc_service.py` (not a real Nmin soil test, not a
  full-season water balance).
- **Pesticide needs**: not calculated (requires a BSV module — see below).
- **Elevation** (`land_profiles.elevation_m`, Open-Elevation): never
  implemented in the original prototype — column left `null`. The 3D
  terrain view (LiDAR HD) provides visual elevation but doesn't write this
  column.

## Scaling Vision

This module is built to grow into a real product, not stay a frozen
prototype. Next steps under consideration, roughly by impact:

- **BSV module (Bulletin de Santé du Végétal)** — cross regional climate
  data with known phytosanitary risks (Japanese beetle, red palm weevil...)
  to finally compute `besoins_pesticides`, and feed the platform's Pest &
  Insect Advisor directly.
- **Real learned scoring** — replace `ml_service.py`'s explicit rules with a
  model trained on labeled RPG data at scale (a partnership with
  INRAE/AgroParisTech is envisioned), without changing the output shape the
  rest of the pipeline consumes.
- **Elevation & terrain** — write `land_profiles.elevation_m`
  (Open-Elevation, or derived from the LiDAR HD already used for the 3D
  view), to refine runoff/drainage calculations in the agro-calc.
- **A genuinely agentic agent** — replace the fixed pipeline in
  `app/routers/agriculture.py` with a tool-selection loop (via the
  platform's Orchestrator), keeping the same data contracts so nothing else
  needs to change.
- **RAG scalability** — the `RAG_BACKEND=qdrant` toggle already exists to
  decouple the vector store from a container's local disk; the next step is
  automating the Qdrant push on every ingestion run rather than as a manual
  task, for a document corpus that keeps growing without redeployment.
- **External-source robustness** — caching/rate-limiting the
  SoilGrids/Open-Meteo/Sentinel Hub calls (currently made fresh on every
  `/analyze`), to hold up under load as the number of active farmers grows,
  without depending entirely on each third-party API's instantaneous
  availability.
- **Broader crop coverage** — beyond the current nine crops, cover more
  regional sectors (market gardening, arboriculture) as the farmer base
  extends past large-scale field crops.
