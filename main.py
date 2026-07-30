import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph import app as agent_app

app = FastAPI(title="AI Agricultural Business Advisor")

# Define the expected JSON payload format
class AdvisorRequest(BaseModel):
    region: str
    season: str
    soil_suggestions: list[str]

@app.post("/advise")
async def get_advice(request: AdvisorRequest):
    if not os.getenv("MISTRAL_API_KEY"):
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY environment variable is not set.")

    state_input = {
        "messages": [HumanMessage(content="Analyze the market data and finalize the top 3 crops.")],
        "region": request.region,
        "season": request.season,
        "suggested_crops": request.soil_suggestions
    }

    try:
        # Invoke the LangGraph agent
        final_state = agent_app.invoke(state_input)
        
        # Extract the final text response from the model
        final_message = final_state["messages"][-1].content
        return {"recommendation": final_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper endpoint to test using the local JSON file directly
@app.post("/advise/test-local")
async def advise_from_file():
    try:
        with open("suggested_crops.json", "r") as f:
            data = json.load(f)
        
        # Map the JSON keys to our Pydantic model
        req = AdvisorRequest(
            region=data["region"],
            season=data["season"],
            soil_suggestions=data["soil_suggestions"]
        )
        return await get_advice(req)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="suggested_crops.json not found")