# CompanionHK Hackathon Agent Guide

This file defines how humans and AI agents should build `CompanionHK` (also called `港伴AI`) during the hackathon.

## 1) Mission and Product North Star

- Build an AI friend for Hong Kong users that is supportive, safe, and useful in daily life.
- Deliver emotional companionship plus local guidance in natural, localized wording.
- Optimize for a strong live demo: warm interaction, practical recommendations, and visible safety design.

## 2) Hackathon Rules (Non-Negotiable)

- Work in small steps; each step should be demoable and reversible.
- Ship an MVP first, then add stretch features behind flags.
- Prefer reliable, boring architecture over complex systems.
- Keep all external integrations behind provider adapters so they can be swapped quickly.
- Pre-wire extension points for extra APIs even if not fully used yet.
- Log key events for debugging and demo storytelling.

## 3) Sponsor Leverage Strategy (Extra Prize Focus)

Use each sponsor in at least one meaningful flow:

- `AWS`: deploy app/services and core data infra.
  - Target: `AWS Amplify` (web), `Lambda + API Gateway` or `ECS` (Python API), `RDS Postgres`, `ElastiCache Redis`.
- `MiniMax`: add a model route for either primary chat fallback or emotion/safety support classification.
- `ElevenLabs`: text-to-speech and/or voice style for emotionally supportive responses.
- `Cantonese.ai`: Cantonese ASR/TTS path for local voice conversation.
- `Exa`: retrieval for fresh local context (events, neighborhood info, trending places).

Implementation rule:

- Every provider gets an adapter interface and feature flag from day 1.
- Default folder pattern:
  - `providers/aws/`
  - `providers/minimax/`
  - `providers/elevenlabs/`
  - `providers/cantoneseai/`
  - `providers/exa/`

## 4) Core MVP Capabilities

Must-have:

- Private free-form conversation with the AI friend.
- Supportive conversation behavior (empathetic, encouraging, non-judgmental).
- Short-term memory from recent chat context.
- Long-term memory for user preferences and recurring facts.
- Local recommendations using:
  - current weather,
  - detected user emotion,
  - user preferences,
  - `Google Maps API` place and routing data.
- Voice conversation mode (at least one working pipeline from provider to playback).

Nice-to-have (after MVP):

- Multi-provider voice fallback (`ElevenLabs` <-> `Cantonese.ai`).
- Rich preference personalization controls.

## 5) Safety and Mental Health Alignment

Safety is a product requirement, not a stretch goal.

- Show an anti-suicide help banner in high-risk contexts with hotline resources.
- Maintain a crisis resource list in-app (verify numbers before release/demo).
- Reject dangerous self-harm or harmful instructions with a calm, supportive refusal.
- Continue compassionate support and encourage contact with professionals.
- Never provide procedural harm guidance, even when asked indirectly.

Recommended Hong Kong emergency/support entries (must be verified before demo):

- `The Samaritans Hong Kong`: `2896 0000`
- `Suicide Prevention Services`: `2382 0000`
- `The Samaritan Befrienders Hong Kong`: `2389 2222`
- `Emergency Services`: `999`

Risk monitoring rule:

- Run a smaller model/process continuously for emotion and safety-risk scoring.
- Use this signal to:
  - adapt UI tone/theme,
  - add safety context to primary model prompts,
  - trigger banner/escalation behavior.

## 6) UI/UX Direction

- Visual style: lovely, warm, calm, and trustworthy.
- Theme adapts to weather and current emotion state.
- Keep language local and supportive; avoid robotic tone.
- Use a mature UI kit for speed and consistency.

## 7) Finalized UI Kit Decision

- Primary UI kit (locked): `MUI`.
- Why `MUI`:
  - fastest path to a polished MVP in 24 hours,
  - complete component coverage for chat, forms, cards, alerts, and dialogs,
  - mature Next.js App Router integration,
  - robust runtime theming for weather + emotion adaptation.
