from abc import ABC, abstractmethod
from typing import Any


class ChatProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate_reply(self, message: str, context: dict[str, Any] | None = None) -> str:
        """Generate a supportive chat reply."""


class VoiceProvider(ABC):
    provider_name: str

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Return synthesized audio bytes."""


class RetrievalProvider(ABC):
    provider_name: str

    @abstractmethod
    def retrieve(self, query: str) -> list[dict[str, Any]]:
        """Return retrieval results for freshness/context enrichment."""


class WeatherProvider(ABC):
    provider_name: str

    @abstractmethod
    def get_current_weather(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "auto"
    ) -> dict[str, Any]:
        """Return normalized weather context for a location."""


class MapsProvider(ABC):
    provider_name: str

    @abstractmethod
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
        """Return nearby places matching the query."""

    @abstractmethod
    def get_route(
        self,
        *,
        origin_latitude: float,
        origin_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
        travel_mode: str
    ) -> dict[str, Any] | None:
        """Return route metadata, if available."""
