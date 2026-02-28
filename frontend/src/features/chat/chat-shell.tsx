"use client";

import { SyntheticEvent, useEffect, useRef, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { Role } from "@/features/chat/types";
import { MapCanvas } from "@/features/recommendations/map-canvas";
import { RecommendationList } from "@/features/recommendations/recommendation-list";
import type { RecommendationResponse } from "@/features/recommendations/types";
import { postChatMessage } from "@/lib/api/chat";
import { postRecommendations } from "@/lib/api/recommendations";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
};

const ROLE_OPTIONS: Role[] = ["companion", "local_guide", "study_guide"];

const ROLE_LABELS: Record<Role, string> = {
  companion: "Companion",
  local_guide: "Local Guide",
  study_guide: "Study Guide",
};

const ROLE_DESCRIPTIONS: Record<Role, string> = {
  companion: "Share how you feel and get supportive daily companionship.",
  local_guide: "Ask about places, routes, neighborhoods, and local options.",
  study_guide: "Plan study sessions, break down topics, and review concepts.",
};

const ROLE_EMPTY_STATE: Record<Role, string> = {
  companion: "Start by sharing how you are feeling today.",
  local_guide: "Tell me what area or activity you want to explore.",
  study_guide: "Share what you want to study and your timeline.",
};

const HONG_KONG_FALLBACK_COORDINATES = {
  latitude: 22.3193,
  longitude: 114.1694,
};
const GOOGLE_MAPS_BROWSER_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

type Coordinates = {
  latitude: number;
  longitude: number;
};

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
      (position) => {
        if (settled) {
          return;
        }
        settled = true;
        window.clearTimeout(timer);
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      () => {
        if (settled) {
          return;
        }
        settled = true;
        window.clearTimeout(timer);
        resolve(null);
      },
      {
        enableHighAccuracy: false,
        timeout: timeoutMs,
        maximumAge: 5 * 60 * 1000,
      },
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
  return {
    companion: [],
    local_guide: [],
    study_guide: [],
  };
}

