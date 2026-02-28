"use client";

import { useEffect, useRef, useState } from "react";
import { Heart, MapPin, BookOpen, Send, Cloud, Sun, CloudRain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SafetyBanner } from "@/components/safety-banner";
import { useWeather } from "@/components/weather-provider";
import { MapCanvas } from "@/features/recommendations/map-canvas";
import { RecommendationList } from "@/features/recommendations/recommendation-list";
import type { RecommendationResponse } from "@/features/recommendations/types";
import type { Role } from "@/features/chat/types";
import { postChatMessage } from "@/lib/api/chat";
import { postRecommendations } from "@/lib/api/recommendations";
import { cn } from "@/lib/utils";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

const ROLE_OPTIONS: Role[] = ["companion", "local_guide", "study_guide"];

const ROLE_META: Record<
  Role,
  { label: string; icon: typeof Heart; description: string; empty: string }
> = {
  companion: {
    label: "Companion",
    icon: Heart,
    description: "Share how you feel and get supportive daily companionship.",
    empty: "Start by sharing how you are feeling today.",
  },
  local_guide: {
    label: "Local Guide",
    icon: MapPin,
    description: "Ask about places, routes, neighborhoods, and local options.",
    empty: "Tell me what area or activity you want to explore.",
  },
  study_guide: {
    label: "Study Guide",
    icon: BookOpen,
    description: "Plan study sessions, break down topics, and review concepts.",
    empty: "Share what you want to study and your timeline.",
  },
};

const HONG_KONG_FALLBACK = { latitude: 22.3193, longitude: 114.1694 };
const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

type Coordinates = { latitude: number; longitude: number };

