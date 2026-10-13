# Waste API

Exposes `knowledge/canonical_knowledge.json` (53 crops, 321 waste entries) to
the React app (Agriculture → Business → Marketplace). **No LLM keys required**
for these endpoints.

## Run
```bash
cd backend/waste_agents
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8004
```
Health: `GET http://localhost:8004/health`

## Endpoints
| Method | Path | Role |
|---|---|---|
| `POST` | `/waste/for-crops` | Body `{"cultures": ["ble_tendre", "mais", ...]}` → waste profiles for the top agricultural crops |
| `GET` | `/waste/marketplace-suggestions?culture=mais` | Wastes worth listing on the marketplace after harvest |
| `POST` | `/waste/reload` | Clear the in-memory cache after editing the JSON |

## Frontend
`VITE_AGENT_WASTE_URL=http://localhost:8004` (optional — this is the default).

Live research and enrichment of the knowledge base is done through the
Streamlit tool (`streamlit run ui/streamlit_app.py`); see the
[module README](../README.md).
