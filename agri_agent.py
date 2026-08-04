import os
import json
import requests
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from mistralai.client import Mistral

# --- 1. Define LangGraph State ---
class AgentState(TypedDict):
    scenario_id: str
    farm_data: Optional[Dict[str, Any]]
    weather_data: Optional[Dict[str, Any]]
    error: Optional[str]
    final_output: Optional[Dict[str, Any]]


# --- 2. Node 1: Fetch Farm Context from Mock DB ---
def fetch_farm_node(state: AgentState) -> AgentState:
    scenario_id = state.get("scenario_id", "farm_001")
    db_path = os.path.join(os.path.dirname(__file__), "mock_db.json")
    
    if not os.path.exists(db_path):
        return {**state, "error": f"Database file '{db_path}' not found."}
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            scenarios = data.get("mock_agricultural_database", [])
            
        farm = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
        if not farm:
            return {**state, "error": f"Scenario ID '{scenario_id}' not found in database."}
        
        return {**state, "farm_data": farm, "error": None}
    except Exception as e:
        return {**state, "error": f"Error reading database: {str(e)}"}


# --- 3. Node 2: Fetch Live Weather from Open-Meteo API ---
def fetch_weather_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    farm_data = state["farm_data"]
    lat = farm_data["location"]["latitude"]
    lon = farm_data["location"]["longitude"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max"
        ],
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            daily = res_json.get("daily", {})
            weather_summary = {
                "city": farm_data["location"]["city"],
                "today_max_temp_c": daily.get("temperature_2m_max", [None])[0],
                "today_min_temp_c": daily.get("temperature_2m_min", [None])[0],
                "precipitation_sum_mm": daily.get("precipitation_sum", [None])[0],
                "precipitation_probability_pct": daily.get("precipitation_probability_max", [None])[0],
                "max_wind_speed_kmh": daily.get("wind_speed_10m_max", [None])[0],
                "simulated_condition_tag": farm_data.get("expected_weather_condition_to_simulate")
            }
            return {**state, "weather_data": weather_summary}
        else:
            # Fallback to simulation tag if API rate limited or offline
            return {
                **state,
                "weather_data": {
                    "city": farm_data["location"]["city"],
                    "simulated_condition_tag": farm_data.get("expected_weather_condition_to_simulate"),
                    "note": "Using simulated condition due to weather API fallback."
                }
            }
    except Exception as e:
        return {
            **state,
            "weather_data": {
                "city": farm_data["location"]["city"],
                "simulated_condition_tag": farm_data.get("expected_weather_condition_to_simulate"),
                "note": f"Weather fetch fallback: {str(e)}"
            }
        }


# --- 4. Node 3: Mistral Agent Reasoning ---
def mistral_reasoning_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    farm_data = state["farm_data"]
    weather_data = state["weather_data"]

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return {**state, "error": "MISTRAL_API_KEY environment variable is not set."}

    client = Mistral(api_key=api_key)

    system_prompt = """You are an elite agricultural AI agent. Analyze the provided weather forecast, crop context, and available hardware inventory to output structured daily irrigation, water-saving advice, and emergency alerts.

CRITICAL INSTRUCTION REGARDING WEATHER:
- Look ONLY at the numeric weather values (temperature, precipitation_probability_pct, precipitation_sum_mm). 
- Ignore any historical or descriptive 'simulated_condition_tag' if it contradicts the actual live weather numbers. If precipitation probability is low (e.g., < 20%) and temperature is high, treat it as a dry/hot day, regardless of what any text tag says.

RULES:
1. 'has_alert': Set to true ONLY if there is an imminent threat based on the actual numbers (e.g., extreme high heat or actual high precipitation probability > 70%).
2. 'alert_message': Short warning if has_alert is true, otherwise null.
3. 'daily_advice': 2-3 sentences of precise, actionable advice using ONLY the equipment present in 'hardware_inventory'.
4. 'water_saving_technique': 1-2 sentences explaining a practical water-conservation method using their specific tools/soil type.

OUTPUT FORMAT:
Output ONLY a single valid JSON object with keys: "has_alert", "alert_message", "daily_advice", "water_saving_technique".
Do not wrap in markdown quotes or extra commentary."""
    user_payload = {
        "farmer_name": farm_data["farmer_name"],
        "crop_context": farm_data["crop_context"],
        "hardware_inventory": farm_data["hardware_inventory"],
        "weather_data": weather_data
    }

    try:
        response = client.chat.complete(
            model="mistral-medium-latest",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, indent=2)}
            ]
        )

        content = response.choices[0].message.content
        parsed_json = json.loads(content)

        full_output = {
            "farmer_name": farm_data["farmer_name"],
            "location": farm_data["location"]["city"],
            "crop": farm_data["crop_context"]["crop_name"],
            "weather_summary": weather_data,
            "analysis": parsed_json
        }

        return {**state, "final_output": full_output}
    except Exception as e:
        return {**state, "error": f"Mistral processing failed: {str(e)}"}


# --- 5. Build and Compile the LangGraph Workflow ---
def build_agri_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("fetch_farm", fetch_farm_node)
    workflow.add_node("fetch_weather", fetch_weather_node)
    workflow.add_node("mistral_reasoning", mistral_reasoning_node)

    workflow.add_edge(START, "fetch_farm")
    workflow.add_edge("fetch_farm", "fetch_weather")
    workflow.add_edge("fetch_weather", "mistral_reasoning")
    workflow.add_edge("mistral_reasoning", END)

    return workflow.compile()


# Export compiled agent
agri_agent_app = build_agri_graph()