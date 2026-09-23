# Waste Agents (Valorisation / Circular Economy Knowledge Base)

**Status: ⚠️ Two systems, one real path missing its data file.**

## Role
Given a recommended crop, surfaces its agricultural waste streams and
how they can be valorized (transformations, products, applications) —
feeding both the frontend's crop detail view and (eventually)
Marketplace listing suggestions for waste.

## System 1 — Live API (port 8004) — what the product uses
Read-only, no LLM/search keys required. Serves an in-memory
(`lru_cache`) view of `canonical_knowledge.json`.

- `POST /waste/for-crops` — batch lookup for Agriculture's top crops.
- `GET /waste/marketplace-suggestions?culture=X` — wastes with a real
  transformation/product/application story, formatted for a listing.
- `POST /waste/reload` — clears the cache after a manual JSON edit.

`crop_mapping.py` bridges Agriculture's French crop keys (`ble_tendre`,
`mais`...) to the KB's English canonical names, and ranks wastes per
crop by richness (transformation/product/application count → confidence
→ composition detail), capped at 5 wastes/crop.

**⚠️ `canonical_knowledge.json` is not present in this repo snapshot**
(`knowledge/` and `documents/` are empty) — the live API will degrade
until this file is generated (System 2, below) or committed.

## System 2 — Offline research pipeline (Streamlit only, not exposed via API)
A genuine 5-agent pipeline, orchestrated by `KnowledgeBaseAgent`:

```
Researcher → Extractor → Validator → (storage + Qdrant sync) → Reasoner
```
- **Researcher** — LLM plans ≤6 search queries/crop, runs them against
  Semantic Scholar + CrossRef (academic) and Tavily/Serper (web).
- **Extractor** — non-LLM char-count pre-filter, then batches sources
  into cost-controlled Mistral calls to parse structured Crop/Waste
  objects with references.
- **Validator** — deterministic Python guard against the LLM mislabeling
  a plant part as a crop.
- **Storage** — atomic JSON write (temp-file-then-rename); JSON is
  source of truth, the Qdrant index is disposable/derived
  (`scripts/migrate_to_qdrant.py` rebuilds it by re-embedding).
- **Reasoner** — RAG Q&A; auto-triggers a live research pass if fewer
  than 2 vector hits come back for a crop before answering
  (self-healing KB); has a `compare_crops()` mode too.
- A PDF upload path (`parser.py`) feeds the same extractor/validator
  pipeline as web sources.

Streamlit UI pages: home, dashboard, crop search, waste search,
transformation search, Q&A chat, knowledge viewer, PDF upload, logs.

## Notable engineering choices (differ from the rest of the monorepo)
- Embeddings are **local** sentence-transformers BGE, not Mistral API.
- Migrated off ChromaDB to **Qdrant Cloud** (the `vector_db/chromadb/`
  folder is migration leftover cruft).
- LLM provider abstracted behind an interface (`settings.llm_provider`).
- Real rate-limiting: thread-safe, penalizes all threads on a 429,
  honors `Retry-After`, adds jitter — with dedicated tests.
- Optional LangSmith tracing, no-ops cleanly when unconfigured.

## To do
- Generate/commit `canonical_knowledge.json` so `POST /waste/for-crops`
  actually returns data.
- Wire this into Marketplace once that module exists.

## Run locally
```bash
cd backend/waste_agents
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8004        # live API
streamlit run ui/streamlit_app.py                # research/ops tool
```
