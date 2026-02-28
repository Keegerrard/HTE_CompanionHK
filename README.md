# CompanionHK (`港伴AI`)

CompanionHK is an AI companion app for Hong Kong users with three role spaces: `Companion`, `Local Guide`, and `Study Guide`, focused on safety and practical daily support.

This repository currently contains the foundational framework (Hour 0-4 scope):

- `frontend/`: Next.js (App Router) + TypeScript + MUI
- `backend/`: FastAPI + Pydantic orchestration API
- `infra/`: Local PostgreSQL + Redis development stack

Architecture direction (agreed):

- Keep provider adapters with `MiniMax` preserved as the core model route.
- Support stateful orchestration through a LangGraph-capable runtime boundary (feature-flagged).
- Use hybrid long-term memory: Postgres profile memory + pgvector retrieval memory.
- Use one chat model route with role-specific prompts and role-scoped thread spaces.

## Quick Start

1. Copy environment template:
   - `cp .env.example .env`
2. Start local infra:
   - `docker compose -f infra/docker-compose.yml up -d`
3. Run backend (choose one):
   - `venv`: `cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]' && uvicorn app.main:app --reload --port 8000`
   - `uv`: `cd backend && uv sync --all-extras && uv run uvicorn app.main:app --reload --port 8000`
   - `conda`: `cd backend && conda env create -f environment.yml || conda env update -f environment.yml --prune && conda run -n companionhk-backend uvicorn app.main:app --reload --port 8000`
4. Run frontend:
   - `cd frontend && npm install && npm run dev`

## Development Commands

- Backend tests:
  - `venv`: `cd backend && source .venv/bin/activate && pytest -q`
  - `uv`: `cd backend && uv run pytest -q`
  - `conda`: `cd backend && conda run -n companionhk-backend pytest -q`
- Frontend tests:
  - `cd frontend && npm run test`

## Current Scope

The foundation slice includes:

- multi-role chat shell UI (Companion / Local Guide / Study Guide),
- `/health` and mocked `/chat` backend routes with `role` + `thread_id` contract,
- adapter-first provider skeletons,
- local Postgres/Redis baseline,
- smoke tests for frontend and backend contracts.

## Integration Contracts

- Weather API usage: `docs/integrations/open-meteo.md`
- Google Maps API usage: `docs/integrations/google-maps.md`
- Recommendation and weather app contract: `docs/architecture/recommendation-contract.md`
