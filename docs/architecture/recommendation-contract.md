# Recommendation and Weather API Contract

This document defines CompanionHK internal API contracts between frontend and backend for weather and local recommendations.

## Weather Endpoint

### Request

- Method: `GET`
- Path: `/weather`
- Query params:
  - `latitude: float` (required)
  - `longitude: float` (required)
  - `timezone: string` (optional, default `auto`)

### Response Shape

```json
{
  "request_id": "uuid",
  "weather": {
    "latitude": 22.3193,
    "longitude": 114.1694,
    "temperature_c": 27.1,
    "weather_code": 3,
    "is_day": true,
    "condition": "cloudy",
    "source": "open-meteo"
  },
  "degraded": false,
  "fallback_reason": null
}
```

## Recommendation Endpoint

### Request

- Method: `POST`
- Path: `/recommendations`
- JSON body:

```json
{
  "user_id": "demo-user",
  "role": "local_guide",
  "query": "quiet cafe in central",
  "latitude": 22.2819,
  "longitude": 114.1589,
  "max_results": 5,
  "preference_tags": ["quiet", "wifi"],
  "travel_mode": "walking"
}
```

### Response Shape

```json
{
  "request_id": "uuid",
  "recommendations": [
    {
      "place_id": "abc123",
      "name": "Example Cafe",
      "address": "Central, Hong Kong",
      "rating": 4.4,
      "user_ratings_total": 832,
      "types": ["cafe", "food", "point_of_interest"],
      "location": {
        "latitude": 22.2821,
        "longitude": 114.1578
      },
      "photo_url": "https://maps.googleapis.com/maps/api/place/photo?...",
      "maps_uri": "https://www.google.com/maps/place/?q=place_id:abc123",
      "distance_text": "1.2 km",
      "duration_text": "16 mins",
      "fit_score": 0.84,
      "rationale": "High-rated cafe close to you, suitable for rainy weather."
    }
  ],
  "context": {
    "weather_condition": "rain",
    "temperature_c": 24.7,
    "degraded": false,
    "fallback_reason": null
  }
}
```

## Validation Rules

- `role` must be `companion | local_guide | study_guide`.
- Recommendation flow is optimized for `local_guide`.
- `max_results` is clamped to `3..5`.
- `travel_mode` supports `walking | transit | driving`.
- `fit_score` is normalized to `0..1`.

## Compatibility Rules

- New fields must be additive.
- Existing field names and meanings are stable for frontend clients.
- Provider-specific payloads stay internal to backend service layer.

## Error and Degradation Rules

- Weather/Maps failures return degraded responses with a fallback reason.
- Recommendation endpoint should still return a valid payload shape.
- Empty provider results trigger fallback queries and/or minimal fallback recommendations.
