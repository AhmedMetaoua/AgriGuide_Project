# Orchestrateur (Agent superviseur)

**Status: ❌ Design doc only — no code exists yet. This is the single
highest-leverage gap in the whole project (see root README).**

## Role (as designed, not yet built)
Single entry point for the frontend. Routes each request to the right
sub-agent based on detected intent and the farmer's current state
(onboarding → terrain_selectionne → analyse_terminee →
scenarios_proposes → decision_confirmee → suivi_actif — see
`docs/ARCHITECTURE.md` §2).

## Intended stack
LangGraph — a "router" node decides, rather than a manual frontend
menu (though the frontend should keep explicit tab navigation too, for
users who prefer clicking to chatting).

## Does NOT do business logic
Only routing + context aggregation (`terrain_id`, state, recent
history) to hand off to the chosen sub-agent.

## Intended endpoint
```
POST /chat {user_id, terrain_id, message}
```
→ determine target agent → forward → return the formatted response to
the frontend.

## Why this matters right now
Every sub-agent currently gets called **directly** by the frontend at
its own hardcoded port. This works, but it means:
- The frontend has become the de facto orchestrator, and every new
  cross-agent workflow has to be hand-wired into React rather than
  handled centrally.
- Regulation in particular never receives `terrain_id`/`user_id` at
  all (its `/chat` only takes `{question}`), so it structurally can't
  be state-aware the way this design assumes every agent should be.
- The farmer-journey state machine described in
  `docs/ARCHITECTURE.md` isn't actually enforced anywhere — each
  frontend page independently decides what to show.

## What's needed to build this
1. A LangGraph graph with one router node + one edge per sub-agent.
2. Simple intent classification (keyword or small-model based) to pick
   the target agent from `message`.
3. Context aggregation: look up the farmer's current state from
   `farmer_decisions.statut` (+ presence of upstream rows) and pass it
   through to the sub-agent.
4. Migrate the frontend's direct per-agent API calls behind this one
   endpoint incrementally — start with Regulation (biggest state-
   awareness gap), since it's the least entangled with the existing UI.

## Run locally (once built)
```bash
cd backend/orchestrator
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006
```
