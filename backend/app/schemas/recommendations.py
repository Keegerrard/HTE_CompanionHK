from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.chat import ChatRole

TravelMode = Literal["walking", "transit", "driving"]


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RecommendationRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: ChatRole = "local_guide"
    query: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    max_results: int = Field(default=5, ge=3, le=5)
    preference_tags: list[str] = Field(default_factory=list)
    travel_mode: TravelMode = "walking"


class RecommendationItem(BaseModel):
    place_id: str
    name: str
    address: str
    rating: float | None = None
    user_ratings_total: int | None = None
    types: list[str] = Field(default_factory=list)
    location: Coordinates
    photo_url: str | None = None
    maps_uri: str | None = None
    distance_text: str | None = None
    duration_text: str | None = None
    fit_score: float = Field(ge=0.0, le=1.0)
    rationale: str


class RecommendationContext(BaseModel):
    weather_condition: str = "unknown"
    temperature_c: float | None = None
    degraded: bool = False
    fallback_reason: str | None = None


class RecommendationResponse(BaseModel):
    request_id: str
    recommendations: list[RecommendationItem]
    context: RecommendationContext
