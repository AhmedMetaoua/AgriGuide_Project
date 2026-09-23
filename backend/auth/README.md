# Auth

**Status: ✅ Fully real — the platform's foundational, best-tested
service.**

## Role
Sign-up/sign-in and farmer profile management (equipment + declared
terrains). Every other agent depends on the JWT this service issues
and, indirectly, on the `terrains`/`users` rows it owns.

## Roles
- **farmer** — full access (advisors + marketplace write). Must declare
  owned equipment and at least one terrain at signup.
- **acheteur** — marketplace read-only, no advisor access.

## Endpoints
- `POST /auth/signup` — `{email, password, nom, telephone?, role,
  equipements?, terrains?}` → creates the account (+ equipment/terrains
  if `role=farmer`) and returns a token.
- `POST /auth/signin` → token + profile.
- `GET /auth/me` → full profile (`Authorization: Bearer <token>`).
- `PUT /auth/me/equipements` — replace declared equipment (farmer only).
- `POST/PUT/DELETE /auth/me/terrains/{id}` — terrain CRUD (farmer only).

## Security
- Passwords hashed with bcrypt (`passlib`), never stored in plaintext.
- JWT session (HS256, 7-day expiry, `sub` = user_id).
- ⚠️ `JWT_SECRET_KEY` falls back to a hardcoded
  `"dev-secret-change-me-in-production"` string if unset — **must be
  set explicitly before any real deployment.**
- CORS open in dev only — restrict before prod.

## Cross-service auth (no shared library)
Other agents (e.g. Business) independently re-implement HS256
verification against the same `JWT_SECRET_KEY` env var, rather than
importing a shared package or calling back to this service. Correctly
implemented (constant-time signature comparison, `exp`/`alg`/`sub`
checks) but duplicated — a shared `auth` package would remove the risk
of the implementations drifting apart.

## Data
- Real PostGIS geometry for terrains: frontend-drawn (lat,lng) points
  → WKT `POLYGON` via `ST_GeomFromText`; server-side area fallback
  (spherical-excess formula) if the client doesn't send
  `superficie_ha`.
- `psycopg2` pool with a 5s `connect_timeout` so sign-in fails fast
  instead of hanging when Postgres is down.

## Dev convenience (frontend)
`VITE_SKIP_AUTH=true` in a gitignored `.env.local` injects a fake
"dev-bypass-user" session — mirrors `agent_business`'s
`BUSINESS_AUTH_DISABLED` escape hatch. Both are dev-only; confirm
neither is set in any deployed environment.

## Run locally
```bash
cd backend/auth
pip install -r requirements.txt
docker compose up -d db          # exposes Postgres on host port 5434
uvicorn app.main:app --reload --port 8001
```
