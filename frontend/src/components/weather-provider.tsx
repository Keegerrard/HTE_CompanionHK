"use client";

import { createContext, useContext, useEffect, useState, type PropsWithChildren } from "react";
import { fetchCurrentWeather } from "@/lib/api/weather";

export interface WeatherContext {
  condition: string;
  isDay: boolean | null;
  temperatureC: number | null;
}

const FALLBACK_COORDINATES = { latitude: 22.3193, longitude: 114.1694 };

const WeatherCtx = createContext<WeatherContext>({
  condition: "unknown",
  isDay: true,
  temperatureC: null,
});

export function useWeather() {
  return useContext(WeatherCtx);
}

function conditionToDataAttr(condition: string, isDay: boolean | null): string {
  if (condition === "clear") {
    return isDay === false ? "clear-night" : "clear-day";
  }
  const known = ["rain", "drizzle", "thunderstorm", "cloudy", "partly_cloudy", "fog", "snow"];
  return known.includes(condition) ? condition : "unknown";
}

function getBrowserCoordinates(
  timeoutMs = 2500,
): Promise<{ latitude: number; longitude: number } | null> {
  return new Promise((resolve) => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
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
      (pos) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
      },
      () => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(null);
      },
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 5 * 60_000 },
    );
  });
}

export function WeatherProvider({ children }: PropsWithChildren) {
  const [weather, setWeather] = useState<WeatherContext>({
    condition: "unknown",
    isDay: true,
    temperatureC: null,
  });

  useEffect(() => {
    let active = true;

    async function load() {
      const coords = (await getBrowserCoordinates()) ?? FALLBACK_COORDINATES;
      try {
        const res = await fetchCurrentWeather(coords);
        if (!active) return;
        setWeather({
          condition: res.weather.condition,
          isDay: res.weather.is_day,
          temperatureC: res.weather.temperature_c,
        });
      } catch {
        /* keep defaults */
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const attr = conditionToDataAttr(weather.condition, weather.isDay);
    document.documentElement.setAttribute("data-weather", attr);
  }, [weather.condition, weather.isDay]);

  return <WeatherCtx.Provider value={weather}>{children}</WeatherCtx.Provider>;
}
