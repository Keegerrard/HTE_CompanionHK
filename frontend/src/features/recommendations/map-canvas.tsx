"use client";

import { useEffect, useRef, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import type { RecommendationItem } from "@/features/recommendations/types";

interface MapCanvasProps {
  apiKey?: string;
  center: {
    latitude: number;
    longitude: number;
  };
  recommendations: RecommendationItem[];
}

type GoogleMapInstance = {
  fitBounds: (bounds: GoogleLatLngBoundsInstance) => void;
};

type GoogleMarkerInstance = {
  setMap: (map: GoogleMapInstance | null) => void;
  getPosition: () => unknown;
};

type GoogleLatLngBoundsInstance = {
  extend: (value: unknown) => void;
};

type GoogleMapsNamespace = {
  Map: new (
    element: HTMLDivElement,
    options: {
      center: { lat: number; lng: number };
      zoom: number;
      mapTypeControl: boolean;
      streetViewControl: boolean;
      fullscreenControl: boolean;
    },
  ) => GoogleMapInstance;
  Marker: new (options: {
    map: GoogleMapInstance;
    position: { lat: number; lng: number };
    title: string;
  }) => GoogleMarkerInstance;
  LatLngBounds: new () => GoogleLatLngBoundsInstance;
};

let googleMapsLoaderPromise: Promise<void> | null = null;

function readGoogleMapsNamespace(): GoogleMapsNamespace | null {
  const windowWithGoogle = window as Window & {
    google?: {
      maps?: GoogleMapsNamespace;
    };
  };
  return windowWithGoogle.google?.maps ?? null;
}

function loadGoogleMapsScript(apiKey: string): Promise<void> {
  if (typeof window !== "undefined" && readGoogleMapsNamespace()) {
    return Promise.resolve();
  }
  if (googleMapsLoaderPromise) {
    return googleMapsLoaderPromise;
  }

  googleMapsLoaderPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector(
      "script[data-companionhk-google-maps='true']",
    ) as HTMLScriptElement | null;

    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener(
        "error",
        () => reject(new Error("Failed to load Google Maps script.")),
        { once: true },
      );
      return;
    }

    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}`;
    script.async = true;
    script.defer = true;
    script.dataset.companionhkGoogleMaps = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Maps script."));
    document.head.appendChild(script);
  });

  return googleMapsLoaderPromise;
}

export function MapCanvas({ apiKey, center, recommendations }: MapCanvasProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<GoogleMapInstance | null>(null);
  const markersRef = useRef<GoogleMarkerInstance[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (!apiKey || recommendations.length === 0 || !mapContainerRef.current) {
      return;
    }

    let active = true;

    async function renderMap() {
      try {
        await loadGoogleMapsScript(apiKey);
        if (!active || !mapContainerRef.current) {
          return;
        }
        const googleMaps = readGoogleMapsNamespace();
        if (!googleMaps) {
          setMapError("Google Maps SDK is unavailable.");
          return;
        }

        const map =
          mapRef.current ??
          new googleMaps.Map(mapContainerRef.current, {
            center: { lat: center.latitude, lng: center.longitude },
            zoom: 13,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
          });
        mapRef.current = map;

        markersRef.current.forEach((marker) => marker.setMap(null));
        markersRef.current = [];

        const bounds = new googleMaps.LatLngBounds();
        recommendations.forEach((recommendation) => {
          const marker = new googleMaps.Marker({
            map,
            position: {
              lat: recommendation.location.latitude,
              lng: recommendation.location.longitude,
            },
            title: recommendation.name,
          });
          markersRef.current.push(marker);
          bounds.extend(marker.getPosition());
        });
        bounds.extend({ lat: center.latitude, lng: center.longitude });
        map.fitBounds(bounds);
        setMapError(null);
      } catch (error) {
        if (!active) {
          return;
        }
        setMapError(error instanceof Error ? error.message : "Unable to render map.");
      }
    }

    void renderMap();
    return () => {
      active = false;
    };
  }, [apiKey, center.latitude, center.longitude, recommendations]);

  if (!apiKey) {
    return (
      <Alert severity="info">
        Set <code>NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to display the interactive map canvas.
      </Alert>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 3 }}>
      <Typography variant="h6" sx={{ px: 0.5, pb: 1, fontWeight: 700 }}>
        Map View
      </Typography>
      {mapError && (
        <Alert severity="warning" sx={{ mb: 1.5 }}>
          {mapError}
        </Alert>
      )}
      <Box
        ref={mapContainerRef}
        sx={{
          width: "100%",
          height: 320,
          borderRadius: 2,
          overflow: "hidden",
          bgcolor: "grey.100",
        }}
      />
    </Paper>
  );
}
