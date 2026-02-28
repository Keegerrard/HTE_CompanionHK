import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.settings import Settings
from app.providers.base import MapsProvider

logger = logging.getLogger(__name__)

_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


class StubMapsProvider(MapsProvider):
    provider_name = "maps-stub"

    def search_places(
        self,
        *,
        query: str,
        latitude: float,
        longitude: float,
        radius_meters: int,
        language: str,
        max_results: int
    ) -> list[dict[str, Any]]:
        _ = (query, latitude, longitude, radius_meters, language, max_results)
        return []

    def get_route(
        self,
        *,
        origin_latitude: float,
        origin_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
        travel_mode: str
    ) -> dict[str, Any] | None:
        _ = (
            origin_latitude,
            origin_longitude,
            destination_latitude,
            destination_longitude,
            travel_mode
        )
        return None


class GoogleMapsProvider(MapsProvider):
    provider_name = "google-maps"

    def __init__(self, settings: Settings):
        self._api_key = settings.google_maps_api_key
        self._default_language = settings.google_maps_language
        self._region = settings.google_maps_region
        self._photo_max_width = settings.google_maps_photo_max_width
        self._timeout_seconds = settings.provider_timeout_seconds

    def _get_json(
        self,
        *,
        endpoint: str,
        params: dict[str, Any]
    ) -> dict[str, Any] | None:
        query = urlencode(params)
        url = f"{endpoint}?{query}"
        try:
            with urlopen(url, timeout=self._timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning(
                "google_maps_request_failed endpoint=%s error=%s",
                endpoint,
                exc
            )
            return None

    def _build_photo_url(self, photo_reference: str | None) -> str | None:
        if not photo_reference:
            return None
        params = urlencode(
            {
                "maxwidth": self._photo_max_width,
                "photo_reference": photo_reference,
                "key": self._api_key
            }
        )
        return f"https://maps.googleapis.com/maps/api/place/photo?{params}"

    def search_places(
        self,
        *,
        query: str,
        latitude: float,
        longitude: float,
        radius_meters: int,
        language: str,
        max_results: int
    ) -> list[dict[str, Any]]:
        if not self._api_key:
            logger.warning("google_maps_api_key_missing search_skipped")
            return []

        payload = self._get_json(
            endpoint=_TEXT_SEARCH_URL,
            params={
                "query": query,
                "location": f"{latitude},{longitude}",
                "radius": radius_meters,
                "language": language or self._default_language,
                "region": self._region,
                "key": self._api_key
            }
        )
        if payload is None:
            return []

        status = str(payload.get("status", "UNKNOWN"))
        if status == "ZERO_RESULTS":
            return []
        if status != "OK":
            logger.warning(
                "google_maps_text_search_unexpected_status status=%s query=%s",
                status,
                query
            )
            return []

        places: list[dict[str, Any]] = []
        for item in payload.get("results", [])[:max_results]:
            location = (item.get("geometry") or {}).get("location") or {}
            item_latitude = _safe_float(location.get("lat"))
            item_longitude = _safe_float(location.get("lng"))
            if item_latitude is None or item_longitude is None:
                continue

            photos = item.get("photos") or []
            photo_reference = None
            if photos and isinstance(photos, list):
                photo_reference = (photos[0] or {}).get("photo_reference")

            place_id = str(item.get("place_id", ""))
            places.append(
                {
                    "place_id": place_id,
                    "name": str(item.get("name", "Unknown place")),
                    "address": str(item.get("formatted_address", "Address unavailable")),
                    "rating": _safe_float(item.get("rating")),
                    "user_ratings_total": _safe_int(item.get("user_ratings_total")),
                    "types": list(item.get("types") or []),
                    "latitude": item_latitude,
                    "longitude": item_longitude,
                    "photo_url": self._build_photo_url(photo_reference),
                    "maps_uri": (
                        f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                        if place_id
                        else None
                    )
                }
            )
        return places

    def get_route(
        self,
        *,
        origin_latitude: float,
        origin_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
        travel_mode: str
    ) -> dict[str, Any] | None:
        if not self._api_key:
            logger.warning("google_maps_api_key_missing route_skipped")
            return None

        mode = travel_mode if travel_mode in {
            "walking", "driving", "transit"} else "walking"
        payload = self._get_json(
            endpoint=_DIRECTIONS_URL,
            params={
                "origin": f"{origin_latitude},{origin_longitude}",
                "destination": f"{destination_latitude},{destination_longitude}",
                "mode": mode,
                "region": self._region,
                "language": self._default_language,
                "key": self._api_key
            }
        )
        if payload is None:
            return None

        status = str(payload.get("status", "UNKNOWN"))
        if status != "OK":
            return None

        routes = payload.get("routes") or []
        if not routes:
            return None
        legs = (routes[0] or {}).get("legs") or []
        if not legs:
            return None
        leg = legs[0] or {}
        distance = leg.get("distance") or {}
        duration = leg.get("duration") or {}

        return {
            "distance_meters": _safe_int(distance.get("value")),
            "distance_text": distance.get("text"),
            "duration_seconds": _safe_int(duration.get("value")),
            "duration_text": duration.get("text"),
            "travel_mode": mode
        }
