"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Heart, MapPin, BookOpen, Send, Cloud, Sun, CloudRain, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SafetyBanner } from "@/components/safety-banner";
import { useWeather } from "@/components/weather-provider";
import { MapCanvas } from "@/features/recommendations/map-canvas";
import { RecommendationList } from "@/features/recommendations/recommendation-list";
import type { RecommendationResponse } from "@/features/recommendations/types";
import type { Role } from "@/features/chat/types";
import { postChatMessage } from "@/lib/api/chat";
import { postRecommendations } from "@/lib/api/recommendations";
import {
  spring,
  springGentle,
  springBouncy,
  fadeSlideUp,
  fadeScale,
  bubbleIn,
  staggerContainer,
} from "@/lib/motion-config";
import { cn } from "@/lib/utils";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: number;
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
const MAX_TEXTAREA_HEIGHT = 120;

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

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function roleColor(role: Role): string {
  return `var(--role-${role.replace("_", "-")})`;
}

/* ─── WeatherPill ─── */

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
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={springGentle}
      className="flex items-center gap-1.5 rounded-full bg-card/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-(--shadow-warm-sm) glass glass-border"
    >
      <Icon className="size-3.5" />
      <span className="capitalize">{weather.condition.replace("_", " ")}</span>
      {temp && <span>{temp}</span>}
    </motion.div>
  );
}

/* ─── TypingIndicator ─── */

function TypingIndicator() {
  const dotVariants = {
    initial: { opacity: 0.3, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
  };

  return (
    <motion.div
      variants={bubbleIn}
      initial="hidden"
      animate="visible"
      className="flex items-center gap-1.5 self-start rounded-(--radius-bubble) rounded-bl-md bg-card px-4 py-3 shadow-(--shadow-warm-sm)"
    >
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="size-2 rounded-full bg-muted-foreground"
          variants={dotVariants}
          initial="initial"
          animate="animate"
          transition={{
            repeat: Infinity,
            repeatType: "reverse",
            duration: 0.5,
            delay: i * 0.15,
            ease: "easeInOut",
          }}
        />
      ))}
    </motion.div>
  );
}

/* ─── ChatBubble ─── */

interface ChatBubbleProps {
  msg: ChatMessage;
  activeRole: Role;
  showRoleIcon: boolean;
}

function ChatBubble({ msg, activeRole, showRoleIcon }: ChatBubbleProps) {
  const isUser = msg.role === "user";
  const RoleIcon = ROLE_META[activeRole].icon;

  return (
    <motion.div
      variants={bubbleIn}
      whileHover={{ scale: 1.005, transition: { duration: 0.15 } }}
      className={cn("max-w-[85%]", isUser ? "self-end" : "self-start")}
    >
      <div className="flex items-end gap-2">
        {!isUser && showRoleIcon && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={springBouncy}
            className="mb-1 flex size-7 shrink-0 items-center justify-center rounded-full"
            style={{
              backgroundColor: `color-mix(in srgb, ${roleColor(activeRole)} 15%, transparent)`,
            }}
          >
            <RoleIcon className="size-3.5" style={{ color: roleColor(activeRole) }} />
          </motion.div>
        )}
        {!isUser && !showRoleIcon && <div className="w-7 shrink-0" />}

        <div className="flex flex-col gap-0.5">
          <div
            className={cn(
              "px-4 py-2.5 text-[0.9375rem] leading-relaxed",
              isUser
                ? "rounded-(--radius-bubble) rounded-br-md bg-primary text-primary-foreground"
                : "rounded-(--radius-bubble) rounded-bl-md border-l-2 bg-card text-card-foreground shadow-(--shadow-warm-sm)",
            )}
            style={!isUser ? { borderLeftColor: roleColor(activeRole) } : undefined}
          >
            {msg.text}
          </div>
          <span
            className={cn(
              "text-[0.65rem] text-muted-foreground/50 select-none",
              isUser ? "text-right" : "text-left",
            )}
          >
            {formatTime(msg.timestamp)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

/* ─── ScrollToBottomFAB ─── */

function ScrollToBottomFAB({ onClick }: { onClick: () => void }) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 8, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.9 }}
      transition={spring}
      onClick={onClick}
      className="absolute bottom-2 left-1/2 z-10 flex -translate-x-1/2 items-center gap-1 rounded-full bg-card/90 px-3 py-1.5 text-xs font-medium text-muted-foreground shadow-(--shadow-warm-md) glass glass-border cursor-pointer hover:bg-card transition-colors"
      aria-label="Scroll to latest messages"
    >
      <ChevronDown className="size-3.5" />
      New messages
    </motion.button>
  );
}

