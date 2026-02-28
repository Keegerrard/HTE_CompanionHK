import { createTheme } from "@mui/material/styles";

export interface WeatherThemeContext {
  condition?: string;
  isDay?: boolean | null;
  temperatureC?: number | null;
}

function buildPalette(context?: WeatherThemeContext) {
  const condition = context?.condition ?? "unknown";
  const isDay = context?.isDay ?? true;

  if (condition === "clear" && !isDay) {
    return {
      mode: "dark" as const,
      primary: { main: "#90CAF9" },
      secondary: { main: "#F48FB1" },
      background: { default: "#0B1320", paper: "#111A2A" },
    };
  }

  if (condition === "clear") {
    return {
      mode: "light" as const,
      primary: { main: "#2563EB" },
      secondary: { main: "#F59E0B" },
      background: { default: "#FFF9E8", paper: "#FFFFFF" },
    };
  }

  if (condition === "rain" || condition === "drizzle" || condition === "thunderstorm") {
    return {
      mode: "light" as const,
      primary: { main: "#1E3A8A" },
      secondary: { main: "#0EA5E9" },
      background: { default: "#EDF4FF", paper: "#FFFFFF" },
    };
  }

  if (condition === "cloudy" || condition === "partly_cloudy" || condition === "fog") {
    return {
      mode: "light" as const,
      primary: { main: "#475569" },
      secondary: { main: "#7C3AED" },
      background: { default: "#F1F5F9", paper: "#FFFFFF" },
    };
  }

  return {
    mode: "light" as const,
    primary: { main: "#5A67D8" },
    secondary: { main: "#ED64A6" },
    background: { default: "#F7FAFC", paper: "#FFFFFF" },
  };
}

export function createCompanionTheme(context?: WeatherThemeContext) {
  const palette = buildPalette(context);
  return createTheme({
    palette,
    shape: {
      borderRadius: 12,
    },
  });
}

export const companionTheme = createCompanionTheme();
