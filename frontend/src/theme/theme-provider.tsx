"use client";

import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import type { PropsWithChildren } from "react";
import { useEffect, useMemo, useState } from "react";
import { fetchCurrentWeather } from "@/lib/api/weather";
import { createCompanionTheme, type WeatherThemeContext } from "./theme";

const FALLBACK_COORDINATES = {
  latitude: 22.3193,
  longitude: 114.1694,
};

function getBrowserCoordinates(timeoutMs = 2500): Promise<{
  latitude: number;
  longitude: number;
} | null> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }

    let settled = false;
    const timer = window.setTimeout(() => {
      if (!settled) {
        settled = true;
        resolve(null);
      }
    }, timeoutMs);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (settled) {
          return;
        }
        settled = true;
        window.clearTimeout(timer);
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      () => {
        if (settled) {
          return;
        }
        settled = true;
        window.clearTimeout(timer);
        resolve(null);
      },
      {
        enableHighAccuracy: false,
        timeout: timeoutMs,
        maximumAge: 5 * 60 * 1000,
      },
    );
  });
}

export function CompanionThemeProvider({ children }: PropsWithChildren) {
  const [weatherContext, setWeatherContext] = useState<WeatherThemeContext>({
    condition: "unknown",
    isDay: true,
    temperatureC: null,
  });

  useEffect(() => {
    let isActive = true;

    async function loadWeatherTheme() {
      const browserCoordinates = await getBrowserCoordinates();
      const coordinates = browserCoordinates ?? FALLBACK_COORDINATES;

      try {
        const response = await fetchCurrentWeather(coordinates);
        if (!isActive) {
          return;
        }
        setWeatherContext({
          condition: response.weather.condition,
          isDay: response.weather.is_day,
          temperatureC: response.weather.temperature_c,
        });
      } catch {
        if (!isActive) {
          return;
        }
        setWeatherContext({
          condition: "unknown",
          isDay: true,
          temperatureC: null,
        });
      }
    }

    void loadWeatherTheme();
    return () => {
      isActive = false;
    };
  }, []);

  const theme = useMemo(() => createCompanionTheme(weatherContext), [weatherContext]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
