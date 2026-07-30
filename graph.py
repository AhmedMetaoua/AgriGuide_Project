import datetime
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mistralai.chat_models import ChatMistralAI
from tools import analyze_price_trends

# 1. Définition de l'état de l'agent
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    region: str
    season: str
    suggested_crops: list[str]

# 2. Initialisation du modèle Mistral et des outils
llm = ChatMistralAI(model="mistral-medium-latest", temperature=0.2)
tools = [analyze_price_trends]
llm_with_tools = llm.bind_tools(tools)

# 3. Nœud de raisonnement
def reasoning_node(state: AgentState):
    # Fetch the current year dynamically
    current_year = datetime.date.today().year
    
    sys_msg = (
        f"Vous êtes un conseiller expert en stratégie et économie agricole en France pour l'année {current_year}. "
        f"Région : {state['region']} | Saison : {state['season']}. "
        f"L'équipe agronomique a recommandé ces 5 cultures adaptées au sol : {', '.join(state['suggested_crops'])}. "
        "Vos consignes :\n"
        "1. Utilisez l'outil analyze_price_trends pour analyser les prix historiques de ces cultures.\n"
        "2. Évaluez la rentabilité, la stabilité des prix et les tendances du marché.\n"
        "3. Sélectionnez les 3 MEILLEURES cultures à planter pour la saison.\n"
        "4. Rédigez un rapport d'analyse stratégique complet en FRANÇAIS expliquant votre décision."
    )
    
    messages = [{"role": "system", "content": sys_msg}] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 4. Compilation du graphe
workflow = StateGraph(AgentState)
workflow.add_node("agent", reasoning_node)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

app = workflow.compile()