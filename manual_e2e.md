# CompanionHK Manual E2E Guide (Local Production Preview)

This guide helps contributors configure, test, and run CompanionHK locally in a production-like way before deploying online.

## Goal

- Validate the full stack locally (frontend + backend + Postgres + Redis).
- Catch configuration issues early (env vars, provider flags, API routing).
- Run both automated tests and manual E2E checks before deployment.

## 1) Prerequisites

- `Node.js` 20+ and `npm`
- `Python` 3.11+
- One Python workflow: `venv` (recommended), `uv`, or `conda`
- `Docker` + `docker compose`

Optional but recommended for richer Local Guide preview:

- `GOOGLE_MAPS_API_KEY` (backend places + routes)
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` (frontend map canvas)

## 2) Configure Environment

From repo root:

```bash
cp .env.example .env
```

Edit `.env` as needed.

Minimum keys for baseline local preview:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- `BACKEND_HOST=0.0.0.0`
- `BACKEND_PORT=8000`
- `FRONTEND_ORIGIN=http://localhost:3000`
- `CHAT_PROVIDER=mock`
- `FEATURE_WEATHER_ENABLED=true`
- `FEATURE_GOOGLE_MAPS_ENABLED=true`

Notes:

- If Google Maps keys are empty, Local Guide still works with degraded fallback recommendations.
- Open-Meteo does not require an API key by default.

## 3) Start Local Infra (Postgres + Redis)

From repo root:

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps
```

Expected: both `companionhk-postgres` and `companionhk-redis` show as running/healthy.

## 4) Install Dependencies

### Backend (choose one)

`venv`:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cd ..
```

`uv`:

```bash
cd backend
uv sync --all-extras
cd ..
```

`conda`:

```bash
cd backend
conda env create -f environment.yml || conda env update -f environment.yml --prune
cd ..
```

### Frontend

```bash
cd frontend
npm install
cd ..
```

## 5) Run Automated Tests (Pre-E2E Gate)

Backend:

- `venv`: `cd backend && source .venv/bin/activate && pytest -q`
- `uv`: `cd backend && uv run pytest -q`
- `conda`: `cd backend && conda run -n companionhk-backend pytest -q`

Frontend:

```bash
cd frontend && npm run test
```

If tests fail, fix them before manual E2E.

## 6) Run App Locally (Production-Like Preview)

Open two terminals.

Terminal A (backend, no reload):

- `venv`: `cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `uv`: `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `conda`: `cd backend && conda run -n companionhk-backend uvicorn app.main:app --host 0.0.0.0 --port 8000`

Terminal B (frontend, production mode):

```bash
cd frontend
npm run build
npm run start
```

Open `http://localhost:3000`.

Quick API smoke checks:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/
```

Expected:

- `/` returns `{"status":"ok"}`
- `/health` returns healthy status payload

## 7) Manual E2E Checklist

Use the UI at `http://localhost:3000`.

### A. Multi-role chat continuity and separation

1. In `Companion`, send: "I feel stressed after work."
2. Switch to `Study Guide`, send: "Help me make a 3-day study plan for calculus."
3. Switch to `Local Guide`, send: "Recommend a quiet cafe in Central."
4. Switch back across tabs.

Expected:

- Each role keeps its own conversation history.
- Messages do not leak between role tabs.

### B. Backend chat contract sanity

Run:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"manual-e2e-user",
    "role":"companion",
    "thread_id":"manual-e2e-thread",
    "message":"hello"
  }'
```

Expected:

- Response includes `request_id`, `thread_id`, and `reply`.

### C. Local Guide recommendations + weather context

1. In `Local Guide`, send a place-oriented request (for example, "Outdoor walk near Tsim Sha Tsui").
2. Confirm "Live Local Guide Context" appears.
3. Verify recommendation cards are shown.

Expected:

- 3-5 recommendations are returned.
- Each recommendation includes rationale text.
- Distance/time hints appear when route data is available.
- Weather context line appears above recommendations.

### D. Degraded fallback behavior (resilience check)

Temporarily set in `.env`:

- `FEATURE_WEATHER_ENABLED=false`
- `FEATURE_GOOGLE_MAPS_ENABLED=false`

Restart backend and repeat Local Guide request.

Expected:

- Chat remains usable.
- Recommendations still render with fallback content.
- No frontend crash.

### E. Optional live Google Maps canvas check

If both keys are set:

- `GOOGLE_MAPS_API_KEY`
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`

Expected:

- Map renders markers for recommended places.
- Recommendation links open the corresponding place in Google Maps.

## 8) Shutdown and Cleanup

Stop app servers with `Ctrl+C`, then:

```bash
docker compose -f infra/docker-compose.yml down
```

To remove local volumes too:

```bash
docker compose -f infra/docker-compose.yml down -v
```

## 9) Definition of Done Before Deploy

- Automated tests pass (`pytest -q`, `npm run test`).
- Manual checklist A-D passes.
- No critical console/backend runtime errors during E2E flow.
- Production-like local run (`npm run build && npm run start`) succeeds.
