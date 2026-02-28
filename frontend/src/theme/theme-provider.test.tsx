import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CompanionThemeProvider } from "@/theme/theme-provider";
import * as weatherApi from "@/lib/api/weather";

vi.mock("@/lib/api/weather", () => ({
  fetchCurrentWeather: vi.fn(),
}));

describe("CompanionThemeProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(weatherApi.fetchCurrentWeather).mockResolvedValue({
      request_id: "weather-request",
      weather: {
        latitude: 22.3193,
        longitude: 114.1694,
        temperature_c: 28,
        weather_code: 0,
        is_day: true,
        condition: "clear",
        source: "open-meteo",
      },
      degraded: false,
      fallback_reason: null,
    });
  });

  it("loads weather context and renders children", async () => {
    render(
      <CompanionThemeProvider>
        <div>Theme Ready</div>
      </CompanionThemeProvider>,
    );

    expect(screen.getByText("Theme Ready")).toBeInTheDocument();
    await waitFor(() => {
      expect(weatherApi.fetchCurrentWeather).toHaveBeenCalledWith({
        latitude: 22.3193,
        longitude: 114.1694,
      });
    });
  });
});
