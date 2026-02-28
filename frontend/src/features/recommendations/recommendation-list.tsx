import { MapPin } from "lucide-react";
import type { RecommendationItem } from "@/features/recommendations/types";
import { RecommendationCard } from "@/features/recommendations/recommendation-card";

interface RecommendationListProps {
  recommendations: RecommendationItem[];
}

export function RecommendationList({ recommendations }: RecommendationListProps) {
  if (recommendations.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <h2 className="flex items-center gap-2 text-base font-bold font-heading text-foreground">
        <MapPin className="size-4 text-role-local-guide" />
        Local Recommendations
      </h2>
      {recommendations.map((rec) => (
        <RecommendationCard key={rec.place_id} recommendation={rec} />
      ))}
    </div>
  );
}
