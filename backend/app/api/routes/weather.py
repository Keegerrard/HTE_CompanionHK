from fastapi import APIRouter, Query

from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter()
weather_service = WeatherService()


@router.get("/weather", response_model=WeatherResponse)
def weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    timezone: str = Query(default="auto")
) -> WeatherResponse:
    return weather_service.get_current_weather(
        latitude=latitude,
        longitude=longitude,
        timezone=timezone
    )
