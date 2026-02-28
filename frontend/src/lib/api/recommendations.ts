import type {
  RecommendationRequest,
  RecommendationResponse,
} from "@/features/recommendations/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function postRecommendations(
  payload: RecommendationRequest,
): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE_URL}/recommendations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Recommendation request failed with status ${response.status}`);
  }

  return (await response.json()) as RecommendationResponse;
}
