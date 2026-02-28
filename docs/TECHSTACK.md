# CompanionHK Final Tech Stack

This document locks the implementation stack for the 24-hour hackathon MVP.

## 1) Final Stack (Single Source of Truth)

- Frontend: `Next.js (App Router)` + `TypeScript` + `MUI`
- Backend API: `Python` + `FastAPI`
- Primary database: `PostgreSQL`
- Fast cache/session context: `Redis`
- Vector memory: `pgvector` in PostgreSQL
- Model orchestration: provider adapter layer with `MiniMax` path
- Voice providers: `ElevenLabs` and `Cantonese.ai`
- Local recommendation data: `Google Maps API` + weather source + user context
- Infra target: AWS-first deployment
- Observability: `CloudWatch` baseline (+ optional `Sentry`)

## 2) Layered Architecture

## Frontend Layer

- Stack: `Next.js + TypeScript + MUI`
- Responsibilities:
  - chat UI and memory-aware conversation screens,
  - weather/emotion adaptive theming,
  - recommendation cards,
  - voice controls and playback UI,
  - safety banner and crisis resources.

## API and Orchestration Layer

- Stack: `FastAPI` + `Pydantic`
- Responsibilities:
  - prompt orchestration and provider routing,
  - safety policy enforcement,
  - memory read/write policy,
  - recommendation aggregation (maps/weather/mood/preferences),
  - provider fallback handling.

## Data and Memory Layer

- `PostgreSQL`:
  - users, profiles, preferences, long-term memory records, audit metadata.
- `pgvector`:
  - embedding storage and semantic retrieval for long-term memory.
- `Redis`:
  - short-term context windows with TTL,
  - temporary state,
  - rate-limit counters.

## AI and Safety Layer

- Primary conversation route:
  - provider-agnostic adapter with `MiniMax` integrated for sponsor value.
- Safety/emotion route:
  - smaller model/process for risk scoring and emotion tagging.
- Safety policy:
  - hard refuse dangerous requests,
  - preserve supportive tone,
  - trigger escalation UX.

## Voice Layer

- `ElevenLabs`: high-quality TTS path.
- `Cantonese.ai`: Cantonese voice route (ASR/TTS where applicable).
- Adapter-based fallback between voice providers.

## Recommendation Layer

- `Google Maps API`: places and routing data.
- Weather source: `Open-Meteo` default.
- Context inputs: emotion state + user preferences + location/weather.
- Optional freshness boost: `Exa` retrieval.

## Infrastructure Layer (AWS-First)

- Frontend hosting: `AWS Amplify`
- Backend runtime: `AWS ECS Fargate`
- Database: `AWS RDS PostgreSQL`
- Cache: `AWS ElastiCache Redis`
- Secrets/config: environment variables + AWS secret tooling as needed

## Observability Layer

- Baseline:
  - structured logs to `CloudWatch`,
  - request/error metrics.
- Optional:
  - `Sentry` for frontend/backend exception tracking.

## 3) Why This Fits a 24h Hackathon

- Fastest stable path with mature frameworks and libraries.
- Clear separation of concerns by layer and provider adapters.
- Minimal migration risk: `PostgreSQL + pgvector + Redis` covers MVP and near-term scale.
- Sponsor alignment can be demonstrated without overcomplicated architecture.

## 4) Sponsor Coverage Map

- `AWS`: hosting, compute, database, cache.
- `MiniMax`: primary/fallback LLM route and/or safety/emotion path.
- `ElevenLabs`: voice output.
- `Cantonese.ai`: Cantonese voice path.
- `Exa`: optional retrieval enrichment for fresh local content.

## 5) Must-Have vs Optional (Time Management)

Must-have for demo:

- End-to-end supportive chat.
- Safety monitoring + refusal + crisis banner.
- Short-term memory (`Redis`) + basic long-term memory (`PostgreSQL`).
- Recommendation endpoint using mood/weather/preferences + Google Maps.
- At least one working voice route.

Optional if ahead of schedule:

- Full dual-provider voice failover.
- Deep vector recall tuning.
- Exa-enhanced recommendation enrichment.
- Advanced observability dashboards and tracing.

## 6) Implementation Rules

- Keep all external services behind provider adapters.
- Prefer feature flags over branching logic in UI.
- Degrade gracefully when any provider is unavailable.
- Never block core supportive chat on non-critical integrations.
