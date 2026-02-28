"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Map } from "lucide-react";
import type { RecommendationItem } from "@/features/recommendations/types";

interface MapCanvasProps {
  apiKey?: string;
  center: { latitude: number; longitude: number };
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
  const w = window as Window & { google?: { maps?: GoogleMapsNamespace } };
  return w.google?.maps ?? null;
}

function loadGoogleMapsScript(apiKey: string): Promise<void> {
  if (typeof window !== "undefined" && readGoogleMapsNamespace()) return Promise.resolve();
  if (googleMapsLoaderPromise) return googleMapsLoaderPromise;

  googleMapsLoaderPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(
      "script[data-companionhk-google-maps='true']",
    ) as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Failed to load Google Maps.")), {
        once: true,
      });
      return;
    }
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}`;
    script.async = true;
    script.defer = true;
    script.dataset.companionhkGoogleMaps = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Maps."));
    document.head.appendChild(script);
  });
  return googleMapsLoaderPromise;
}

export function MapCanvas({ apiKey, center, recommendations }: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<GoogleMapInstance | null>(null);
  const markersRef = useRef<GoogleMarkerInstance[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (!apiKey || recommendations.length === 0 || !containerRef.current) return;
    let active = true;

    async function render() {
      if (!apiKey) return;
      try {
        await loadGoogleMapsScript(apiKey);
        if (!active || !containerRef.current) return;
        const gm = readGoogleMapsNamespace();
        if (!gm) {
          setMapError("Google Maps SDK is unavailable.");
          return;
        }

        const map =
          mapRef.current ??
          new gm.Map(containerRef.current, {
            center: { lat: center.latitude, lng: center.longitude },
            zoom: 13,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
          });
        mapRef.current = map;

        markersRef.current.forEach((m) => m.setMap(null));
        markersRef.current = [];

        const bounds = new gm.LatLngBounds();
        recommendations.forEach((rec) => {
          const marker = new gm.Marker({
            map,
            position: { lat: rec.location.latitude, lng: rec.location.longitude },
            title: rec.name,
          });
          markersRef.current.push(marker);
          bounds.extend(marker.getPosition());
        });
        bounds.extend({ lat: center.latitude, lng: center.longitude });
        map.fitBounds(bounds);
        setMapError(null);
      } catch (err) {
        if (active) setMapError(err instanceof Error ? err.message : "Unable to render map.");
      }
    }

    void render();
    return () => {
      active = false;
    };
  }, [apiKey, center.latitude, center.longitude, recommendations]);

  if (!apiKey) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-muted/50 px-4 py-3 text-sm text-muted-foreground">
        <Map className="size-4 shrink-0" />
        Set{" "}
        <code className="rounded bg-muted px-1 font-mono text-xs">
          NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
        </code>{" "}
        to display the map.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border/60 bg-card shadow-(--shadow-warm-sm)">
      <div className="flex items-center gap-2 px-4 py-2.5">
        <Map className="size-4 text-role-local-guide" />
        <span className="text-sm font-bold font-heading text-card-foreground">Map View</span>
      </div>
      {mapError && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent-foreground">
          <AlertTriangle className="size-4 shrink-0" />
          {mapError}
        </div>
      )}
      <div ref={containerRef} className="h-72 w-full bg-muted" />
    </div>
  );
}
