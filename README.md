# AgriMent

**Think Smart. Farm Smarter.**

Presented by **DerjaGPT / TAIAN**

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
  recommend the crop options best suited to a given parcel. Combines a
  machine-learning crop-scoring model with a satellite deep-learning
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

- **Pest & Insect Advisor** — Identifies pests and plant diseases directly
  from photo uploads, giving farmers a fast first read on an emerging
  problem.
- **Community Alerts** — Lets farmers report and share pest/disease alerts
  with neighboring farms, turning individual observations into an early
  warning network.
- **Monitoring Agent** — Provides daily automated tracking of environmental
  and farm risk indicators, spending, and alerts through a live dashboard.

### 3. Waste Valorization & Marketplace

- **Waste Valorization** — Identifies processing and resale pathways for
  agricultural residues and waste, built on a scientific knowledge base
  spanning dozens of crops, and surfaces relevant options directly alongside
  a farmer's crop recommendations.
- **Agricultural Marketplace** — Directly connects farmers with buyers for
  harvested crops and agricultural waste/residues.

## Architecture

AgriMent is built as a set of independent AI agents, each a FastAPI service
with its own Postgres tables, coordinated by a supervisor agent and a
shared React frontend:

```
Frontend (React + TanStack Start)
        │
        ▼
Orchestrator — routes requests across agents based on the farmer's stage
        │
        ├── Regulation Advisor    (RAG: Code Rural, Cerfa, aides)
        ├── Agriculture Advisor   (satellite, soil, climate → ML + DL)
        ├── Business Advisor      (scenario scoring + market intelligence)
        ├── Monitoring Agent      (daily tracking, alerts)
        └── Waste Valorization    (crop → waste → transformation → marketplace)
        │
        ▼
Shared data layer: PostgreSQL + PostGIS · Auth (JWT, shared across agents)
```

## Repo Structure

```
AgriMent_Project/
├── backend/
│   ├── orchestrator/         # Supervisor agent — cross-agent routing
│   ├── auth/                  # Accounts, roles (farmer/buyer), shared JWT
│   ├── agent_regulation/      # Regulation Advisor (RAG)
│   ├── agent_agriculture/     # Agriculture Advisor (analysis, ML, RAG, chat, 3D)
│   ├── agent_business/        # Business Advisor (scenario scoring, market data)
│   ├── agent_monitoring/      # Monitoring Agent (daily tracking, alerts)
│   ├── waste_agents/          # Waste Valorization
│   └── marketplace/           # Agricultural Marketplace
├── database/
│   └── schema.sql             # Full PostgreSQL + PostGIS schema
├── frontend/                  # React + TanStack Start (Vite)
├── docs/
│   ├── ARCHITECTURE.md        # Detailed technical architecture
│   └── team_guide.md          # Team ownership, conventions
├── scripts/
│   ├── setup_venv.sh / .ps1   # Shared Python venv setup, one-time
│   └── run_backend.py         # Launches all agents with uvicorn
├── dev.sh / dev.ps1            # Postgres + all agents, one command
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
- **Crop recommendation** — a machine-learning model scoring nine crops
  (including potato, sugar beet, soybean, and protein peas), with
  irrigation/fertilizer/pesticide needs and yield estimation.
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
| Business Advisor | 8000 |
| Auth | 8001 |
| Agriculture Advisor | 8002 |
| Monitoring Agent | 8003 |
| Waste Valorization | 8004 |
| Regulation Advisor | 8005 |
| Postgres (host, outside Docker) | 5434 |

### Environment Variables

All in a root `.env` file (never committed). See `.env.example` for the
complete list and defaults. Key ones:

| Variable | Used by | Notes |
|---|---|---|
| `MISTRAL_API_KEY` | Agriculture, Business, Regulation | free-tier key from console.mistral.ai |
| `SENTINEL_HUB_CLIENT_ID` / `_SECRET` | Agriculture (NDVI, satellite classification) | free Copernicus Data Space Ecosystem account |
| `JWT_SECRET_KEY` | Auth ↔ all agents | shared signing secret; rotate before any real deployment |
| `DATABASE_URL` | all agents | auto-rewritten `db` → `localhost:5434` when running outside Docker |
| `RAG_BACKEND` | Agriculture | `chroma` (default, local) or `qdrant` (Qdrant Cloud) |
| `QDRANT_URL` / `QDRANT_API_KEY` | Agriculture (only if `RAG_BACKEND=qdrant`) | optional |

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

The frontend runs on Vite's dev server and talks to each agent directly on
its own port (see table above).

## Team Ownership

See `docs/team_guide.md` for full detail (inter-module dependencies, RGPD
conventions, Git branching). Summary:

| Team | Owns | Depends on |
|---|---|---|
| Agriculture | `agent_agriculture/` | — |
| Business | `agent_business/` | Agriculture (crop recommendations) |
| Regulation | `agent_regulation/` | — (independent RAG pipeline) |
| Monitoring & Marketplace | `agent_monitoring/`, `marketplace/` | Agriculture, Business |
| Orchestrator & Frontend | `orchestrator/`, `frontend/` | all agents |
| Auth | `auth/` | — |

**Shared rule** — each agent reads/writes only its own tables; no direct
cross-agent database access.
