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
vi.mock("@/components/weather-provider", () => ({
  useWeather: () => ({ condition: "unknown", isDay: true, temperatureC: null }),
  WeatherProvider: ({ children }: { children: React.ReactNode }) => children,
}));

describe("ChatShell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(recommendationApi.postRecommendations).mockResolvedValue({
      request_id: "recommendation-request",
      recommendations: [],
      context: {
        weather_condition: "unknown",
        temperature_c: null,
        degraded: false,
        fallback_reason: null,
      },
    });
  });

  it("submits a message and renders the assistant response", async () => {
    vi.mocked(chatApi.postChatMessage).mockResolvedValue({
      request_id: "test-request",
      thread_id: "demo-user-companion-thread",
      runtime: "simple",
      provider: "mock",
      reply: "I am here with you.",
      safety: {
        risk_level: "low",
        show_crisis_banner: false,
      },
    });

    render(<ChatShell />);
    fireEvent.change(screen.getByLabelText("Message input"), {
      target: { value: "Today feels difficult." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(chatApi.postChatMessage).toHaveBeenCalledWith({
        user_id: "demo-user",
        role: "companion",
        thread_id: "demo-user-companion-thread",
        message: "Today feels difficult.",
      });
    });

    expect(await screen.findByText("I am here with you.")).toBeInTheDocument();
  });

  it("uses local guide role and role-scoped thread after switching tabs", async () => {
    vi.mocked(chatApi.postChatMessage).mockResolvedValue({
      request_id: "local-guide-request",
      thread_id: "demo-user-local_guide-thread",
      runtime: "simple",
      provider: "mock",
      reply: "Try Sheung Wan and PMQ for this route.",
      safety: {
        risk_level: "low",
        show_crisis_banner: false,
      },
    });

    render(<ChatShell />);
    fireEvent.click(screen.getByRole("button", { name: /Local Guide/i }));
    fireEvent.change(screen.getByLabelText("Message input"), {
      target: { value: "I want a half-day walk plan." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(chatApi.postChatMessage).toHaveBeenCalledWith({
        user_id: "demo-user",
        role: "local_guide",
        thread_id: "demo-user-local_guide-thread",
        message: "I want a half-day walk plan.",
      });
    });
    await waitFor(() => {
      expect(recommendationApi.postRecommendations).toHaveBeenCalledWith({
        user_id: "demo-user",
        role: "local_guide",
        query: "I want a half-day walk plan.",
        latitude: 22.3193,
        longitude: 114.1694,
        max_results: 5,
        travel_mode: "walking",
      });
    });
  });

  it("keeps message history isolated across role spaces", async () => {
    vi.mocked(chatApi.postChatMessage)
      .mockResolvedValueOnce({
        request_id: "companion-request",
        thread_id: "demo-user-companion-thread",
        runtime: "simple",
        provider: "mock",
        reply: "Companion space reply.",
        safety: {
          risk_level: "low",
          show_crisis_banner: false,
        },
      })
      .mockResolvedValueOnce({
        request_id: "local-guide-request",
        thread_id: "demo-user-local_guide-thread",
        runtime: "simple",
        provider: "mock",
        reply: "Local guide space reply.",
        safety: {
          risk_level: "low",
          show_crisis_banner: false,
        },
      });

    render(<ChatShell />);

    fireEvent.change(screen.getByLabelText("Message input"), {
      target: { value: "I feel nervous about tomorrow." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText("Companion space reply.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Local Guide/i }));
    await waitFor(() => {
      expect(screen.queryByText("Companion space reply.")).not.toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Message input"), {
      target: { value: "Plan a quick evening route." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText("Local guide space reply.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Companion/i }));
    expect(await screen.findByText("Companion space reply.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText("Local guide space reply.")).not.toBeInTheDocument();
    });
  });
});
