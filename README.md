# AgriMent

**Think Smart. Farm Smarter.**

Presented by **DerjaGPT / TALAN**

AgriMent is a smart agricultural platform that combines AI agents, machine
learning models, and RAG (Retrieval-Augmented Generation) to help farmers
optimize crop selection, protect yields, navigate regulations, and valorize
agricultural waste — from first parcel analysis through to daily monitoring
and market access.

## Core Concept

A farmer describes or selects a plot of land. AgriMent cross-references
real-time satellite, soil, and climate data to recommend the best-suited
crops, model realistic profitability scenarios, surface the regulations and
subsidies that apply, protect the resulting yield, and connect what's grown
(and what's left over) to buyers — all through a single coherent platform
powered by a set of specialized AI agents.

## Key Features

### 1. Diagnostic & Decision Making

- **Agriculture Advisor** — Analyzes soil composition, weather patterns,
  satellite imagery (NDVI, land-cover classification), and farm equipment to
  recommend the crop options best suited to a given parcel. Combines an
  explainable crop-scoring engine with a satellite deep-learning
  classifier, computes irrigation/fertilizer/pesticide needs and yield
  estimates, and produces a fully sourced AI-generated report grounded in a
  scientific and regulatory document corpus (RAG). Includes an interactive
  3D terrain view and a contextual chat assistant that can answer questions
  about the analyzed parcel, the farmer's own profile, and general
  agronomic knowledge.
- **Business Advisor** — Evaluates profitability and risk through financial
  modeling across three realistic scenarios per crop recommendation, using
  real market-price intelligence rather than pure LLM estimation, and tracks
  the farmer's confirmed decisions over time.
- **Regulation Advisor** — Uses RAG to guide farmers through regulatory
  compliance (Code Rural, Cerfa forms) and helps identify available
  agricultural aid and subsidies, with every answer sourced back to its
  underlying document.

### 2. Crop Protection & Monitoring

- **Pest & Insect Advisor** *(planned)* — Identifies pests and plant diseases directly
  from photo uploads, giving farmers a fast first read on an emerging
  problem.
- **Community Alerts** *(planned)* — Lets farmers report and share pest/disease alerts
  with neighboring farms, turning individual observations into an early
  warning network.
- **Monitoring Agent** — Generates a daily AI briefing from live weather and
  the farmer's confirmed crop plan — alerts, irrigation advice, tasks and
  per-crop risk — and tracks real versus planned spending on a live
  dashboard.

### 3. Waste Valorization & Marketplace

- **Waste Valorization** — Identifies processing and resale pathways for
  agricultural residues and waste, built on a scientific knowledge base
  spanning dozens of crops, and surfaces relevant options directly alongside
  a farmer's crop recommendations.
- **Agricultural Marketplace** — Directly connects farmers with buyers for
  harvested crops and agricultural waste/residues. *(UI prototype on sample
  data; backend service planned.)*

## Architecture

AgriMent is built as a set of independent AI agents, each a FastAPI service
with its own Postgres tables, coordinated by a supervisor agent and a
shared React frontend:

```
Frontend (React + TanStack Start)
        │
        ▼
Orchestrator — relays the journey steps (analysis → scenarios → monitoring)
        │
        ├── Regulation Advisor    (RAG: Code Rural, Cerfa, aides)
        ├── Agriculture Advisor   (satellite, soil, climate → scoring + DL)
        ├── Business Advisor      (scenario scoring + market intelligence)
        ├── Monitoring Agent      (daily briefing)
        └── Waste Valorization    (crop → waste → transformation → marketplace)
        │
        ▼
Shared data layer: PostgreSQL + PostGIS · Auth (JWT, verified by every agent
through the shared `agriment_shared` package)
```

The orchestrator is **hybrid by design**: only the sequential journey steps
route through it. Plain CRUD (sign-in, terrain editing) and free-form search
(Regulation, Waste) stay direct frontend → agent calls. See
`backend/orchestrator/README.md`.

**The farmer journey:** pick a parcel → data-driven crop recommendation →
financially scored scenarios → confirm a decision (human-in-the-loop) → daily
monitoring → sell harvest and waste.

## Project Status

| Module | Status | Notes |
|---|---|---|
| Auth | ✅ Complete | Sign-up/in, roles, terrains (PostGIS), JWT |
| Agriculture Advisor | ✅ Complete | Parcel resolution, soil/climate/NDVI, scoring, sourced RAG report, chat, 3D relief, persisted land profile |
| Business Advisor | ✅ Complete | 3 deterministic scenarios, market intelligence, human-in-the-loop decision |
| Orchestrator | ✅ Built, not yet used by the UI | 3 journey endpoints, LangGraph relays, tested |
| Shared package | ✅ In use | Common JWT verification |
| Waste Valorization | ✅ Live API + offline research pipeline | 53 crops / 321 waste entries in the knowledge base |
| Monitoring Agent | 🟡 Works, no persistence | Daily briefing; spend tracking is client-side only |
| Regulation Advisor | 🟡 Partial | Hybrid RAG + subsidy search work; form-filling and document review are stubs; no farmer context |
| Marketplace | 🟠 UI prototype | Frontend on sample data; backend service not built |
| Pest & Insect Advisor, Community Alerts | 📋 Planned | Not started |

Each module's README has its own detail and known limitations.

## Repo Structure

```
AgriMent_Project/
├── backend/
│   ├── orchestrator/         # Supervisor agent — journey relays + status
│   ├── shared/                # agriment_shared — common JWT verification
│   ├── auth/                  # Accounts, roles (farmer/buyer), issues the JWT
│   ├── agent_regulation/      # Regulation Advisor (RAG)
│   ├── agent_agriculture/     # Agriculture Advisor (analysis, ML, RAG, chat, 3D)
│   ├── agent_business/        # Business Advisor (scenario scoring, market data)
│   ├── agent_monitoring/      # Monitoring Agent (daily briefing)
│   ├── waste_agents/          # Waste Valorization
│   └── marketplace/           # Agricultural Marketplace (not built yet)
├── database/
│   ├── schema.sql             # Full PostgreSQL + PostGIS schema
│   └── migration_*.sql        # Incremental migrations for existing databases
├── frontend/                  # React + TanStack Start (Vite)
├── docs/
│   ├── ARCHITECTURE.md        # Detailed technical architecture
│   └── team_guide.md          # Team ownership, conventions
├── scripts/
│   ├── setup_venv.sh / .ps1   # Shared Python venv setup, one-time
│   └── run_backend.py         # Launches all agents with uvicorn
├── dev.sh / dev.ps1            # Postgres + all agents, one command
├── requirements.txt            # Shared deps for local dev (+ requirements-ml.txt)
├── .env.example                # All environment variables
└── docker-compose.yml
```

## Agriculture Advisor — Feature Detail

The platform's flagship module:

- **Parcel resolution** — IGN cadastre, RPG, or manual entry; neighboring
  parcels within a configurable radius.
- **Multi-source analysis** — soil (SoilGrids), weather (Open-Meteo), NDVI
  (Sentinel Hub / Copernicus Data Space), and satellite land-cover
  classification via a deep-learning model (TempCNN pre-trained on
  BreizhCrops, fine-tuned).
- **Crop recommendation** — a documented, rule-based scorer over nine crops
  (including potato, sugar beet, soybean, and protein peas) that returns
  per-crop feature importance, with irrigation/fertilizer/pesticide needs and
  yield estimation. It shares its output shape with a trained classifier so a
  learned model can replace it later without touching the rest of the
  pipeline.
- **Sourced AI report** — generated via Mistral, grounded in a RAG corpus
  (scientific literature + regulatory documents) with inline citations.
- **Contextual chatbot** — answers grounded in the document corpus, the
  currently analyzed parcel, and the logged-in farmer's own profile
  (terrains, equipment).
- **3D terrain view** — interactive relief mesh generated from IGN LiDAR HD
  data.

## Technical Setup

### Ports

| Service | Port |
|---|---|
| Orchestrator | 8000 |
| Auth | 8001 |
| Agriculture Advisor | 8002 |
| Monitoring Agent | 8003 |
| Waste Valorization | 8004 |
| Regulation Advisor | 8005 |
| Business Advisor | 8006 |
| Postgres (host, outside Docker) | 5434 |

### Environment Variables

All in a root `.env` file (never committed). See `.env.example` for the
complete list and defaults. Key ones:

| Variable | Used by | Notes |
|---|---|---|
| `MISTRAL_API_KEY` | Agriculture, Business, Monitoring, Regulation, Waste | free-tier key from console.mistral.ai |
| `MISTRAL_MODEL` | all LLM-backed agents | one place to choose the model; defaults to `mistral-large-latest` |
| `SENTINEL_HUB_CLIENT_ID` / `_SECRET` | Agriculture (NDVI, satellite classification) | free Copernicus Data Space Ecosystem account |
| `JWT_SECRET_KEY` | Auth ↔ all agents | shared signing secret; rotate before any real deployment |
| `DATABASE_URL` | all agents | auto-rewritten `db` → `localhost:5434` when running outside Docker |
| `RAG_BACKEND` | Agriculture | `chroma` (default, local) or `qdrant` (Qdrant Cloud) |
| `QDRANT_URL` / `QDRANT_API_KEY` | Regulation, Waste, Agriculture (if `RAG_BACKEND=qdrant`) | Qdrant Cloud |
| `QDRANT_COLLECTION_NAME` | Regulation | |
| `WEB_SEARCH_API_KEY` / `TAVILY_API_KEY` | Regulation / Waste research mode | optional web search |
| `MARKET_DATA_DIR` | Business | folder with the Agreste CSVs and FranceAgriMer PDFs |
| `AGENT_*_URL` | Orchestrator | sub-agent URLs; defaults match the port table |
| `VITE_MAPBOX_TOKEN` | Frontend | 3D terrain view |
| `VITE_SKIP_AUTH` | Frontend | dev-only auth bypass — never in production |

> Never commit your `.env`; it holds API keys. Rotate any key that has been
> shared or exposed.

### Running the Backend

**Prerequisite: Python 3.12** (not 3.13 — `numpy`/`pyproj` don't yet ship
Windows wheels for 3.13 and fail to build from source).

```bash
cp .env.example .env    # fill in API keys — see table above
```

**1. Create the shared virtual environment (one-time, from repo root):**

```powershell
# Windows
py -3.12 -m venv .venv
.\scripts\setup_venv.ps1
```

```bash
# macOS / Linux
python3.12 -m venv .venv
./scripts/setup_venv.sh
```

**2. Install the ML stack (RAG, deep learning, PDF parsing):**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```

```bash
./.venv/bin/python -m pip install -r requirements-ml.txt
```

> **Windows note** — if `chromadb` fails to install on `chroma-hnswlib`
> (no MSVC compiler): install `chroma-hnswlib==0.7.5`, then
> `chromadb==0.5.15 --no-deps`, then chromadb's real runtime dependencies by
> hand (`overrides`, `posthog`, `pypika`, `typer`, `rich`,
> `importlib-resources`, `kubernetes`, `build`, the `opentelemetry-*`
> stack). Full command in `backend/agent_agriculture/README.md`.

**3. Launch Postgres + every agent, one command:**

```powershell
.\dev.ps1
```

```bash
./dev.sh
```

This starts Postgres via Docker and runs every agent directly with
`uvicorn` inside the shared venv. To run a single agent instead:

```powershell
.\.venv\Scripts\python.exe scripts\run_backend.py --only agriculture
```

**Alternative — full Docker stack:**

```bash
docker compose up -d
```

### Running the Frontend

```bash
cd frontend
npm install          # or bun install (bun.lock present)
cp .env.example .env.local
# set VITE_SKIP_AUTH=true in .env.local for auth-free local UI development
npm run dev
```

The frontend runs on Vite's dev server and currently talks to each agent
directly on its own port (see table above). The orchestrator's journey
endpoints are built and tested but not yet called by the UI.

### Tests

Run each suite on its own (the agents all use a package named `app`). From the
repo root, with the virtualenv active:

```bash
python -m pytest backend/shared -q
python -m pytest backend/orchestrator/tests -q       # set JWT_SECRET_KEY first
python -m pytest backend/agent_business/app/tests -q
python -m pytest backend/agent_regulation/tests -q
python -m pytest backend/waste_agents/tests -q
```

Script-style suites (run from the module folder; they print `[OK]` lines):

```bash
cd backend/agent_agriculture && python -m app.tests.test_endpoints   # no network
cd backend/auth && python -m app.tests.test_endpoints                # needs Postgres
```

Business runs its suite with in-memory persistence and auth disabled, so no
database is needed.

## Team Ownership

See `docs/team_guide.md` for full detail (inter-module dependencies, RGPD
conventions, Git branching). Summary:

| Team | Owns | Depends on |
|---|---|---|
| Agriculture | `agent_agriculture/` | — |
| Business | `agent_business/` | Agriculture (crop recommendations) |
| Regulation | `agent_regulation/` | — (independent RAG pipeline) |
| Monitoring & Marketplace | `agent_monitoring/`, `marketplace/` | Agriculture, Business |
| Orchestrator & Frontend | `orchestrator/`, `shared/`, `frontend/` | all agents |
| Auth | `auth/` | — |

**Shared rule** — each agent reads/writes only its own tables; no direct
cross-agent database access.
