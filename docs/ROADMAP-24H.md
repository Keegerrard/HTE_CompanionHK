# CompanionHK 24-Hour Roadmap

This roadmap is optimized for a 3-4 person hackathon team.

## 1) Team Roles

- Frontend Lead:
  - Next.js + MUI app shell,
  - chat UI, safety banner UI, recommendation cards,
  - dynamic weather/emotion theme behavior.
- Backend Lead:
  - FastAPI endpoints, orchestration, memory APIs,
  - safety policy gate and provider adapters.
- Integration Lead:
  - MiniMax route, Google Maps, weather, voice providers,
  - emotion/risk monitor and recommendation ranking logic.
- Optional DevOps Lead (if 4th person available):
  - AWS deployment path, env setup, logs/metrics wiring.

## 2) Critical Path

```mermaid
flowchart LR
    foundation[Foundation0to4] --> chatSafety[ChatAndSafety4to8]
    chatSafety --> memory[Memory8to12]
    memory --> recommendations[Recommendations12to16]
    recommendations --> voice[Voice16to20]
    voice --> polishDeploy[PolishDeploy20to24]
```

Core dependency rule:

- Do not start advanced recommendations or voice before chat + safety baseline is stable.

## 3) Time-Blocked Execution Plan

## Hour 0-4: Foundation and Scaffolding

- Frontend Lead:
  - initialize Next.js App Router + TypeScript + MUI,
  - build chat shell (message list, composer, loading/error states),
  - add theme context skeleton.
- Backend Lead:
  - scaffold FastAPI service and health route,
  - define provider adapter interfaces,
  - add `/chat` endpoint with mocked response.
- Integration Lead:
  - configure Google Maps + weather API stubs,
  - configure MiniMax adapter skeleton,
  - set up voice adapter contracts.
- DevOps Lead:
  - provision local dev stack for Postgres + Redis,
  - define environment variable template.

Deliverable:

- Chat UI can call backend and receive a mocked supportive response.

## Hour 4-8: Chat and Safety Baseline

- Frontend Lead:
  - connect real chat endpoint,
  - implement anti-suicide banner and crisis resources panel.
- Backend Lead:
  - add supportive system prompt and refusal policy layer,
  - implement safety decision API.
- Integration Lead:
  - wire MiniMax model route,
  - implement emotion/risk scoring path (small model/process),
  - pass safety context to primary chat route.

Deliverable:

- End-to-end supportive chat with dangerous-input refusal and visible safety banner.

## Hour 8-12: Memory Layer

- Frontend Lead:
  - preference capture UI (tone, topics, locale hints).
- Backend Lead:
  - implement short-term memory in Redis with TTL,
  - implement long-term memory schema in Postgres.
- Integration Lead:
  - add embeddings + pgvector retrieval path,
  - add memory summarization for long sessions.

Deliverable:

- Chat behavior reflects recent conversation and saved preferences.

## Hour 12-16: Recommendation Engine

- Frontend Lead:
  - build recommendation cards and reasoning text UI,
  - show weather/emotion context in UI.
- Backend Lead:
  - add recommendation orchestration endpoint.
- Integration Lead:
  - integrate Google Maps Places + routing signals,
  - integrate weather source and preference scoring,
  - add optional Exa freshness enrichment.

Deliverable:

- Returns 3-5 localized recommendations with mood/context rationale.

## Hour 16-20: Voice Pipeline

- Frontend Lead:
  - build voice input/output controls and playback.
- Backend Lead:
  - add voice request/response endpoints.
- Integration Lead:
  - wire ElevenLabs path,
  - wire Cantonese.ai path,
  - implement provider fallback behavior.

Deliverable:

- At least one reliable voice conversation path works in demo.

## Hour 20-24: Polish, Deploy, and Demo Hardening

- Frontend Lead:
  - warm visual polish, responsive checks, final theme tuning.
- Backend Lead:
  - stabilize error handling and logs.
- Integration Lead:
  - verify sponsor usage paths and fallback behavior.
- DevOps Lead:
  - deploy frontend/backend/data stack on AWS target path,
  - run smoke test in deployed environment.

Deliverable:

- Demo-ready build with scripted happy path and safety path.

## 4) Risk-Cut Strategy (If Behind Schedule)

Cut order while preserving core value:

1. Defer advanced animations and non-critical UI polish.
2. Limit voice to one provider path first.
3. Disable Exa enrichment and keep Google Maps + weather only.
4. Defer semantic vector tuning; keep basic long-term memory writes.
5. Keep Family Mode as post-MVP stretch only.

Never cut:

- Supportive chat baseline.
- Safety refusal + crisis escalation UX.
- Basic memory context.

## 5) Daily Checkpoints

- Checkpoint A (Hour 4): chat shell + mock backend done.
- Checkpoint B (Hour 8): safety behavior working.
- Checkpoint C (Hour 12): memory persistence working.
- Checkpoint D (Hour 16): recommendations working.
- Checkpoint E (Hour 20): voice baseline working.
- Checkpoint F (Hour 24): deployment + demo script finalized.

## 6) Demo Readiness Checklist

- User can chat privately with supportive AI friend.
- Dangerous prompts trigger refusal and support banner.
- AI remembers recent context and user preferences.
- Recommendations are localized and context-aware.
- Voice flow works on at least one provider.
- Sponsor integrations are demonstrable in the walkthrough.