export function ChatShell() {
  const userId = "demo-user";
  const [activeRole, setActiveRole] = useState<Role>("companion");
  const threadIdRef = useRef<Record<Role, string>>(buildInitialThreadMap(userId));
  const [messagesByRole, setMessagesByRole] =
    useState<Record<Role, ChatMessage[]>>(buildInitialMessageMap());
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [recommendationResponse, setRecommendationResponse] =
    useState<RecommendationResponse | null>(null);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [isRecommendationLoading, setIsRecommendationLoading] = useState(false);
  const activeMessages = messagesByRole[activeRole];
  const activeRecommendations = recommendationResponse?.recommendations ?? [];
  const recommendationCenter =
    activeRecommendations[0]?.location ?? coordinates ?? HONG_KONG_FALLBACK_COORDINATES;

  useEffect(() => {
    let active = true;

    async function resolveCoordinates() {
      const browserCoordinates = await getBrowserCoordinates();
      if (!active) {
        return;
      }
      setCoordinates(browserCoordinates ?? HONG_KONG_FALLBACK_COORDINATES);
    }

    void resolveCoordinates();
    return () => {
      active = false;
    };
  }, []);

  const handleRoleChange = (_event: SyntheticEvent, nextRole: Role) => {
    setActiveRole(nextRole);
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSubmitting) {
      return;
    }

    const roleAtSend = activeRole;
    const threadIdAtSend = threadIdRef.current[roleAtSend];
    setError(null);
    setInput("");
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: trimmed,
    };
    setMessagesByRole((previous) => ({
      ...previous,
      [roleAtSend]: [...previous[roleAtSend], userMessage],
    }));
    setIsSubmitting(true);
    let recommendationPromise: Promise<RecommendationResponse> | null = null;
    if (roleAtSend === "local_guide") {
      setRecommendationError(null);
      setIsRecommendationLoading(true);
      const requestCoordinates = coordinates ?? HONG_KONG_FALLBACK_COORDINATES;
      recommendationPromise = postRecommendations({
        user_id: userId,
        role: roleAtSend,
        query: trimmed,
        latitude: requestCoordinates.latitude,
        longitude: requestCoordinates.longitude,
        max_results: 5,
        travel_mode: "walking",
      });
    }

    try {
      const response = await postChatMessage({
        user_id: userId,
        role: roleAtSend,
        thread_id: threadIdAtSend,
        message: trimmed,
      });
      const assistantMessage: ChatMessage = {
        id: response.request_id,
        role: "assistant",
        text: response.reply,
      };
      setMessagesByRole((previous) => ({
        ...previous,
        [roleAtSend]: [...previous[roleAtSend], assistantMessage],
      }));
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "Unable to send message.");
    } finally {
      setIsSubmitting(false);
    }

    if (recommendationPromise) {
      try {
        const recommendationPayload = await recommendationPromise;
        setRecommendationResponse(recommendationPayload);
      } catch (recommendationRequestError) {
        setRecommendationResponse(null);
        setRecommendationError(
          recommendationRequestError instanceof Error
            ? recommendationRequestError.message
            : "Unable to load local recommendations.",
        );
      } finally {
        setIsRecommendationLoading(false);
      }
    }
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>
        CompanionHK Chat
      </Typography>
      <Typography sx={{ color: "text.secondary" }}>
        Choose a role space to switch context between companionship, local guidance, and study help.
      </Typography>
      <Tabs
        value={activeRole}
        onChange={handleRoleChange}
        variant="fullWidth"
        aria-label="Role spaces"
      >
        {ROLE_OPTIONS.map((roleOption) => (
          <Tab key={roleOption} value={roleOption} label={ROLE_LABELS[roleOption]} />
        ))}
      </Tabs>
      <Typography sx={{ color: "text.secondary" }}>{ROLE_DESCRIPTIONS[activeRole]}</Typography>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper
        variant="outlined"
        sx={{
          p: 2,
          borderRadius: 3,
          minHeight: 320,
          display: "flex",
          flexDirection: "column",
          gap: 1.25,
        }}
      >
        {activeMessages.length === 0 && (
          <Typography sx={{ color: "text.secondary" }}>{ROLE_EMPTY_STATE[activeRole]}</Typography>
        )}
        {activeMessages.map((message) => (
          <Box
            key={message.id}
            sx={{
              maxWidth: "85%",
              alignSelf: message.role === "user" ? "flex-end" : "flex-start",
              bgcolor: message.role === "user" ? "primary.main" : "grey.100",
              color: message.role === "user" ? "primary.contrastText" : "text.primary",
              px: 1.5,
              py: 1,
              borderRadius: 2,
            }}
          >
            <Typography>{message.text}</Typography>
          </Box>
        ))}
      </Paper>

      {activeRole === "local_guide" && (
        <Stack spacing={1.5}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Live Local Guide Context
          </Typography>
          {recommendationResponse && (
            <Typography sx={{ color: "text.secondary" }}>
              Weather context: {recommendationResponse.context.weather_condition}
              {recommendationResponse.context.temperature_c !== null
                ? ` (${recommendationResponse.context.temperature_c.toFixed(1)} deg C)`
                : ""}
            </Typography>
          )}
          {recommendationError && <Alert severity="warning">{recommendationError}</Alert>}
          {isRecommendationLoading && (
            <Typography sx={{ color: "text.secondary" }}>
              Fetching local recommendations...
            </Typography>
          )}
          {!isRecommendationLoading &&
            !recommendationError &&
            activeRecommendations.length === 0 && (
              <Typography sx={{ color: "text.secondary" }}>
                Send a Local Guide message to see ranked nearby places and map markers.
              </Typography>
            )}
          {activeRecommendations.length > 0 && (
            <>
              <MapCanvas
                apiKey={GOOGLE_MAPS_BROWSER_API_KEY}
                center={recommendationCenter}
                recommendations={activeRecommendations}
              />
              <RecommendationList recommendations={activeRecommendations} />
            </>
          )}
        </Stack>
      )}

      <Stack direction="row" spacing={1}>
        <TextField
          fullWidth
          label="Message input"
          value={input}
          disabled={isSubmitting}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSend();
            }
          }}
        />
        <Button
          variant="contained"
          onClick={() => void handleSend()}
          disabled={isSubmitting || input.trim().length === 0}
        >
          Send
        </Button>
      </Stack>
    </Stack>
  );
}
