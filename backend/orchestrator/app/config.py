"""
Configuration de l'orchestrateur : URLs des sous-agents.

Chaque URL est surchargeable via variable d'env pour coller au réseau Docker
Compose (`http://agent_business:8000`) ou à un lancement local hors Docker
(`http://localhost:8006`, cf. backend/agent_business/README.md).
"""
import os

AGRICULTURE_URL: str = os.getenv("AGENT_AGRICULTURE_URL", "http://localhost:8002")
BUSINESS_URL: str = os.getenv("AGENT_BUSINESS_URL", "http://localhost:8006")
MONITORING_URL: str = os.getenv("AGENT_MONITORING_URL", "http://localhost:8003")
REGULATION_URL: str = os.getenv("AGENT_REGULATION_URL", "http://localhost:8005")
WASTE_URL: str = os.getenv("AGENT_WASTE_URL", "http://localhost:8004")
AUTH_URL: str = os.getenv("AGENT_AUTH_URL", "http://localhost:8001")

# Timeout par appel sous-agent. L'analyse Agriculture (satellite + sol + DL)
# est la plus lente du pipeline — cf. son propre README sur les temps de
# réponse de /analyze.
SUB_AGENT_TIMEOUT_S: float = float(os.getenv("ORCHESTRATOR_SUB_AGENT_TIMEOUT_S", "45"))
