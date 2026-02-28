from fastapi.testclient import TestClient

from app.api.routes import weather as weather_route
from app.main import app
from app.schemas.weather import WeatherData, WeatherResponse

client = TestClient(app)


def test_weather_endpoint_returns_normalized_payload(monkeypatch) -> None:
    def fake_get_current_weather(*, latitude: float, longitude: float, timezone: str) -> WeatherResponse:
        assert latitude == 22.3193
        assert longitude == 114.1694
        assert timezone == "auto"
        return WeatherResponse(
            request_id="weather-request-1",
            weather=WeatherData(
                latitude=latitude,
                longitude=longitude,
                temperature_c=27.1,
                weather_code=1,
                is_day=True,
                condition="partly_cloudy",
                source="open-meteo"
            ),
            degraded=False,
            fallback_reason=None
        )

    monkeypatch.setattr(weather_route.weather_service,
                        "get_current_weather", fake_get_current_weather)

    response = client.get(
        "/weather", params={"latitude": 22.3193, "longitude": 114.1694})

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "weather-request-1"
    assert body["weather"]["condition"] == "partly_cloudy"
    assert body["degraded"] is False


def test_weather_endpoint_validates_required_coordinates() -> None:
    response = client.get("/weather")

    assert response.status_code == 422
