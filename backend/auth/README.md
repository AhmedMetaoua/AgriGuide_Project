# Auth

**Status: ✅ Fully real — the platform's foundational, best-tested service.**

## Role
Sign-up/sign-in and farmer profile management (equipment + declared
terrains). Every other agent depends on the JWT this service issues and, in
turn, on the `users` / `terrains` rows it owns.

## Roles
- **farmer** — full access (advisors + marketplace write). Declares owned
  equipment at sign-up; terrains can be sent at sign-up or added afterwards
  (`POST /auth/me/terrains`) — the web app does the latter, from the
  Agriculture page.
- **acheteur** (buyer) — marketplace read-only, no advisor access.

## Endpoints
| Method | Route | Description |
|---|---|---|
| `POST` | `/auth/signup` | `{email, password, nom, telephone?, role, equipements?, terrains?}` → creates the account (+ equipment and any terrains sent, if `role=farmer`) and returns a token. |
| `POST` | `/auth/signin` | Token + profile. |
| `GET` | `/auth/me` | Full profile (`Authorization: Bearer <token>`). |
| `PUT` | `/auth/me/equipements` | Replace declared equipment (farmer only). |
| `POST` | `/auth/me/terrains` | Add a terrain (farmer only). |
| `PUT` / `DELETE` | `/auth/me/terrains/{id}` | Update / remove a terrain (farmer only). |
| `GET` | `/health` | Health check. |

## Security
- Passwords hashed with bcrypt (`passlib`), never stored in plaintext.
- JWT session: HS256, 7-day expiry, `sub` = user id.
- ⚠️ `JWT_SECRET_KEY` falls back to a hardcoded dev string if unset — **set it
  explicitly before any real deployment.**
- CORS is open in development only — restrict before production.

## How other services verify tokens
Auth issues the token; the other agents verify it against the same
`JWT_SECRET_KEY` without calling back to Auth. Business, Agriculture and the
Orchestrator share one decoding implementation through
[`agriment_shared`](../shared/README.md), each keeping its own access policy.

## Data
- Terrains use real PostGIS geometry: frontend-drawn `(lat, lng)` points →
  WKT `POLYGON` via `ST_GeomFromText`, with a server-side spherical-excess area
  fallback if the client doesn't send `superficie_ha`.
- `psycopg2` connection pool with a 5 s `connect_timeout`, so sign-in fails
  fast instead of hanging when Postgres is down.

## Dev convenience (frontend)
`VITE_SKIP_AUTH=true` injects a fake dev session so the UI can be explored
without Auth or Postgres. It mirrors Business's `BUSINESS_AUTH_DISABLED`
switch. Both are **dev-only** — confirm neither is set in a deployed
environment.

## Run locally
```bash
cd backend/auth
pip install -r requirements.txt
docker compose up -d db          # Postgres on host port 5434
uvicorn app.main:app --reload --port 8001
```

## Tests
The suite is a sequential end-to-end script (sign-up → sign-in → profile →
terrain CRUD), **not** a pytest suite — later steps reuse the account created
by earlier ones — and it needs a real Postgres with `database/schema.sql`
applied:
```bash
docker compose up -d db
cd backend/auth
python -m app.tests.test_endpoints
```
