import sys
import types
from pathlib import Path

# Make backend/ importable as the project root (mirrors running uvicorn from backend/).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Stub out modules that load models, open DB connections or call external APIs
# at import time, so the pipeline logic can be tested offline.
_vector = types.ModuleType("services.vector_service")
_vector.search_chunks = lambda *a, **k: []
sys.modules.setdefault("services.vector_service", _vector)

_llm = types.ModuleType("llm")
_llm.ask = lambda system_prompt, user_prompt: ""
sys.modules.setdefault("llm", _llm)

_tavily = types.ModuleType("tavily")
_tavily.TavilyClient = lambda api_key=None: None
sys.modules.setdefault("tavily", _tavily)
