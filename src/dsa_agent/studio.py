from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from .graph_workflow import DsaTutorGraph
from .orchestrator import DsaLearningAgent


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

_tutor_graph = DsaTutorGraph(DsaLearningAgent(enable_execution=True))
graph = _tutor_graph._compiled_graph

if graph is None:
    raise RuntimeError("LangGraph is not installed, so Studio cannot load the compiled graph.")
