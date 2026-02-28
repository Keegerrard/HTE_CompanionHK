import logging

from app.core.settings import Settings
from app.providers.base import ChatProvider, MapsProvider, RetrievalProvider, VoiceProvider, WeatherProvider
from app.providers.google_maps import GoogleMapsProvider, StubMapsProvider
from app.providers.minimax import MiniMaxChatProvider
from app.providers.mock import MockChatProvider
from app.providers.open_meteo import OpenMeteoWeatherProvider, StubWeatherProvider

logger = logging.getLogger(__name__)


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

    def resolve_voice_provider(self, provider_name: str) -> VoiceProvider | None:
        if provider_name == "elevenlabs" and self._settings.feature_elevenlabs_enabled:
            try:
                from app.providers.elevenlabs import ElevenLabsVoiceProvider
                return ElevenLabsVoiceProvider()
            except Exception:
                logger.exception("elevenlabs_provider_init_failed")
                return None

        if provider_name == "cantoneseai" and self._settings.feature_cantoneseai_enabled:
            try:
                from app.providers.cantoneseai import CantoneseAIVoiceProvider
                return CantoneseAIVoiceProvider()
            except Exception:
                logger.exception("cantoneseai_provider_init_failed")
                return None

        return None

    def resolve_retrieval_provider(self) -> RetrievalProvider | None:
        if self._settings.feature_exa_enabled and self._settings.exa_api_key:
            from app.providers.exa import ExaRetrievalProvider
            return ExaRetrievalProvider(
                api_key=self._settings.exa_api_key,
                timeout=self._settings.provider_timeout_seconds,
            )
        return None

    def resolve_weather_provider(self) -> WeatherProvider:
        if self._settings.feature_weather_enabled:
            return OpenMeteoWeatherProvider(self._settings)
        return StubWeatherProvider()

    def resolve_maps_provider(self) -> MapsProvider:
        if self._settings.feature_google_maps_enabled and self._settings.google_maps_api_key:
            return GoogleMapsProvider(self._settings)
        return StubMapsProvider()
