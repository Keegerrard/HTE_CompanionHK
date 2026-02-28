import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { RecommendationItem } from "@/features/recommendations/types";
import { RecommendationCard } from "@/features/recommendations/recommendation-card";

interface RecommendationListProps {
  recommendations: RecommendationItem[];
}

export function RecommendationList({ recommendations }: RecommendationListProps) {
  if (recommendations.length === 0) {
    return null;
  }

  return (
    <Stack spacing={1.5}>
      <Typography variant="h6" sx={{ fontWeight: 700 }}>
        Local Recommendations
      </Typography>
      {recommendations.map((recommendation) => (
        <RecommendationCard key={recommendation.place_id} recommendation={recommendation} />
      ))}
    </Stack>
  );
}
