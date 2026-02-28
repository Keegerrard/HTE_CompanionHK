"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { ExternalLink, MapPin, Star } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { bubbleIn } from "@/lib/motion-config";
import type { RecommendationItem } from "@/features/recommendations/types";

interface RecommendationCardProps {
  recommendation: RecommendationItem;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  return (
    <motion.div
      variants={bubbleIn}
      whileHover={{ y: -2, scale: 1.01, transition: { duration: 0.2 } }}
    >
      <Card className="overflow-hidden border-border/60 bg-card shadow-(--shadow-warm-sm) transition-shadow duration-200 hover:shadow-(--shadow-warm-md)">
        {recommendation.photo_url && (
          <div className="relative h-40 w-full overflow-hidden">
            <Image
              src={recommendation.photo_url}
              alt={recommendation.name}
              fill
              className="object-cover transition-transform duration-500 hover:scale-105"
              unoptimized
            />
          </div>
        )}
        <CardContent className="flex flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-base font-bold font-heading leading-snug text-card-foreground">
              {recommendation.name}
            </h3>
            <Badge className="shrink-0 rounded-full bg-primary/15 text-primary font-semibold text-xs px-2.5 py-0.5">
              {(recommendation.fit_score * 100).toFixed(0)}% fit
            </Badge>
          </div>

          <p className="flex items-start gap-1.5 text-sm text-muted-foreground">
            <MapPin className="mt-0.5 size-3.5 shrink-0" />
            {recommendation.address}
          </p>

          <div className="flex flex-wrap gap-1.5">
            {recommendation.rating != null && (
              <Badge
                variant="outline"
                className="gap-1 rounded-full border-border/60 text-xs font-medium"
              >
                <Star className="size-3 fill-accent text-accent" />
                {recommendation.rating.toFixed(1)}
              </Badge>
            )}
            {recommendation.user_ratings_total != null && (
              <Badge
                variant="outline"
                className="rounded-full border-border/60 text-xs font-medium"
              >
                {recommendation.user_ratings_total.toLocaleString()} reviews
              </Badge>
            )}
            {recommendation.distance_text && (
              <Badge
                variant="outline"
                className="rounded-full border-border/60 text-xs font-medium"
              >
                {recommendation.distance_text}
              </Badge>
            )}
            {recommendation.duration_text && (
              <Badge
                variant="outline"
                className="rounded-full border-border/60 text-xs font-medium"
              >
                {recommendation.duration_text}
              </Badge>
            )}
          </div>

          <p className="text-sm leading-relaxed text-muted-foreground">
            {recommendation.rationale}
          </p>

          {recommendation.maps_uri && (
            <a
              href={recommendation.maps_uri}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              <ExternalLink className="size-3.5" />
              Open in Google Maps
            </a>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
