from typing import Literal

from pydantic import BaseModel

WeatherCondition = Literal[
    "clear",
    "partly_cloudy",
    "cloudy",
    "fog",
    "drizzle",
    "rain",
    "snow",
    "thunderstorm",
    "unknown"
]


class WeatherData(BaseModel):
    latitude: float
    longitude: float
    temperature_c: float | None = None
    weather_code: int | None = None
    is_day: bool | None = None
    condition: WeatherCondition = "unknown"
    source: str = "open-meteo"


class WeatherResponse(BaseModel):
    request_id: str
    weather: WeatherData
    degraded: bool = False
    fallback_reason: str | None = None
