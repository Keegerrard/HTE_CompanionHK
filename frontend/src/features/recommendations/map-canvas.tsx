"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Map } from "lucide-react";
import { fadeSlideUp, springGentle } from "@/lib/motion-config";
import type { RecommendationItem } from "@/features/recommendations/types";

interface MapCanvasProps {
  apiKey?: string;
  center: { latitude: number; longitude: number };
  recommendations: RecommendationItem[];
}

type GoogleMapInstance = {
  fitBounds: (bounds: GoogleLatLngBoundsInstance) => void;
  setOptions: (opts: Record<string, unknown>) => void;
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
      styles?: Record<string, unknown>[];
    },
  ) => GoogleMapInstance;
  Marker: new (options: {
    map: GoogleMapInstance;
    position: { lat: number; lng: number };
    title: string;
  }) => GoogleMarkerInstance;
  LatLngBounds: new () => GoogleLatLngBoundsInstance;
};

const WARM_MAP_STYLES: Record<string, unknown>[] = [
  { featureType: "water", elementType: "geometry.fill", stylers: [{ color: "#c9daf8" }] },
  {
    featureType: "landscape.natural",
    elementType: "geometry.fill",
    stylers: [{ color: "#f0ebe3" }],
  },
  { featureType: "poi", elementType: "geometry.fill", stylers: [{ color: "#e8e0d4" }] },
  { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#7a6e60" }] },
  { featureType: "road.highway", elementType: "geometry.fill", stylers: [{ color: "#f5dcc0" }] },
  { featureType: "road.highway", elementType: "geometry.stroke", stylers: [{ color: "#e0c8a8" }] },
  { featureType: "road.arterial", elementType: "geometry.fill", stylers: [{ color: "#faf5ef" }] },
  { featureType: "road.local", elementType: "geometry.fill", stylers: [{ color: "#ffffff" }] },
  { featureType: "transit", elementType: "geometry.fill", stylers: [{ color: "#e8ddd0" }] },
  {
    featureType: "administrative",
    elementType: "labels.text.fill",
    stylers: [{ color: "#6b5e50" }],
  },
  { featureType: "poi.park", elementType: "geometry.fill", stylers: [{ color: "#d4e4c8" }] },
  {
    featureType: "all",
    elementType: "labels.text.stroke",
    stylers: [{ color: "#ffffff" }, { weight: 3 }],
  },
];

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

function MapSkeleton() {
  return (
    <div className="relative h-64 sm:h-72 md:h-80 w-full overflow-hidden rounded-b-xl">
      <div className="animate-shimmer absolute inset-0" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-muted-foreground/50">
          <Map className="size-8 animate-pulse-gentle" />
          <span className="text-xs font-medium">Loading map...</span>
        </div>
      </div>
    </div>
  );
}

export function MapCanvas({ apiKey, center, recommendations }: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<GoogleMapInstance | null>(null);
  const markersRef = useRef<GoogleMarkerInstance[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!apiKey || recommendations.length === 0 || !containerRef.current) return;
    let active = true;

    async function render() {
      if (!apiKey) return;
      try {
        setIsLoading(true);
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
            styles: WARM_MAP_STYLES,
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
        setIsLoading(false);
      } catch (err) {
        if (active) {
          setMapError(err instanceof Error ? err.message : "Unable to render map.");
          setIsLoading(false);
        }
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
    <motion.div
      variants={fadeSlideUp}
      initial="hidden"
      animate="visible"
      transition={springGentle}
      className="overflow-hidden rounded-xl border border-border/60 bg-card shadow-(--shadow-warm-sm)"
    >
      <div className="flex items-center gap-2 px-4 py-2.5">
        <Map className="size-4 text-role-local-guide" />
        <span className="text-sm font-bold font-heading text-card-foreground">Map View</span>
      </div>

      <AnimatePresence mode="wait">
        {mapError && (
          <motion.div
            key="map-error"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-2 flex items-center gap-2 rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent-foreground"
          >
            <AlertTriangle className="size-4 shrink-0" />
            {mapError}
          </motion.div>
        )}
      </AnimatePresence>

      {isLoading && <MapSkeleton />}

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoading ? 0 : 1 }}
        transition={{ duration: 0.4 }}
      >
        <div
          ref={containerRef}
          className="h-64 sm:h-72 md:h-80 w-full bg-muted"
          style={isLoading ? { position: "absolute", visibility: "hidden" } : undefined}
        />
      </motion.div>
    </motion.div>
  );
}