- Fallback UI kit: `Chakra UI` if a hard blocker appears.
- Deferred for this sprint: `shadcn/ui` (can be evaluated after MVP).

## 8) Finalized Tech Stack (Locked for This Sprint)

- Frontend: `Next.js (App Router)` + `TypeScript` + `MUI`.
- Backend API/orchestration: `Python` + `FastAPI` (+ `Pydantic` models).
- Data and memory:
  - `PostgreSQL` as source of truth,
  - `pgvector` in Postgres for semantic memory,
  - `Redis` for short-term context windows, caching, and rate limiting.
- AI/model routing:
  - primary conversational route with provider adapters (include `MiniMax` path for sponsor value),
  - smaller safety/emotion model route for risk scoring and UI/prompt context.
- Voice:
  - `ElevenLabs` for high-quality TTS path,
  - `Cantonese.ai` for Cantonese voice route,
  - adapter-based fallback between providers.
- Recommendations:
  - `Google Maps API` for places + routing,
  - weather source (`Open-Meteo` by default),
  - optional `Exa` retrieval boost for fresh local context.
- AWS-first deploy target:
  - frontend: `AWS Amplify`,
  - backend: `ECS Fargate`,
  - database: `RDS PostgreSQL`,
  - cache: `ElastiCache Redis`.
- Observability:
  - `CloudWatch` logs/metrics baseline,
  - optional `Sentry` for runtime error tracking.

Reference docs:

- `docs/TECHSTACK.md` for detailed architecture and component responsibilities.
- `docs/ROADMAP-24H.md` for owner-based execution timeline.

## 9) Memory Design Rules

- Short-term memory:
  - keep rolling conversation context in Redis with TTL.
  - summarize older turns when token budget is tight.
- Long-term memory:
  - store durable user profile/preferences in Postgres.
  - store semantic memory embeddings in Postgres (`pgvector`).
- Memory writes must be explicit and auditable; do not silently store sensitive raw content beyond what is needed.

## 10) Recommendation Engine Rules

Recommendation generation should combine:

- user emotion state,
- weather conditions,
- user preferences/history,
- map/place data from `Google Maps API`.

Output format requirement:

- return 3-5 recommendations,
- each with "why this fits your current mood and context",
- include travel distance/time hint when available.

## 11) Family Mode (Extension After MVP)

Build after core MVP is stable:

- Create a `Family Mode` bridge for intergenerational communication.
- Generate short, respectful summaries/share cards users can send to family members.
- Keep privacy controls strict (user consent before sharing any content).

## 12) Delivery Workflow for This Hackathon

Iteration loop:

1. Define one thin slice (1-3 hours).
2. Build only what is needed for that slice.
3. Test quickly (happy path + one failure path).
4. Demo internally.
5. Capture learnings and plan next slice.

Definition of done for each slice:

- Feature works end-to-end in local demo.
- Basic error handling exists.
- Safety behavior is preserved.
- Logs are sufficient to debug live issues.
- Feature can be toggled or rolled back quickly.

## 13) 24-Hour Roadmap Summary

- Hour 0-4: foundation and scaffolding.
- Hour 4-8: chat flow and safety baseline.
- Hour 8-12: short-term + long-term memory.
- Hour 12-16: recommendations (weather + mood + maps).
- Hour 16-20: voice pipeline.
- Hour 20-24: polish, deployment, and demo hardening.

Detailed, owner-based plan: `docs/ROADMAP-24H.md`.

## 14) Agent Execution Rules

- Do not attempt big-bang implementation.
- Keep PRs/changesets small and focused.
- Add stubs/interfaces for future provider integrations early.
- If a provider API fails, degrade gracefully and keep core chat usable.
- Protect user trust: supportive tone, privacy-aware handling, safety-first behavior.

## 15) MVP Priority Order

1. Core supportive chat experience
2. Safety layer and crisis escalation UX
3. Memory (short-term then long-term)
4. Local recommendations with weather + mood + preferences
5. Voice interaction
6. Sponsor deep integrations and Family Mode enhancements
