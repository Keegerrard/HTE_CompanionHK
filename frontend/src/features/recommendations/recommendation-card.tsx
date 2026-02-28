import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import Chip from "@mui/material/Chip";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { RecommendationItem } from "@/features/recommendations/types";

interface RecommendationCardProps {
  recommendation: RecommendationItem;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  return (
    <Card variant="outlined" sx={{ borderRadius: 3 }}>
      {recommendation.photo_url && (
        <CardMedia
          component="img"
          sx={{ height: 160 }}
          image={recommendation.photo_url}
          alt={recommendation.name}
        />
      )}
      <CardContent>
        <Stack spacing={1.25}>
          <Stack
            direction="row"
            spacing={1}
            useFlexGap
            sx={{ justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap" }}
          >
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {recommendation.name}
            </Typography>
            <Chip
              label={`Fit ${(recommendation.fit_score * 100).toFixed(0)}%`}
              color="primary"
              size="small"
            />
          </Stack>

          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            {recommendation.address}
          </Typography>

          <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
            {recommendation.rating !== null && (
              <Chip
                size="small"
                variant="outlined"
                label={`Rating ${recommendation.rating.toFixed(1)}`}
              />
            )}
            {recommendation.user_ratings_total !== null && (
              <Chip
                size="small"
                variant="outlined"
                label={`${recommendation.user_ratings_total.toLocaleString()} reviews`}
              />
            )}
            {recommendation.distance_text && (
              <Chip size="small" variant="outlined" label={recommendation.distance_text} />
            )}
            {recommendation.duration_text && (
              <Chip size="small" variant="outlined" label={recommendation.duration_text} />
            )}
          </Stack>

          <Typography variant="body2">{recommendation.rationale}</Typography>

          {recommendation.maps_uri && (
            <Link href={recommendation.maps_uri} target="_blank" rel="noopener noreferrer">
              Open in Google Maps
            </Link>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
