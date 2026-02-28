# Open-Meteo Integration Contract

This document defines the exact Open-Meteo usage for CompanionHK weather-driven theming and recommendation context.

## Purpose

- Provide current weather context for UI theme adaptation.
- Provide weather context to recommendation ranking/rationale.
- Keep weather provider swappable through backend adapters.

## Upstream API

- Provider: Open-Meteo
- Base URL (configurable): `https://api.open-meteo.com`
- Endpoint used: `GET /v1/forecast`

## Required Upstream Query Parameters

- `latitude` (float, required)
- `longitude` (float, required)
- `current=temperature_2m,weather_code,is_day` (required)
- `timezone` (optional; default `auto`)

Example upstream request:

`GET https://api.open-meteo.com/v1/forecast?latitude=22.3193&longitude=114.1694&current=temperature_2m,weather_code,is_day&timezone=auto`

## Internal Backend API Contract

The frontend calls CompanionHK backend instead of Open-Meteo directly.

- Endpoint: `GET /weather`
- Query:
  - `latitude` (required)
  - `longitude` (required)
  - `timezone` (optional, default `auto`)

Example:

`GET /weather?latitude=22.3193&longitude=114.1694&timezone=auto`

## Response Fields Consumed by App

- `weather.temperature_c` (number | null)
- `weather.weather_code` (number | null)
- `weather.is_day` (boolean | null)
- `weather.condition` (normalized string)
- `weather.source` (`open-meteo` or `stub`)

Normalized `condition` values:

- `clear`
- `partly_cloudy`
- `cloudy`
- `fog`
- `drizzle`
- `rain`
- `snow`
- `thunderstorm`
- `unknown`

## Weather Code Mapping (Open-Meteo -> CompanionHK)

- `0` -> `clear`
- `1`, `2` -> `partly_cloudy`
- `3` -> `cloudy`
- `45`, `48` -> `fog`
- `51`, `53`, `55`, `56`, `57` -> `drizzle`
- `61`, `63`, `65`, `66`, `67`, `80`, `81`, `82` -> `rain`
- `71`, `73`, `75`, `77`, `85`, `86` -> `snow`
- `95`, `96`, `99` -> `thunderstorm`
- Any unknown code -> `unknown`

## Reliability and Fallback Rules

- Timeout quickly (single-digit seconds) and never block core chat.
- If upstream fails, return a degraded payload with:
  - `source=stub`
  - `condition=unknown`
  - `temperature_c=null`
  - `degraded=true`
  - `fallback_reason` populated
- Frontend must still render with a safe default theme when degraded.

## Usage Guardrails

- Do not call Open-Meteo from frontend directly.
- Do not store precise user location beyond request scope unless explicitly required.
- Keep weather requests stateless and idempotent.
- Keep provider-specific fields out of frontend contracts.
