# Regulation Advisor

**Status: ⚠️ Partially real — hybrid RAG and subsidy search work; two advertised tools are stubs; the agent is anonymous and stateless.**

## Role
A LangChain tool-calling agent that answers French agricultural regulation and
subsidy questions (Code Rural, Cerfa, aids), backed by hybrid RAG plus live web
and subsidy search. Every answer ends with sources built only from URLs the
tools actually returned.

## Architecture
Two Mistral model instances: one **selects the tools** to call, a second
**writes the final answer** from the tool outputs. Both read their model name
from `MISTRAL_MODEL` (default `mistral-large-latest`) — the two roles are
separate objects so they can be pointed at different models later (a cheaper
one for tool selection) without touching the agent logic.

## Tools (3, all real)
1. **`recherche_reglementation_agricole`** — hybrid retrieval over a
   **Qdrant** collection: dense Mistral embeddings + BM25 sparse vectors fused
   server-side with Reciprocal Rank Fusion (20 candidates per channel → top 5,
   near-duplicate chunks removed).
2. **`recherche_aides_financieres_agricoles`** — subsidy search: six templated
   campaign-year web queries (Tavily), official-domain results ranked first,
   structured Mistral extraction under a strict no-invention prompt, and
   French-date parsing to drop expired aid and sort by nearest deadline.
3. **`recherche_web_aides_agricoles`** — general web search, split between
   unrestricted and official-domain-only results, merged official-first.

The system prompt enforces tool-call order, verbatim-facts-only grounding, and
official-over-unofficial handling of contradictions.

## Endpoints
| Method | Route | Description |
|---|---|---|
| `POST` | `/chat` | `{question}` → grounded answer with sources |
| `GET` | `/subsidies` | Reads the Postgres subsidy cache (no live search) |
| `POST` | `/subsidies/sync` | Re-runs extraction on 3 default queries and upserts (`ON CONFLICT (source_url)`) |
| `GET` | `/health` | Health check |

`/subsidies/sync` has **no scheduler and no frontend trigger yet** — call it
manually.

## Known limitations
- **Form filling** (`form_filler_tool.py`) and **document review**
  (`document_reviewer_tool.py`) are empty stubs and are not registered as
  tools.
- **Anonymous and stateless**: `/chat` takes only `{question}` — no `user_id`,
  no `terrain_id`, no auth, no conversation history — so it cannot answer
  parcel-specific questions yet. Passing farmer context through the
  orchestrator is the intended fix.
- **Docs vs. implementation**: `docs/ARCHITECTURE.md` describes a Postgres
  `pgvector` store; the implementation uses Qdrant Cloud.

## Tests
Strong coverage of the subsidy pipeline (store, sync, extraction, date
parsing) and the web-search tool; none yet for the RAG tool or the hybrid
retriever.
```bash
python -m pytest backend/agent_regulation/tests
```

## Run locally
```bash
cd backend/agent_regulation
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005
```
Required in the root `.env`: `MISTRAL_API_KEY`, `QDRANT_URL`,
`QDRANT_COLLECTION_NAME`; optional `QDRANT_API_KEY`, `MISTRAL_MODEL`,
`WEB_SEARCH_API_KEY` (Tavily). A Streamlit test UI lives in
`interface_test/`.
