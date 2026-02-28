from app.core.settings import Settings
from app.providers.base import ChatProvider, MapsProvider, WeatherProvider
from app.providers.google_maps import GoogleMapsProvider, StubMapsProvider
from app.providers.minimax import MiniMaxChatProvider
from app.providers.mock import MockChatProvider
from app.providers.open_meteo import OpenMeteoWeatherProvider, StubWeatherProvider


class ProviderRouter:
    def __init__(self, settings: Settings):
        self._settings = settings

    def resolve_chat_provider(self) -> ChatProvider:
        if (
            self._settings.chat_provider == "minimax"
            and self._settings.feature_minimax_enabled
            and self._settings.minimax_api_key
        ):
            return MiniMaxChatProvider(
                api_key=self._settings.minimax_api_key,
                model=self._settings.minimax_model,
                base_url=self._settings.minimax_base_url,
            )
        return MockChatProvider()

    def resolve_weather_provider(self) -> WeatherProvider:
        if self._settings.feature_weather_enabled:
            return OpenMeteoWeatherProvider(self._settings)
        return StubWeatherProvider()

    def resolve_maps_provider(self) -> MapsProvider:
        if self._settings.feature_google_maps_enabled and self._settings.google_maps_api_key:
            return GoogleMapsProvider(self._settings)
        return StubMapsProvider()