function getBrowserCoordinates(timeoutMs = 2500): Promise<Coordinates | null> {
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

function buildInitialThreadMap(userId: string): Record<Role, string> {
  return {
    companion: `${userId}-companion-thread`,
    local_guide: `${userId}-local_guide-thread`,
    study_guide: `${userId}-study_guide-thread`,
  };
}

function buildInitialMessageMap(): Record<Role, ChatMessage[]> {
  return { companion: [], local_guide: [], study_guide: [] };
}

function WeatherPill() {
  const weather = useWeather();
  if (weather.condition === "unknown") return null;

  const icons: Record<string, typeof Sun> = {
    clear: Sun,
    rain: CloudRain,
    drizzle: CloudRain,
    thunderstorm: CloudRain,
    cloudy: Cloud,
    partly_cloudy: Cloud,
    fog: Cloud,
    snow: Cloud,
  };
  const Icon = icons[weather.condition] ?? Cloud;
  const temp = weather.temperatureC != null ? `${weather.temperatureC.toFixed(0)}°C` : "";

  return (
    <div className="flex items-center gap-1.5 rounded-full bg-card/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-(--shadow-warm-sm) backdrop-blur-sm">
      <Icon className="size-3.5" />
      <span className="capitalize">{weather.condition.replace("_", " ")}</span>
      {temp && <span>{temp}</span>}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 self-start rounded-(--radius-bubble) rounded-bl-md bg-card px-4 py-3 shadow-(--shadow-warm-sm)">
      <span className="typing-dot size-2 rounded-full bg-muted-foreground" />
      <span className="typing-dot size-2 rounded-full bg-muted-foreground" />
      <span className="typing-dot size-2 rounded-full bg-muted-foreground" />
    </div>
  );
}

export function ChatShell() {
  const userId = "demo-user";
  const [activeRole, setActiveRole] = useState<Role>("companion");
  const threadIdRef = useRef(buildInitialThreadMap(userId));
  const [messagesByRole, setMessagesByRole] =
    useState<Record<Role, ChatMessage[]>>(buildInitialMessageMap());
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCrisisBanner, setShowCrisisBanner] = useState(false);
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [recommendationResponse, setRecommendationResponse] =
    useState<RecommendationResponse | null>(null);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [isRecommendationLoading, setIsRecommendationLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeMessages = messagesByRole[activeRole];
  const activeRecommendations = recommendationResponse?.recommendations ?? [];
  const recommendationCenter =
    activeRecommendations[0]?.location ?? coordinates ?? HONG_KONG_FALLBACK;
  const meta = ROLE_META[activeRole];

  useEffect(() => {
    let active = true;
    async function resolve() {
      const coords = await getBrowserCoordinates();
      if (active) setCoordinates(coords ?? HONG_KONG_FALLBACK);
    }
    void resolve();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeMessages.length, isSubmitting]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSubmitting) return;

    const roleAtSend = activeRole;
    const threadId = threadIdRef.current[roleAtSend];
    setError(null);
    setInput("");
    const userMsg: ChatMessage = { id: `user-${Date.now()}`, role: "user", text: trimmed };
    setMessagesByRole((prev) => ({ ...prev, [roleAtSend]: [...prev[roleAtSend], userMsg] }));
    setIsSubmitting(true);

    let recPromise: Promise<RecommendationResponse> | null = null;
    if (roleAtSend === "local_guide") {
      setRecommendationError(null);
      setIsRecommendationLoading(true);
      const loc = coordinates ?? HONG_KONG_FALLBACK;
      recPromise = postRecommendations({
        user_id: userId,
        role: roleAtSend,
        query: trimmed,
        latitude: loc.latitude,
        longitude: loc.longitude,
        max_results: 5,
        travel_mode: "walking",
      });
    }

    try {
      const res = await postChatMessage({
        user_id: userId,
        role: roleAtSend,
        thread_id: threadId,
        message: trimmed,
      });
      const assistantMsg: ChatMessage = { id: res.request_id, role: "assistant", text: res.reply };
      setMessagesByRole((prev) => ({ ...prev, [roleAtSend]: [...prev[roleAtSend], assistantMsg] }));
      if (res.safety.show_crisis_banner) setShowCrisisBanner(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to send message.");
    } finally {
      setIsSubmitting(false);
    }

    if (recPromise) {
      try {
        setRecommendationResponse(await recPromise);
      } catch (e) {
        setRecommendationResponse(null);
        setRecommendationError(e instanceof Error ? e.message : "Unable to load recommendations.");
      } finally {
        setIsRecommendationLoading(false);
      }
    }
  };

  return (
    <div className="flex min-h-dvh flex-col">
      {/* ─── Header ─── */}
      <header className="flex items-center justify-between px-4 py-3 md:px-6">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold font-heading text-foreground tracking-tight">
            港伴<span className="text-primary">AI</span>
          </span>
        </div>
        <WeatherPill />
      </header>

      {/* ─── Role Selector ─── */}
      <nav className="flex justify-center gap-2 px-4 pb-2" aria-label="Role spaces">
        {ROLE_OPTIONS.map((role) => {
          const { label, icon: Icon } = ROLE_META[role];
          const isActive = role === activeRole;
          const roleColor = `var(--role-${role.replace("_", "-")})`;
          return (
            <button
              key={role}
              onClick={() => setActiveRole(role)}
              className={cn(
                "flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-all duration-200 cursor-pointer",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                isActive
                  ? "text-white shadow-(--shadow-warm-md)"
                  : "bg-card text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
              style={isActive ? { backgroundColor: roleColor } : undefined}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="size-4" />
              {label}
            </button>
          );
        })}
      </nav>

      {/* ─── Role Description ─── */}
      <div className="px-4 pb-2 text-center md:px-6">
        <p className="text-sm text-muted-foreground">{meta.description}</p>
      </div>

      {/* ─── Safety Banner ─── */}
      {showCrisisBanner && (
        <div className="px-4 pb-2 md:px-6">
          <SafetyBanner onDismiss={() => setShowCrisisBanner(false)} />
        </div>
      )}

      {/* ─── Chat Messages ─── */}
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 md:px-6">
        <ScrollArea className="flex-1 py-4">
          <div className="flex flex-col gap-3">
            {activeMessages.length === 0 && (
              <div className="flex flex-1 flex-col items-center justify-center py-16 text-center">
                <meta.icon className="mb-4 size-12 text-muted-foreground/40" />
                <p className="text-base font-medium text-muted-foreground">{meta.empty}</p>
              </div>
            )}

            {activeMessages.map((msg) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={msg.id}
                  className={cn(
                    "animate-bubble-in max-w-[85%]",
                    isUser ? "self-end" : "self-start",
                  )}
                >
                  <div
                    className={cn(
                      "px-4 py-2.5 text-[0.9375rem] leading-relaxed",
                      isUser
                        ? "rounded-(--radius-bubble) rounded-br-md bg-primary text-primary-foreground"
                        : "rounded-(--radius-bubble) rounded-bl-md bg-card text-card-foreground shadow-(--shadow-warm-sm)",
                    )}
                  >
                    {msg.text}
                  </div>
                </div>
              );
            })}

            {isSubmitting && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* ─── Error ─── */}
        {error && (
          <div className="mb-2 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
            {error}
          </div>
        )}
      </div>

      {/* ─── Local Guide Recommendations ─── */}
      {activeRole === "local_guide" && (
        <div className="mx-auto w-full max-w-2xl px-4 pb-2 md:px-6">
          {recommendationError && (
            <div className="mb-2 rounded-xl border border-accent/30 bg-accent/10 px-4 py-2.5 text-sm text-accent-foreground">
              {recommendationError}
            </div>
          )}
          {isRecommendationLoading && (
            <p className="mb-2 text-sm text-muted-foreground animate-pulse-gentle">
              Fetching local recommendations...
            </p>
          )}
          {!isRecommendationLoading &&
            !recommendationError &&
            activeRecommendations.length === 0 &&
            activeMessages.length > 0 && (
              <p className="mb-2 text-sm text-muted-foreground">
                Send a message to see ranked nearby places and map markers.
              </p>
            )}
          {activeRecommendations.length > 0 && (
            <div className="flex flex-col gap-3 pb-2">
              {recommendationResponse && (
                <p className="text-xs text-muted-foreground">
                  Weather: {recommendationResponse.context.weather_condition}
                  {recommendationResponse.context.temperature_c != null
                    ? ` · ${recommendationResponse.context.temperature_c.toFixed(1)}°C`
                    : ""}
                </p>
              )}
              <MapCanvas
                apiKey={GOOGLE_MAPS_API_KEY}
                center={recommendationCenter}
                recommendations={activeRecommendations}
              />
              <RecommendationList recommendations={activeRecommendations} />
            </div>
          )}
        </div>
      )}

      {/* ─── Input Bar ─── */}
      <div className="sticky bottom-0 border-t border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-2xl items-center gap-2 px-4 py-3 md:px-6">
          <Input
            aria-label="Message input"
            className="flex-1 rounded-xl border-input bg-card text-foreground placeholder:text-muted-foreground shadow-(--shadow-warm-sm) focus-visible:ring-primary/30"
            placeholder={meta.empty}
            value={input}
            disabled={isSubmitting}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void handleSend();
              }
            }}
          />
          <Button
            size="icon"
            className="rounded-xl shadow-(--shadow-warm-sm) transition-all duration-200 hover:shadow-(--shadow-warm-md)"
            onClick={() => void handleSend()}
            disabled={isSubmitting || input.trim().length === 0}
            style={{ backgroundColor: `var(--role-${activeRole.replace("_", "-")})` }}
          >
            <Send className="size-4 text-white" />
            <span className="sr-only">Send</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
