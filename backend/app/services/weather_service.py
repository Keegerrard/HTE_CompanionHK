from uuid import uuid4

from app.core.settings import settings
from app.providers.router import ProviderRouter
from app.schemas.weather import WeatherData, WeatherResponse


class WeatherService:
    def __init__(self, provider_router: ProviderRouter | None = None):
        self._provider_router = provider_router or ProviderRouter(settings)

    def get_current_weather(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "auto"
    ) -> WeatherResponse:
        provider = self._provider_router.resolve_weather_provider()
        weather_payload = provider.get_current_weather(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )
        weather = WeatherData(**weather_payload)
        degraded = weather.source == "stub" or weather.condition == "unknown"

        return WeatherResponse(
            request_id=str(uuid4()),
            weather=weather,
            degraded=degraded,
            fallback_reason=(
                "provider_disabled_or_unavailable" if weather.source == "stub" else None)
        )
