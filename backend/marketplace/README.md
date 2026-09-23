# Module Marketplace (économie circulaire)

**Status: ❌ Design doc only — no code exists yet.**

## Role (as designed, not yet built)
Simple listings for harvests and valorizable agricultural waste. No
payment, no delivery — description + price/quantity + contact only.
Not an agent: plain FastAPI CRUD. The only LLM use would be to draft a
listing's title/description from structured fields, and to suggest a
waste's utility text from `waste_agents`' reference data.

## Intended trigger
Agent Monitoring detects the harvest window (via
`decision_allocations.date_maturite_prevue`) and calls this module to
prepare a suggested listing — price via the same RNM/FranceAgriMer
source Business uses, quantity from the confirmed allocation. **This
trigger doesn't exist either, since Monitoring has no scheduler and this
module has no code to call.**

## Planned endpoints
- `POST /annonces` — create a listing (harvest or waste).
- `GET /annonces?type=&region=&culture=` — browse/filter.
- `PATCH /annonces/{id}/statut` — disponible → réservé → expiré.
- `GET /dechets_reference?culture=` — suggested waste utilities (would
  read `waste_agents`' knowledge base).

## Moderation (as designed)
Only authenticated farmers with a verified terrain can post — no
anonymous posts, no account unlinked to a terrain.

## Schema already exists and is waiting
`annonces` and `dechets_reference` tables are defined in
`database/schema.sql` — building this module is a matter of CRUD
routes against tables that already exist, no schema work needed.

## What's needed to build this
1. FastAPI service scaffold (mirror `auth/`'s structure — plain CRUD,
   psycopg2, JWT dependency copied from an existing agent).
2. `POST /annonces` + `GET /annonces` first (unblocks manual listing).
3. Wire `waste_agents`' `/waste/marketplace-suggestions` for waste
   listing drafts.
4. Add the Monitoring→Marketplace trigger once Monitoring has a
   scheduler.
