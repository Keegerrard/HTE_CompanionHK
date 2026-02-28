import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.settings import Settings
from app.providers.base import WeatherProvider

logger = logging.getLogger(__name__)

WEATHER_CODE_TO_CONDITION: dict[int, str] = {
    0: "clear",
    1: "partly_cloudy",
    2: "partly_cloudy",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "drizzle",
    53: "drizzle",
    55: "drizzle",
    56: "drizzle",
    57: "drizzle",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm"
}


def normalize_weather_condition(weather_code: int | None) -> str:
    if weather_code is None:
        return "unknown"
    return WEATHER_CODE_TO_CONDITION.get(weather_code, "unknown")


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


class StubWeatherProvider(WeatherProvider):
    provider_name = "weather-stub"

    def get_current_weather(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "auto"
    ) -> dict[str, Any]:
        _ = timezone
        return {
            "latitude": latitude,
            "longitude": longitude,
            "temperature_c": None,
            "weather_code": None,
            "is_day": None,
            "condition": "unknown",
            "source": "stub"
        }


class OpenMeteoWeatherProvider(WeatherProvider):
    provider_name = "open-meteo"

    def __init__(self, settings: Settings):
        self._base_url = settings.open_meteo_base_url.rstrip("/")
        self._timeout_seconds = settings.provider_timeout_seconds

    def get_current_weather(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "auto"
    ) -> dict[str, Any]:
        query = urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code,is_day",
                "timezone": timezone or "auto"
            }
        )
        url = f"{self._base_url}/v1/forecast?{query}"

        try:
            with urlopen(url, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning(
                "open_meteo_request_failed latitude=%s longitude=%s error=%s",
                latitude,
                longitude,
                exc
            )
            return StubWeatherProvider().get_current_weather(
                latitude=latitude,
                longitude=longitude,
                timezone=timezone
            )

        current = payload.get("current", {})
        weather_code = _safe_int(current.get("weather_code"))
        temperature_c = _safe_float(current.get("temperature_2m"))
        is_day_value = _safe_int(current.get("is_day"))

        return {
            "latitude": latitude,
            "longitude": longitude,
            "temperature_c": temperature_c,
            "weather_code": weather_code,
            "is_day": None if is_day_value is None else bool(is_day_value),
            "condition": normalize_weather_condition(weather_code),
            "source": self.provider_name
        }
