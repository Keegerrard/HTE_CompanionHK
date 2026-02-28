# Google Maps Integration Contract

This document defines CompanionHK usage of Google Maps APIs for local search, ranking, and map presentation.

## Purpose

- Search local places from user intent in `local_guide`.
- Rank recommendations with distance/travel-time and review quality.
- Provide map-ready location data and optional place photo URLs.

## Security and Key Policy

- Backend server uses `GOOGLE_MAPS_API_KEY` for web service calls.
- Frontend map canvas uses `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` for Maps JavaScript SDK.
- Restrict keys by API and origin/IP:
  - Backend key: server IP restriction + only required web service APIs.
  - Frontend key: HTTP referrer restriction + Maps JavaScript API only.

## Upstream APIs Used

Server-side web services:

- Place Text Search:
  - `GET https://maps.googleapis.com/maps/api/place/textsearch/json`
  - Purpose: query-driven place discovery near user location.
- Directions:
  - `GET https://maps.googleapis.com/maps/api/directions/json`
  - Purpose: distance and duration hints for each recommended place.

Client-side map rendering:

- Maps JavaScript API
  - Purpose: interactive map canvas and markers.

Optional field support:

- Photo URLs are generated from `photo_reference`:
  - `https://maps.googleapis.com/maps/api/place/photo?maxwidth=<n>&photo_reference=<ref>&key=<api_key>`

## Internal Backend API Contract

Frontend requests recommendations from CompanionHK backend only.

- Endpoint: `POST /recommendations`
- Key request fields:
  - `user_id` (required)
  - `role` (must be `local_guide` for map recommendation UX)
  - `query` (required)
  - `latitude`, `longitude` (required)
  - `max_results` (clamped to `3..5`)
  - `preference_tags` (optional list)

## Response Fields Used by Frontend

For each recommendation:

- `place_id`
- `name`
- `address`
- `rating`
- `user_ratings_total`
- `types`
- `location.latitude`
- `location.longitude`
- `photo_url` (optional)
- `maps_uri` (Google Maps deep link)
- `distance_text` / `duration_text` (optional)
- `fit_score` (0..1)
- `rationale` (why it fits current context)

Context fields:

- `context.weather_condition`
- `context.temperature_c`
- `context.degraded`
- `context.fallback_reason`

## Ranking Rules (MVP)

Weighted score is deterministic and explainable:

- Query relevance
- Rating and review volume
- Distance/time convenience
- Weather fit (indoor/outdoor adjustment)
- Preference tag fit

Recommendation output rules:

- Return 3 to 5 entries.
- Include rationale on every entry.
- Include travel distance/time when route data is available.

## Reliability and Fallback Rules

- If Maps API fails, return `degraded=true` with fallback reason.
- If route lookup fails for a place, keep the place and omit route fields.
- If initial query is sparse, use safe fallback discovery queries to reach 3 results.
- Do not block core chat on recommendation failures.

## Usage Guardrails

- Frontend must not call Place Text Search or Directions directly.
- Keep provider responses normalized before returning to frontend.
- Avoid exposing raw provider payloads in public API contracts.
- Log provider status and fallback reasons for demo/debug visibility.
