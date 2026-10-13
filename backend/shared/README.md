# Shared (`agriment_shared`)

**Status: ✅ Small, tested, in use.**

Code shared by several agents, packaged as a local installable Python package.

## What's in it
- **JWT decoding** (`agriment_shared/auth.py`) — HS256 verification of the
  tokens issued by Auth, including signature, `exp`, `alg` and `sub` checks.
  This replaces three duplicated copies that previously lived in Business,
  Agriculture and the Orchestrator.

The package shares the **mechanism**, not the **policy**. Each service keeps
its own access rules around it:

| Service | Policy |
|---|---|
| Business | Required token; dev-only bypass via `BUSINESS_AUTH_DISABLED` |
| Agriculture | Optional token (anonymous analysis allowed); an invalid token is still a 401 |
| Orchestrator | Required token, no bypass |

Auth itself is the token *issuer* and keeps its own encode/decode in
`auth/app/security.py`.

## Not built yet
- Shared Pydantic models matching `database/schema.sql`
- A shared client for external APIs used by more than one agent (e.g.
  FranceAgriMer prices, used by Business and planned for Marketplace)
- A common DB connection pool

## Usage
**Local** — the root `requirements.txt` contains `-e ./backend/shared`, so
`import agriment_shared` works in every service of the shared venv.

**Docker** — services that depend on it build with the repo root as context:
```dockerfile
COPY backend/shared /shared
RUN pip install --no-cache-dir /shared
```
```yaml
# docker-compose.yml
build:
  context: .
  dockerfile: backend/<service>/Dockerfile
```

## Tests
```bash
cd backend/shared && python -m pytest -q
```
