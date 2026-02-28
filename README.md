# CompanionHK (`港伴AI`)

CompanionHK is an AI companion app for Hong Kong users, focused on supportive conversation, safety, and practical local recommendations.

This repository currently contains the foundational framework (Hour 0-4 scope):

- `frontend/`: Next.js (App Router) + TypeScript + MUI
- `backend/`: FastAPI + Pydantic orchestration API
- `infra/`: Local PostgreSQL + Redis development stack

Architecture direction (agreed):

- Keep provider adapters with `MiniMax` preserved as the core model route.
- Support stateful orchestration through a LangGraph-capable runtime boundary (feature-flagged).
- Use hybrid long-term memory: Postgres profile memory + pgvector retrieval memory.

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

- chat shell UI,
- `/health` and mocked `/chat` backend routes,
- adapter-first provider skeletons,
- local Postgres/Redis baseline,
- smoke tests for frontend and backend contracts.
