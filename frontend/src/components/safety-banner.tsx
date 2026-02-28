"use client";

import { HandHeart, Phone, X } from "lucide-react";

const CRISIS_RESOURCES = [
  { name: "The Samaritans Hong Kong", number: "2896 0000" },
  { name: "Suicide Prevention Services", number: "2382 0000" },
  { name: "The Samaritan Befrienders HK", number: "2389 2222" },
  { name: "Emergency Services", number: "999" },
];

interface SafetyBannerProps {
  onDismiss?: () => void;
}

export function SafetyBanner({ onDismiss }: SafetyBannerProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-safety-border bg-safety-bg shadow-(--shadow-warm-md)">
      <div className="flex flex-col gap-3 px-5 py-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-full bg-safety-border/20">
              <HandHeart className="size-5 text-safety-text" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-heading text-safety-text">You are not alone</h3>
              <p className="text-xs text-safety-text/70">
                If you or someone you know needs support, these resources can help.
              </p>
            </div>
          </div>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="mt-0.5 flex size-6 items-center justify-center rounded-full text-safety-text/50 transition-colors hover:bg-safety-border/20 hover:text-safety-text cursor-pointer"
              aria-label="Dismiss"
            >
              <X className="size-4" />
            </button>
          )}
        </div>

        {/* Resources */}
        <div className="grid gap-2 sm:grid-cols-2">
          {CRISIS_RESOURCES.map((res) => (
            <a
              key={res.number}
              href={`tel:${res.number.replace(/\s/g, "")}`}
              className="flex items-center gap-2.5 rounded-xl bg-safety-border/10 px-3 py-2.5 transition-colors hover:bg-safety-border/20"
            >
              <Phone className="size-4 shrink-0 text-safety-text/60" />
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-safety-text/80">{res.name}</p>
                <p className="text-sm font-bold font-heading text-safety-text">{res.number}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
