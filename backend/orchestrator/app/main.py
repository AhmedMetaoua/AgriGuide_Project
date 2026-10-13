from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.journey import router as journey_router

# Repo-root .env (JWT_SECRET_KEY partagé avec Auth/Business, AGENT_*_URL…)
_REPO_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_REPO_ENV)
load_dotenv()  # autorise aussi backend/orchestrator/.env en override local

app = FastAPI(title="AgriAdvisor — Orchestrateur", version="0.1.0")

# Dev only : à restreindre à l'origine réelle du frontend une fois déployé
# (même remarque que sur les autres services du monorepo).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(journey_router)


@app.get("/health")
def health():
    from app.config import (
        AGRICULTURE_URL,
        AUTH_URL,
        BUSINESS_URL,
        MONITORING_URL,
        REGULATION_URL,
        WASTE_URL,
    )

    return {
        "status": "ok",
        "service": "orchestrator",
        "sub_agents": {
            "auth": AUTH_URL,
            "agriculture": AGRICULTURE_URL,
            "business": BUSINESS_URL,
            "monitoring": MONITORING_URL,
            "regulation": REGULATION_URL,
            "waste": WASTE_URL,
        },
    }
