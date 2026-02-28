# CompanionHK Backend

FastAPI orchestration service for CompanionHK.

Current framework notes:

- `/chat` is thread-aware (`thread_id`) for stateful session continuity.
- Runtime is feature-flagged:
  - `FEATURE_LANGGRAPH_ENABLED=false` -> `simple` runtime
  - `FEATURE_LANGGRAPH_ENABLED=true` -> LangGraph-capable runtime path
- Long-term memory strategy is controlled by:
  - `MEMORY_LONG_TERM_STRATEGY` (default: `hybrid_profile_retrieval`)
  - `MEMORY_RETRIEVAL_TOP_K`

## Local Commands

### Option A: `venv` + `pip`

- Install:
  - `python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'`
- Run server:
  - `source .venv/bin/activate && uvicorn app.main:app --reload --port 8000`
- Run tests:
  - `source .venv/bin/activate && pytest -q`

### Option B: `uv`

- Install/sync:
  - `uv sync --all-extras`
- Run server:
  - `uv run uvicorn app.main:app --reload --port 8000`
- Run tests:
  - `uv run pytest -q`

### Option C: `conda`

- Create/update environment:
  - `conda env create -f environment.yml || conda env update -f environment.yml --prune`
- Run server:
  - `conda run -n companionhk-backend uvicorn app.main:app --reload --port 8000`
- Run tests:
  - `conda run -n companionhk-backend pytest -q`
