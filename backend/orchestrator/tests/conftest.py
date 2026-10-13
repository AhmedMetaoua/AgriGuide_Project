"""Rend `import app...` possible quel que soit le dossier d'où pytest est lancé
(racine du dépôt ou backend/orchestrator)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
