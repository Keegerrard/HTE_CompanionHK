import type { Role } from "@/features/chat/types";

export type TravelMode = "walking" | "transit" | "driving";

export interface RecommendationRequest {
  user_id: string;
  role: Role;
  query: string;
  latitude: number;
  longitude: number;
  max_results?: number;
  preference_tags?: string[];
  travel_mode?: TravelMode;
}

export interface RecommendationItem {
  place_id: string;
  name: string;
  address: string;
  rating: number | null;
  user_ratings_total: number | null;
  types: string[];
  location: {
    latitude: number;
    longitude: number;
  };
  photo_url: string | null;
  maps_uri: string | null;
  distance_text: string | null;
  duration_text: string | null;
  fit_score: number;
  rationale: string;
}

export interface RecommendationResponse {
  request_id: string;
  recommendations: RecommendationItem[];
  context: {
    weather_condition: string;
    temperature_c: number | null;
    degraded: boolean;
    fallback_reason: string | null;
  };
}
