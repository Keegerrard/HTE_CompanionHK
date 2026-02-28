import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatShell } from "@/features/chat/chat-shell";
import * as chatApi from "@/lib/api/chat";
import * as recommendationApi from "@/lib/api/recommendations";

vi.mock("@/lib/api/chat", () => ({
  postChatMessage: vi.fn(),
}));

vi.mock("@/lib/api/recommendations", () => ({
  postRecommendations: vi.fn(),
}));

describe("recommendation integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(chatApi.postChatMessage).mockResolvedValue({
      request_id: "local-guide-reply",
      thread_id: "demo-user-local_guide-thread",
      runtime: "simple",
      provider: "mock",
      reply: "Here are practical options for your route.",
      safety: {
        risk_level: "low",
        show_crisis_banner: false,
      },
    });
    vi.mocked(recommendationApi.postRecommendations).mockResolvedValue({
      request_id: "recommendation-request-1",
      recommendations: [
        {
          place_id: "place-1",
          name: "Harbour Cafe",
          address: "Tsim Sha Tsui, Hong Kong",
          rating: 4.6,
          user_ratings_total: 812,
          types: ["cafe", "food"],
          location: { latitude: 22.296, longitude: 114.172 },
          photo_url: null,
          maps_uri: "https://maps.google.com",
          distance_text: "1.2 km",
          duration_text: "16 mins",
          fit_score: 0.85,
          rationale: "Good review quality and close distance for your route.",
        },
        {
          place_id: "place-2",
          name: "Waterfront Park",
          address: "Tsim Sha Tsui, Hong Kong",
          rating: 4.4,
          user_ratings_total: 501,
          types: ["park", "point_of_interest"],
          location: { latitude: 22.294, longitude: 114.171 },
          photo_url: null,
          maps_uri: null,
          distance_text: "1.6 km",
          duration_text: "20 mins",
          fit_score: 0.74,
          rationale: "Outdoor option with practical travel time.",
        },
        {
          place_id: "place-3",
          name: "City Museum",
          address: "Tsim Sha Tsui, Hong Kong",
          rating: 4.2,
          user_ratings_total: 388,
          types: ["museum", "point_of_interest"],
          location: { latitude: 22.293, longitude: 114.173 },
          photo_url: null,
          maps_uri: null,
          distance_text: "2.0 km",
          duration_text: "24 mins",
          fit_score: 0.7,
          rationale: "Indoor alternative in case weather shifts.",
        },
      ],
      context: {
        weather_condition: "cloudy",
        temperature_c: 26,
        degraded: false,
        fallback_reason: null,
      },
    });
  });

  it("renders recommendation cards in local guide flow", async () => {
    render(<ChatShell />);
    fireEvent.click(screen.getByRole("tab", { name: "Local Guide" }));
    fireEvent.change(screen.getByLabelText("Message input"), {
      target: { value: "Plan a route with a cafe and a nearby park." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(recommendationApi.postRecommendations).toHaveBeenCalledTimes(1);
    });
    expect(await screen.findByText("Local Recommendations")).toBeInTheDocument();
    expect(await screen.findByText("Harbour Cafe")).toBeInTheDocument();
    expect(screen.getByText("Weather context: cloudy (26.0 deg C)")).toBeInTheDocument();
  });
});
