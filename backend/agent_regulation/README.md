# Agent Regulation

**Status: ⚠️ Partially real — RAG + subsidy search work; 2 advertised
features are unimplemented stubs; not wired into the farmer's state.**

## Role
LangChain tool-calling agent answering French agricultural regulation
and subsidy questions, backed by hybrid RAG + live web/subsidy search.

## Architecture
A **Mistral small** model (tool selection) decides which tool(s) to
call; a **Mistral large** model writes the final grounded answer from
tool outputs. Two-stage design for cost control.

## Real tools (3)
1. **`recherche_reglementation_agricole`** — hybrid RAG over a real
   **Qdrant** collection: dense (Mistral embeddings) + BM25 sparse,
   fused server-side via Reciprocal Rank Fusion (prefetch 20/channel →
   top-5, dedup near-identical chunks). *(Note: the project's original
   architecture doc specifies a Postgres `pgvector` table for this —
   the actual implementation uses Qdrant Cloud instead; pick one and
   update the docs to match.)*
2. **`recherche_aides_financieres_agricoles`** (Subsidy Search) — 6
   templated 2026-campaign web queries (Tavily), official-domain +
   "2026" ranked, structured-output Mistral extraction (strict
   no-invent prompt), regex French-date parsing to exclude
   expired/closed aid and sort by nearest deadline.
3. **`recherche_web_aides_agricoles`** — general web search, split
   unrestricted + official-domain-whitelisted, merged official-first.

System prompt enforces strict tool-call order, "verbatim facts only"
grounding, official-over-unofficial contradiction handling, and a
mandatory sources trailer built only from URLs the tools actually
returned.

## Subsidy cache
- `GET /subsidies` — reads the Postgres cache (no live search).
- `POST /subsidies/sync` — re-runs extraction against 3 default
  queries, upserts via `ON CONFLICT (source_url)`. **No scheduler and
  no frontend trigger exist yet** — must be called manually.

## Not implemented (despite being listed as features)
- **Form filling** (`form_filler_tool.py`) — empty stub.
- **Document review** (`document_reviewer_tool.py`) — empty stub.
- Neither is registered in the agent's tool list.

## Architectural gap
`POST /chat` only takes `{question}` — **no `user_id`, no `terrain_id`,
no auth, no conversation history.** The agent is fully anonymous and
stateless, and can't currently answer parcel-specific questions. This
matches the missing orchestrator (see root README): Regulation was
designed to receive farmer context through it and currently doesn't.

## Test coverage
Strong on the subsidy pipeline (store/sync/extraction/date-parsing);
no tests for the RAG tool or the hybrid retriever itself.

## Run locally
```bash
cd backend/agent_regulation
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005
```
