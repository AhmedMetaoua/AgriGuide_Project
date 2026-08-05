# 🌾 Agricultural Waste Intelligence Agent

An autonomous AI agent that **researches, extracts, and organizes** scientific
knowledge about agricultural waste valorization — what wastes a crop
produces, their composition, how they can be transformed, and what products
and applications result — and answers questions about it through a chat
interface.

Unlike a passive "upload a PDF and ask questions" RAG tool, this agent's
**primary knowledge source is autonomous web and academic research**: given a
crop name, it plans search queries itself, searches Semantic Scholar,
CrossRef, and a general web search API (Tavily/Serper), extracts validated
facts, and synchronizes everything into a canonical knowledge base and a
vector store — with zero hallucination tolerance.

Uploading your own PDFs is supported as a **secondary, optional** input path
that reuses the exact same extraction/validation pipeline.

---

## 1. Architecture

```
agri_waste_agent/
├── config/
│   ├── settings.py           # Pydantic Settings: all API keys & thresholds, read from env/.env
│   └── logging_config.py     # Centralized logging + in-memory log capture for the UI
│
├── models.py                  # Pydantic domain models: Crop, Waste, Composition,
│                               # Transformation, Application, Reference, KnowledgeBase...
│
├── prompts/
│   ├── research_prompts.py    # Agent plans WHAT to search for
│   ├── extraction_prompts.py  # Agent extracts structured facts from a source passage
│   └── qa_prompts.py          # Agent answers user questions via RAG
│
├── services/                  # Stateless/low-level infrastructure wrappers
│   ├── llm_service.py             # LLMService interface + MistralLLMService
│   ├── web_search_service.py      # WebSearchProvider interface + Tavily/Serper
│   ├── academic_search_service.py # Semantic Scholar + CrossRef (no key required)
│   ├── embedding_service.py       # BGE embeddings via sentence-transformers
│   ├── vector_store_service.py    # Qdrant (Cloud) wrapper
│   └── storage_service.py         # Atomic canonical_knowledge.json read/write
│
├── agents/                    # Business logic, orchestrated pipeline
│   ├── researcher.py          # Plans queries, gathers sources (web + academic)
│   ├── extractor.py           # LLM extraction of one source -> typed Waste objects
│   ├── validator.py           # Code-level crop/waste validation, normalization, dedup
│   ├── knowledge_base.py      # Orchestrator: research/PDF -> extract -> validate -> sync
│   ├── reasoner.py            # Q&A agent: RAG + on-demand live research
│   └── parser.py              # PDF parsing (secondary input path)
│
├── ui/
│   └── streamlit_app.py       # Full Streamlit application (9 pages, dark mode)
│
├── knowledge/
│   └── canonical_knowledge.json   # Generated at runtime (not committed with real data)
│
├── documents/                  # Uploaded PDFs land here (secondary path)
│
├── examples/
│   ├── example_queries.py         # Programmatic usage examples
│   └── example_knowledge_base.json # Seed example (validates against the Pydantic schema)
│
├── tests/
│   ├── test_models.py          # Merge/dedup logic on Pydantic models
│   └── test_validator.py       # Crop/waste discrimination, normalization, confidence floor
│
├── requirements.txt
├── .env.example
└── README.md
```

### Data flow

```
User requests research on a crop (UI or example_queries.py)
        │
        ▼
┌───────────────┐   plans search queries (LLM)
│ ResearcherAgent│──────────────────────────────┐
└───────────────┘                               ▼
        │                          Semantic Scholar / CrossRef / Tavily-Serper
        ▼                                       │
   list[SearchResult] ◀───────────────────────────┘
        │
        ▼
┌───────────────┐  one LLM call per source, strict extraction rules
│ ExtractorAgent│  (never invent, prefer UNKNOWN, evidence hierarchy)
└───────────────┘
        │
        ▼
┌───────────────┐  code-level safety net: crop≠waste, confidence floor,
│ ValidatorAgent│  synonym normalization, deduplication
└───────────────┘
        │
        ▼
┌────────────────────┐  merges into canonical_knowledge.json (StorageService)
│ KnowledgeBaseAgent  │  and embeds+upserts into Qdrant (VectorStoreService)
└────────────────────┘
        │
        ▼
User asks a question (Streamlit chat)
        │
        ▼
┌───────────────┐  semantic search over Qdrant; if coverage is thin,
│ ReasonerAgent │  triggers a fresh KnowledgeBaseAgent research pass automatically
└───────────────┘  before answering, grounded strictly in retrieved context
```

### Why this design

- **Single Responsibility per agent.** Each agent does exactly one job
  (plan queries / extract / validate / orchestrate / answer). This keeps
  each LLM prompt focused, which measurably improves reliability with
  Mistral compared to one giant do-everything prompt.
- **Two independent lines of defense against hallucination/misclassification.**
  The extraction prompt itself enforces crop-vs-waste rules and an evidence
  hierarchy, but `ValidatorAgent` re-checks everything in plain
  deterministic Python afterward — so even if the LLM slips, bad data never
  reaches storage.
- **Provider-agnostic interfaces.** `LLMService`, `WebSearchProvider` are
  abstract base classes. Swapping Mistral for another model, or Tavily for
  another search API, means writing one new subclass and flipping a setting
  — nothing else in the codebase changes.
