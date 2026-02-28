import logging
import math
from hashlib import sha256
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.settings import settings
from app.models.enums import (
    AuditEventType,
    ProviderEventScope,
    ProviderEventStatus,
    RoleType,
    TravelMode,
)
from app.providers.router import ProviderRouter
from app.repositories.audit_repository import AuditRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.recommendations import (
    Coordinates,
    RecommendationContext,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse
)
from app.services.weather_service import WeatherService

_OUTDOOR_PLACE_TYPES = {"park", "tourist_attraction",
                        "campground", "hiking_area", "beach"}
_INDOOR_PLACE_TYPES = {"cafe", "restaurant",
                       "museum", "shopping_mall", "library"}
_FALLBACK_DISCOVERY_QUERIES = ["cafe", "park", "museum", "restaurant"]
_WEATHER_INDOOR_CONDITIONS = {"rain", "drizzle", "thunderstorm", "snow"}
logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set[str]:
    return {token.strip().lower() for token in text.split() if token.strip()}


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


class RecommendationService:
    def __init__(
        self,
        provider_router: ProviderRouter | None = None,
        weather_service: WeatherService | None = None
    ):
        self._settings = settings
        self._provider_router = provider_router or ProviderRouter(settings)
        self._weather_service = weather_service or WeatherService(
            self._provider_router)

    def _coarse_user_location(self, *, latitude: float, longitude: float) -> tuple[str, str]:
        region = f"{latitude:.2f},{longitude:.2f}"
        token_length = max(
            6,
            min(24, self._settings.recommendation_user_location_geohash_precision * 2),
        )
        geohash_token = sha256(region.encode(
            "utf-8")).hexdigest()[:token_length]
        return geohash_token, region

    def _persist_recommendation_result(
        self,
        *,
        request: RecommendationRequest,
        response: RecommendationResponse,
        maps_provider_name: str,
        weather_provider_name: str,
    ) -> None:
        role_enum = RoleType(request.role)
        travel_mode = TravelMode(request.travel_mode)

        if self._settings.privacy_store_precise_user_location:
            user_location_region = f"{request.latitude:.6f},{request.longitude:.6f}"
            user_location_geohash = user_location_region
        else:
            user_location_geohash, user_location_region = self._coarse_user_location(
                latitude=request.latitude,
                longitude=request.longitude,
            )

        recommendation_status = (
            ProviderEventStatus.degraded
            if response.context.degraded
            else ProviderEventStatus.success
        )
        if (
            response.context.fallback_reason
            and "disabled_or_unavailable" in response.context.fallback_reason
        ):
            recommendation_status = ProviderEventStatus.fallback

        with SessionLocal() as session:
            user_repository = UserRepository(session)
            recommendation_repository = RecommendationRepository(session)
            audit_repository = AuditRepository(session)

            user_repository.ensure_user(request.user_id)
            recommendation_request = recommendation_repository.create_request(
                request_id=response.request_id,
                user_id=request.user_id,
                role=role_enum,
                query=request.query,
                max_results=request.max_results,
                preference_tags=request.preference_tags,
                travel_mode=travel_mode,
                user_location_geohash=user_location_geohash,
                user_location_region=user_location_region,
                context=response.context,
            )
            recommendation_repository.create_items(
                request_pk=recommendation_request.id,
                recommendations=response.recommendations,
            )

            audit_repository.create_provider_event(
                user_id=request.user_id,
                request_id=response.request_id,
                role=role_enum,
                scope=ProviderEventScope.maps,
                provider_name=maps_provider_name,
                runtime=None,
                status=recommendation_status,
                fallback_reason=response.context.fallback_reason,
                metadata_json={"result_count": len(response.recommendations)},
            )
            weather_status = (
                ProviderEventStatus.degraded
                if response.context.degraded and weather_provider_name == "stub"
                else ProviderEventStatus.success
            )
            audit_repository.create_provider_event(
                user_id=request.user_id,
                request_id=response.request_id,
                role=role_enum,
                scope=ProviderEventScope.weather,
                provider_name=weather_provider_name,
                runtime=None,
                status=weather_status,
                fallback_reason=response.context.fallback_reason,
                metadata_json={
                    "weather_condition": response.context.weather_condition,
                    "temperature_c": response.context.temperature_c,
                },
            )
            audit_repository.create_audit_event(
                event_type=AuditEventType.recommendation_request,
                user_id=request.user_id,
                request_id=response.request_id,
                role=role_enum,
                message="Recommendation request persisted",
                metadata_json={
                    "result_count": len(response.recommendations),
                    "degraded": response.context.degraded,
                    "user_location_region": user_location_region,
                },
            )
            session.commit()

    def _build_search_queries(self, query: str) -> list[str]:
        queries = [query.strip()]
        lowered = query.lower()
        for fallback in _FALLBACK_DISCOVERY_QUERIES:
            if fallback not in lowered:
                queries.append(f"{fallback} near me")
        return queries

    def _weather_fit_score(self, *, condition: str, place_types: list[str]) -> float:
        type_set = {place_type.lower() for place_type in place_types}
        if condition in _WEATHER_INDOOR_CONDITIONS:
            return 1.0 if type_set.intersection(_INDOOR_PLACE_TYPES) else 0.45
        if condition in {"clear", "partly_cloudy"}:
            return 1.0 if type_set.intersection(_OUTDOOR_PLACE_TYPES) else 0.6
        return 0.7

    def _preference_score(self, *, preference_tags: list[str], place_name: str, place_types: list[str]) -> float:
        if not preference_tags:
            return 0.5
        haystack = f"{place_name.lower()} {' '.join(place_types).lower()}"
        matches = sum(1 for tag in preference_tags if tag.lower() in haystack)
        return _clamp_score(matches / max(1, len(preference_tags)))

    def _query_relevance_score(self, *, query: str, place_name: str, place_types: list[str]) -> float:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return 0.0
        haystack = f"{place_name.lower()} {' '.join(place_types).lower()}"
        overlaps = sum(1 for token in query_tokens if token in haystack)
        return _clamp_score(overlaps / len(query_tokens))

    def _distance_score(self, *, distance_meters: int | None) -> float:
        if distance_meters is None:
            return 0.4
        if distance_meters <= 1000:
            return 1.0
        return _clamp_score(1 - (distance_meters / 12000))

    def _rating_score(self, *, rating: float | None) -> float:
        if rating is None:
            return 0.35
        return _clamp_score(rating / 5.0)

    def _review_volume_score(self, *, review_count: int | None) -> float:
        if not review_count:
            return 0.1
        return _clamp_score(math.log10(review_count + 1) / 3)

    def _total_fit_score(
        self,
        *,
        query: str,
        place_name: str,
        place_types: list[str],
        rating: float | None,
        review_count: int | None,
        distance_meters: int | None,
        condition: str,
        preference_tags: list[str]
    ) -> float:
        relevance = self._query_relevance_score(
            query=query,
            place_name=place_name,
            place_types=place_types
        )
        rating_score = self._rating_score(rating=rating)
        review_score = self._review_volume_score(review_count=review_count)
        distance_score = self._distance_score(distance_meters=distance_meters)
        weather_score = self._weather_fit_score(
            condition=condition, place_types=place_types)
        preference_score = self._preference_score(
            preference_tags=preference_tags,
            place_name=place_name,
            place_types=place_types
        )

        score = (
            (0.25 * relevance) +
            (0.20 * rating_score) +
            (0.15 * review_score) +
            (0.20 * distance_score) +
            (0.10 * weather_score) +
            (0.10 * preference_score)
        )
        return round(_clamp_score(score), 4)

    def _build_rationale(
        self,
        *,
        condition: str,
        place_types: list[str],
        rating: float | None,
        distance_text: str | None,
        duration_text: str | None,
        query: str
    ) -> str:
        reasons: list[str] = []
        if rating and rating >= 4.2:
            reasons.append("strong review score")
        if distance_text and duration_text:
            reasons.append(f"about {distance_text} away ({duration_text})")
        elif distance_text:
            reasons.append(f"about {distance_text} away")

        type_set = {place_type.lower() for place_type in place_types}
        if condition in _WEATHER_INDOOR_CONDITIONS and type_set.intersection(_INDOOR_PLACE_TYPES):
            reasons.append("indoor-friendly for current weather")
        elif condition in {"clear", "partly_cloudy"} and type_set.intersection(_OUTDOOR_PLACE_TYPES):
            reasons.append("great fit for outdoor weather")

        if not reasons:
            reasons.append("balanced option near your current area")

        return f"Matches '{query}' with {', '.join(reasons)}."

    def _fallback_recommendations(
        self,
        *,
        latitude: float,
        longitude: float,
        query: str
    ) -> list[RecommendationItem]:
        fallback_names = [
            "Nearby Cafe Option",
            "Nearby Park Walk",
            "Nearby Cultural Stop"
        ]
        fallback_types = [
            ["cafe", "food"],
            ["park", "point_of_interest"],
            ["museum", "point_of_interest"]
        ]
        offsets = [0.002, -0.002, 0.0035]
        recommendations: list[RecommendationItem] = []
        for index, name in enumerate(fallback_names):
            recommendations.append(
                RecommendationItem(
                    place_id=f"fallback-{index + 1}",
                    name=name,
                    address="Hong Kong",
                    rating=None,
                    user_ratings_total=None,
                    types=fallback_types[index],
                    location=Coordinates(
                        latitude=latitude + offsets[index],
                        longitude=longitude - offsets[index]
                    ),
                    photo_url=None,
                    maps_uri=None,
                    distance_text=None,
                    duration_text=None,
                    fit_score=0.35,
                    rationale=f"Fallback recommendation for '{query}' while live place data is unavailable."
                )
            )
        return recommendations

    def generate_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        max_results = max(3, min(5, request.max_results))
        maps_provider = self._provider_router.resolve_maps_provider()
        weather_response = self._weather_service.get_current_weather(
            latitude=request.latitude,
            longitude=request.longitude,
            timezone="auto"
        )

        deduplicated_places: dict[str, dict[str, object]] = {}
        for query in self._build_search_queries(request.query):
            candidates = maps_provider.search_places(
                query=query,
                latitude=request.latitude,
                longitude=request.longitude,
                radius_meters=settings.google_maps_default_radius_meters,
                language=settings.google_maps_language,
                max_results=max_results * 2
            )
            for place in candidates:
                place_id = str(place.get("place_id") or "")
                dedupe_key = place_id or f"{place.get('name')}-{place.get('address')}"
                if dedupe_key not in deduplicated_places:
                    deduplicated_places[dedupe_key] = place
            if len(deduplicated_places) >= max_results * 2:
                break

        scored_items: list[RecommendationItem] = []
        weather_condition = weather_response.weather.condition
        for place in deduplicated_places.values():
            destination_latitude = float(
                place.get("latitude", request.latitude))
            destination_longitude = float(
                place.get("longitude", request.longitude))
            route = maps_provider.get_route(
                origin_latitude=request.latitude,
                origin_longitude=request.longitude,
                destination_latitude=destination_latitude,
                destination_longitude=destination_longitude,
                travel_mode=request.travel_mode
            )
            distance_meters = None if route is None else route.get(
                "distance_meters")
            distance_text = None if route is None else route.get(
                "distance_text")
            duration_text = None if route is None else route.get(
                "duration_text")

            place_types = [str(value)
                           for value in list(place.get("types") or [])]
            rating = place.get("rating")
            review_count = place.get("user_ratings_total")
            fit_score = self._total_fit_score(
                query=request.query,
                place_name=str(place.get("name", "")),
                place_types=place_types,
                rating=None if rating is None else float(rating),
                review_count=None if review_count is None else int(
                    review_count),
                distance_meters=None if distance_meters is None else int(
                    distance_meters),
                condition=weather_condition,
                preference_tags=request.preference_tags
            )

            scored_items.append(
                RecommendationItem(
                    place_id=str(place.get("place_id") or ""),
                    name=str(place.get("name", "Unknown place")),
                    address=str(place.get("address", "Address unavailable")),
                    rating=None if rating is None else float(rating),
                    user_ratings_total=None if review_count is None else int(
                        review_count),
                    types=place_types,
                    location=Coordinates(
                        latitude=destination_latitude,
                        longitude=destination_longitude
                    ),
                    photo_url=(
                        None
                        if place.get("photo_url") is None
                        else str(place.get("photo_url"))
                    ),
                    maps_uri=(
                        None
                        if place.get("maps_uri") is None
                        else str(place.get("maps_uri"))
                    ),
                    distance_text=None if distance_text is None else str(
                        distance_text),
                    duration_text=None if duration_text is None else str(
                        duration_text),
                    fit_score=fit_score,
                    rationale=self._build_rationale(
                        condition=weather_condition,
                        place_types=place_types,
                        rating=None if rating is None else float(rating),
                        distance_text=None if distance_text is None else str(
                            distance_text),
                        duration_text=None if duration_text is None else str(
                            duration_text),
                        query=request.query
                    )
                )
            )

        scored_items.sort(key=lambda item: item.fit_score, reverse=True)
        recommendations = scored_items[:max_results]

        degraded = weather_response.degraded
        fallback_reason = weather_response.fallback_reason
        if maps_provider.provider_name == "maps-stub":
            degraded = True
            fallback_reason = "maps_provider_disabled_or_unavailable"

        if len(recommendations) < 3:
            degraded = True
            fallback_reason = fallback_reason or "insufficient_live_place_results"
            recommendations = self._fallback_recommendations(
                latitude=request.latitude,
                longitude=request.longitude,
                query=request.query
            )[:max_results]

        response = RecommendationResponse(
            request_id=str(uuid4()),
            recommendations=recommendations,
            context=RecommendationContext(
                weather_condition=weather_condition,
                temperature_c=weather_response.weather.temperature_c,
                degraded=degraded,
                fallback_reason=fallback_reason
            )
        )
        try:
            self._persist_recommendation_result(
                request=request,
                response=response,
                maps_provider_name=maps_provider.provider_name,
                weather_provider_name=weather_response.weather.source,
            )
        except Exception:
            logger.exception(
                "recommendation_persistence_failed request_id=%s user_id=%s role=%s",
                response.request_id,
                request.user_id,
                request.role,
            )
        return response
