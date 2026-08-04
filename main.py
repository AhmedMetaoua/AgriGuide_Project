import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

from agri_agent import agri_agent_app

app = FastAPI(
    title="Agricultural Weather Intelligence API",
    description="LangGraph + Mistral AI backend for crop advice and weather alerts.",
    version="1.0.0"
)

# Enable CORS for React/Web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    scenario_id: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Agri-Bot AI Engine",
        "supported_scenarios": 15
    }


@app.get("/api/scenarios")
def get_all_scenarios():
    """Returns all available farm scenarios from the database for the UI dropdown."""
    db_path = os.path.join(os.path.dirname(__file__), "mock_db.json")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="mock_db.json not found")
    
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        scenarios = data.get("mock_agricultural_database", [])
    
    # Return compact list for UI selection
    return [
        {
            "scenario_id": s["scenario_id"],
            "farmer_name": s["farmer_name"],
            "city": s["location"]["city"],
            "crop": s["crop_context"]["crop_name"],
            "growth_stage": s["crop_context"]["growth_stage"],
            "simulated_condition": s["expected_weather_condition_to_simulate"]
        }
        for s in scenarios
    ]


@app.post("/api/analyze")
def analyze_farm_scenario(request: AnalyzeRequest):
    """Executes the LangGraph agent for a given scenario_id."""
    
    # We now strictly rely on the .env file for the API key
    if not os.getenv("MISTRAL_API_KEY"):
        raise HTTPException(
            status_code=500, # Changed to 500 (Server Error) since it's a backend config issue now
            detail="MISTRAL_API_KEY is missing. Please set it in the .env file."
        )

    initial_state = {
        "scenario_id": request.scenario_id,
        "farm_data": None,
        "weather_data": None,
        "error": None,
        "final_output": None
    }

    # Execute LangGraph state machine
    result = agri_agent_app.invoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return result["final_output"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)