from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import RoleType, TravelMode
from app.models.recommendation import RecommendationItem, RecommendationRequest
from app.schemas.recommendations import RecommendationContext, RecommendationItem as RecommendationItemSchema


class RecommendationRepository:
    def __init__(self, session: Session):
        self._session = session

    def create_request(
        self,
        *,
        request_id: str,
        user_id: str,
        role: RoleType,
        query: str,
        max_results: int,
        preference_tags: list[str],
        travel_mode: TravelMode,
        user_location_geohash: str | None,
        user_location_region: str | None,
        context: RecommendationContext,
    ) -> RecommendationRequest:
        recommendation_request = RecommendationRequest(
            request_id=request_id,
            user_id=user_id,
            role=role,
            query=query,
            max_results=max_results,
            preference_tags=preference_tags,
            travel_mode=travel_mode,
            user_location_geohash=user_location_geohash,
            user_location_region=user_location_region,
            weather_condition=context.weather_condition,
            temperature_c=context.temperature_c,
            degraded=context.degraded,
            fallback_reason=context.fallback_reason,
        )
        self._session.add(recommendation_request)
        self._session.flush()
        return recommendation_request

    def create_items(
        self,
        *,
        request_pk: str,
        recommendations: list[RecommendationItemSchema],
    ) -> list[RecommendationItem]:
        rows: list[RecommendationItem] = []
        for recommendation in recommendations:
            row = RecommendationItem(
                recommendation_request_id=request_pk,
                place_id=recommendation.place_id,
                name=recommendation.name,
                address=recommendation.address,
                rating=recommendation.rating,
                user_ratings_total=recommendation.user_ratings_total,
                types=recommendation.types,
                place_latitude=recommendation.location.latitude,
                place_longitude=recommendation.location.longitude,
                photo_url=recommendation.photo_url,
                maps_uri=recommendation.maps_uri,
                distance_text=recommendation.distance_text,
                duration_text=recommendation.duration_text,
                fit_score=recommendation.fit_score,
                rationale=recommendation.rationale,
            )
            rows.append(row)

        self._session.add_all(rows)
        self._session.flush()
        return rows