- **Traceability by construction.** Every `Waste`, `Composition`,
  `Transformation`, and `Application` carries its own `references: list[Reference]`
  with DOI/URL/title, so any fact displayed in the UI can be traced back to
  its source.

---

## 2. Installation

```bash
cd agri_waste_agent
python3 -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment template and fill in your keys:

```bash
cp .env.example .env
```

Required keys:
- `MISTRAL_API_KEY` — your Mistral API key (https://console.mistral.ai/)
- One of `TAVILY_API_KEY` (https://tavily.com/) or `SERPER_API_KEY` (https://serper.dev/),
  matching `WEB_SEARCH_PROVIDER` in `.env`

Optional but recommended:
- `CROSSREF_MAILTO` — your email, for CrossRef's "polite pool" (higher rate limits, no cost)
- `SEMANTIC_SCHOLAR_API_KEY` — raises Semantic Scholar rate limits (works fine without one)

---

## 3. Running

### Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Then open the printed local URL. Start on **Crop Search**, type a crop name
(e.g. "Tomato"), and click **Research this crop** to trigger the autonomous
pipeline. Once it completes, explore **Knowledge Base Statistics**, **Waste
Search**, **Transformation Search**, or ask questions in **Question & Answer
Chat**.

### Programmatic usage

```bash
python examples/example_queries.py
```

Edit the `if __name__ == "__main__":` block at the bottom of that file to
uncomment the example(s) you want to run.

### Running tests

```bash
pytest tests/ -v
```

The test suite is fully offline (no API calls) — it covers the Pydantic
model merge/dedup logic and the `ValidatorAgent` safety net.

---

## 4. Implementation roadmap / milestones

This is how the project was built, and how you can extend it further:

**Milestone 1 — Foundation (done)**
Config, logging, Pydantic models covering the full data shape (crop → waste
→ composition/transformation/application, each with references).

**Milestone 2 — Infrastructure services (done)**
LLM service (Mistral, pluggable), web search (Tavily/Serper, pluggable),
academic search (Semantic Scholar + CrossRef), embeddings (BGE), vector
store (Qdrant Cloud), atomic JSON storage.

**Milestone 3 — Agent pipeline (done)**
Researcher (query planning + source gathering) → Extractor (LLM-based
structured extraction) → Validator (deterministic safety net) →
KnowledgeBaseAgent (orchestration + sync) → Reasoner (RAG Q&A with
on-demand live research) → Parser (secondary PDF path, reuses the same
pipeline).

**Milestone 4 — UI (done)**
Full Streamlit app: Home, Dashboard, Crop/Waste/Transformation Search,
Q&A Chat with crop comparison, Knowledge Viewer (JSON export), Upload
Documents, Extraction Logs, dark mode.

**Milestone 5 — Testing (done)**
Unit tests for the validator and model merge logic; a mocked end-to-end
extraction→validation test confirmed the full data path.

**Suggested next milestones (not yet implemented):**
- **Batch/scheduled research**: a script or cron job that iterates over a
  crop watchlist and calls `needs_refresh()` + `research_and_sync_crop()`
  to keep the knowledge base current automatically.
- **Source ranking**: prioritize higher-impact journals/sources when
  multiple sources conflict, beyond the current "most recent evidence wins
  at equal tier" merge rule.
- **Multi-LLM extraction cross-validation**: run extraction with two
  different LLMs and only accept facts both agree on, for an even stronger
  hallucination safety net on high-stakes data (e.g. exact composition
  percentages).
- **Export to PDF/report**: generate a shareable PDF report per crop from
  the knowledge base (the `pdf` skill/library used elsewhere in this
  environment would fit well here).
- **Authentication/multi-user**: if this moves beyond a local tool, add
  user accounts and scope the knowledge base or usage quotas per user.

---

## 5. Extending the system

**Add a new LLM provider:** implement a new subclass of `LLMService` in
`services/llm_service.py` (see `MistralLLMService` for the pattern), then
register it in `get_llm_service()` and set `LLM_PROVIDER` in `.env`.

**Add a new search provider:** implement `WebSearchProvider` in
`services/web_search_service.py`, register it in `get_web_search_provider()`.

**Add a new crop/waste term to the validation rules:** edit
`NON_CROP_TERMS` and `SYNONYM_CANONICAL_MAP` in `agents/validator.py` (and
mirror the change in `prompts/extraction_prompts.py`'s CROP vs WASTE
VALIDATION / NORMALIZATION sections, so both the LLM-level and code-level
defenses stay in sync).

**Add a new Waste field:** extend the `Waste` model in `models.py`, then
update the JSON schema in `prompts/extraction_prompts.py` and the
`_build_waste` method in `agents/extractor.py` to populate it.

---

## 6. Known limitations

- Academic abstracts (not full papers) are the main extraction input for
  peer-reviewed sources; deep facts buried in a paper's full text/tables
  beyond the abstract will be missed unless a web source surfaces them too.
- `ValidatorAgent`'s `NON_CROP_TERMS` list is a practical, non-exhaustive
  safety net — very obscure plant-part terminology not in the list could
  theoretically slip through if the extraction prompt itself also missed it.
- `canonical_knowledge.json` is local/file-based; for a multi-user
  production deployment, swap `StorageService` for a real database.
  The vector store already runs on Qdrant Cloud (`VectorStoreService`).