/* ─── AutoGrowTextarea ─── */

interface AutoGrowTextareaProps {
  value: string;
  onChange: (value: string) => void;
  onKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  placeholder: string;
  disabled: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

function AutoGrowTextarea({
  value,
  onChange,
  onKeyDown,
  placeholder,
  disabled,
  textareaRef,
}: AutoGrowTextareaProps) {
  useLayoutEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0";
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  }, [value, textareaRef]);

  return (
    <textarea
      ref={textareaRef}
      aria-label="Message input"
      className={cn(
        "flex-1 resize-none rounded-xl border border-input bg-card px-3 py-2 text-base text-foreground placeholder:text-muted-foreground shadow-(--shadow-warm-sm) outline-none md:text-sm",
        "transition-[color,box-shadow,height] duration-150",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "disabled:pointer-events-none disabled:opacity-50",
      )}
      style={{ minHeight: 38, maxHeight: MAX_TEXTAREA_HEIGHT }}
      rows={1}
      placeholder={placeholder}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={onKeyDown}
    />
  );
}

/* ═══════════════════════════════════════════════════════════
   ChatShell — main component
   ═══════════════════════════════════════════════════════════ */

export function ChatShell() {
  const userId = "demo-user";
  const prefersReducedMotion = useReducedMotion();
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
  const [showScrollFAB, setShowScrollFAB] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth" });
    setShowScrollFAB(false);
  }, [prefersReducedMotion]);

  useEffect(() => {
    scrollToBottom();
  }, [activeMessages.length, isSubmitting, scrollToBottom]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, [activeRole]);

  useEffect(() => {
    const el = scrollAreaRef.current;
    if (!el) return;
    function handleScroll() {
      if (!el) return;
      const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      setShowScrollFAB(distFromBottom > 120);
    }
    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSubmitting) return;

    const roleAtSend = activeRole;
    const threadId = threadIdRef.current[roleAtSend];
    setError(null);
    setInput("");
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: trimmed,
      timestamp: Date.now(),
    };
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
      const assistantMsg: ChatMessage = {
        id: res.request_id,
        role: "assistant",
        text: res.reply,
        timestamp: Date.now(),
      };
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

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex min-h-dvh flex-col">
      {/* ─── Header ─── */}
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springGentle}
        className="relative flex items-center justify-between px-4 py-3 md:px-6 glass"
      >
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold font-heading text-foreground tracking-tight">
            港伴<span className="text-primary">AI</span>
          </span>
        </div>
        <WeatherPill />
        <div
          className="absolute inset-x-0 bottom-0 h-px"
          style={{
            background: `linear-gradient(90deg, transparent, ${roleColor(activeRole)}, transparent)`,
            opacity: 0.3,
          }}
        />
      </motion.header>

      {/* ─── Role Selector ─── */}
      <nav className="relative flex justify-center gap-2 px-4 pb-2 pt-1" aria-label="Role spaces">
        {ROLE_OPTIONS.map((role) => {
          const { label, icon: Icon } = ROLE_META[role];
          const isActive = role === activeRole;
          const color = roleColor(role);
          return (
            <motion.button
              key={role}
              onClick={() => setActiveRole(role)}
              whileTap={{ scale: 0.95 }}
              className={cn(
                "relative flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold cursor-pointer",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "transition-colors duration-200",
                isActive
                  ? "text-white"
                  : "bg-card text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
              style={isActive ? { backgroundColor: color } : undefined}
              aria-current={isActive ? "page" : undefined}
            >
              {isActive && (
                <motion.span
                  layoutId="role-pill"
                  className="absolute inset-0 rounded-full shadow-(--shadow-warm-md)"
                  style={{ backgroundColor: color }}
                  transition={spring}
                />
              )}
              <span className="relative z-10 flex items-center gap-1.5">
                <Icon className="size-4" />
                {label}
              </span>
            </motion.button>
          );
        })}
      </nav>

      {/* ─── Role Description ─── */}
      <div className="px-4 pb-2 text-center md:px-6">
        <AnimatePresence mode="wait">
          <motion.p
            key={activeRole}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2 }}
            className="text-sm text-muted-foreground"
          >
            {meta.description}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* ─── Safety Banner ─── */}
      <AnimatePresence>
        {showCrisisBanner && (
          <motion.div
            key="crisis-banner"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={springGentle}
            className="px-4 pb-2 md:px-6 overflow-hidden"
          >
            <SafetyBanner onDismiss={() => setShowCrisisBanner(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Chat Messages ─── */}
      <div className="relative mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 md:px-6">
        <ScrollArea className="flex-1 py-4" ref={scrollAreaRef}>
          <AnimatePresence mode="popLayout">
            <motion.div
              key={activeRole}
              variants={fadeScale}
              initial="hidden"
              animate="visible"
              exit="exit"
              transition={{ duration: 0.15 }}
              className="flex flex-col gap-3"
              role="log"
              aria-live="polite"
              aria-label={`${meta.label} conversation`}
            >
              {activeMessages.length === 0 && (
                <div className="flex flex-1 flex-col items-center justify-center py-16 text-center">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={springBouncy}
                  >
                    <meta.icon className="mb-4 size-12 text-muted-foreground/40 animate-float" />
                  </motion.div>
                  <motion.p
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, ...springGentle }}
                    className="text-base font-medium text-muted-foreground"
                  >
                    {meta.empty}
                  </motion.p>
                </div>
              )}

              {activeMessages.length > 0 && (
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                  className="flex flex-col gap-3"
                >
                  {activeMessages.map((msg, idx) => {
                    const prevMsg = activeMessages[idx - 1];
                    const showRoleIcon =
                      msg.role === "assistant" && (idx === 0 || prevMsg?.role !== "assistant");
                    return (
                      <ChatBubble
                        key={msg.id}
                        msg={msg}
                        activeRole={activeRole}
                        showRoleIcon={showRoleIcon}
                      />
                    );
                  })}
                </motion.div>
              )}

              <AnimatePresence>{isSubmitting && <TypingIndicator />}</AnimatePresence>
              <div ref={messagesEndRef} />
            </motion.div>
          </AnimatePresence>
        </ScrollArea>

        <AnimatePresence>
          {showScrollFAB && <ScrollToBottomFAB onClick={scrollToBottom} />}
        </AnimatePresence>

        <AnimatePresence>
          {error && (
            <motion.div
              variants={fadeSlideUp}
              initial="hidden"
              animate="visible"
              exit="exit"
              transition={spring}
              className="mb-2 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ─── Local Guide Recommendations ─── */}
      <AnimatePresence>
        {activeRole === "local_guide" && (
          <motion.div
            key="rec-panel"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={springGentle}
            className="mx-auto w-full max-w-2xl overflow-hidden px-4 pb-2 md:px-6"
          >
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
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Input Bar ─── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, ...springGentle }}
        className="sticky bottom-0 border-t border-border/60 bg-background/80 glass glass-border"
      >
        <div className="mx-auto flex max-w-2xl items-end gap-2 px-4 py-3 md:px-6">
          <AutoGrowTextarea
            textareaRef={textareaRef}
            placeholder={meta.empty}
            value={input}
            disabled={isSubmitting}
            onChange={setInput}
            onKeyDown={handleKeyDown}
          />
          <motion.div whileTap={{ scale: 0.9 }} transition={springBouncy}>
            <Button
              size="icon"
              className="rounded-xl shadow-(--shadow-warm-sm) transition-all duration-200 hover:shadow-(--shadow-warm-md)"
              onClick={() => void handleSend()}
              disabled={isSubmitting || input.trim().length === 0}
              style={{ backgroundColor: roleColor(activeRole) }}
            >
              <Send className="size-4 text-white" />
              <span className="sr-only">Send</span>
            </Button>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
