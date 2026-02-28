const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface WeatherRequestParams {
  latitude: number;
  longitude: number;
  timezone?: string;
}

export interface WeatherResponse {
  request_id: string;
  weather: {
    latitude: number;
    longitude: number;
    temperature_c: number | null;
    weather_code: number | null;
    is_day: boolean | null;
    condition: string;
    source: string;
  };
  degraded: boolean;
  fallback_reason: string | null;
}

export async function fetchCurrentWeather(params: WeatherRequestParams): Promise<WeatherResponse> {
  const searchParams = new URLSearchParams({
    latitude: String(params.latitude),
    longitude: String(params.longitude),
    timezone: params.timezone ?? "auto",
  });
  const response = await fetch(`${API_BASE_URL}/weather?${searchParams.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Weather request failed with status ${response.status}`);
  }
  return (await response.json()) as WeatherResponse;
}
