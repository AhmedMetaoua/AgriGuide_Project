# Waste Valorization Agent

**Status: ✅ Live read-only API backed by a populated knowledge base · offline research pipeline available through Streamlit.**

## Role
Given a recommended crop, surfaces its agricultural waste streams and how they
can be valorized (transformations, products, applications). It feeds the
frontend's crop detail view today and is designed to feed Marketplace waste
listings.

The module is two systems around one knowledge base:

## System 1 — Live API (port 8004) — what the product uses
Read-only; **no LLM or search keys required**. Serves an in-memory
(`lru_cache`) view of `knowledge/canonical_knowledge.json`, which currently
holds **53 crops and 321 waste entries**.

| Method | Route | Description |
|---|---|---|
| `POST` | `/waste/for-crops` | Batch lookup for Agriculture's top crops (`{"cultures": ["ble_tendre", "mais", ...]}`) |
| `GET` | `/waste/marketplace-suggestions?culture=X` | Wastes with a real transformation/product/application story, formatted as a listing suggestion |
| `POST` | `/waste/reload` | Clear the cache after editing the JSON |
| `GET` | `/health` | Health check |

`api/crop_mapping.py` bridges Agriculture's French crop keys (`ble_tendre`,
`mais`, …) to the knowledge base's English canonical names and ranks wastes per
crop by richness (transformation / product / application count → confidence →
composition detail), capped at 5 wastes per crop.

## System 2 — Offline research pipeline (Streamlit, not exposed by the API)
A five-agent pipeline orchestrated by `KnowledgeBaseAgent`:

```
Researcher → Extractor → Validator → (storage + Qdrant sync) → Reasoner
```
- **Researcher** — an LLM plans up to 6 search queries per crop and runs them
  against Semantic Scholar + CrossRef (academic) and Tavily/Serper (web).
- **Extractor** — a non-LLM character-count pre-filter, then batches sources
  into cost-controlled Mistral calls that parse structured crop/waste objects
  with references.
- **Validator** — deterministic Python guard against the LLM labeling a plant
  part as a crop.
- **Storage** — atomic JSON write (temp file then rename). The JSON is the
  source of truth; the Qdrant index is derived and disposable
  (`scripts/migrate_to_qdrant.py` rebuilds it).
- **Reasoner** — RAG Q&A; if fewer than 2 vector hits come back for a crop it
  triggers a live research pass first (self-healing KB). Also offers
  `compare_crops()`.
- A PDF upload path (`agents/parser.py`) feeds the same extractor/validator.

The Streamlit UI covers home, dashboard, crop / waste / transformation search,
Q&A chat, knowledge viewer, PDF upload and logs.

## Engineering notes
- Local **BGE sentence-transformers** embeddings (not the Mistral embedding
  API, unlike the rest of the platform).
- Vector store migrated from ChromaDB to **Qdrant Cloud**.
- LLM provider abstracted behind an interface (`settings.llm_provider`).
- Thread-safe rate limiting that penalizes all threads on a 429, honors
  `Retry-After` and adds jitter — covered by dedicated tests.
- Optional LangSmith tracing that no-ops cleanly when unconfigured.

## Tests
```bash
python -m pytest backend/waste_agents/tests
```
Covers the validator, batching, rate limiting, models, text utilities,
composition and tracing.

## Roadmap
- Wire `/waste/marketplace-suggestions` into Marketplace once that service
  exists.
- Remove the leftover `vector_db/chromadb/` folder from the Chroma → Qdrant
  migration, if present.

## Run locally
```bash
cd backend/waste_agents
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8004        # live API
streamlit run ui/streamlit_app.py                # research / ops tool
```
Research mode needs `MISTRAL_API_KEY`, `QDRANT_URL`/`QDRANT_API_KEY` and a
search key (`TAVILY_API_KEY` or `SERPER_API_KEY`); the live API needs none.
The frontend reads `VITE_AGENT_WASTE_URL` (default `http://localhost:8004`).
