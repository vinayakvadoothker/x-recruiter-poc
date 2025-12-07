'use client';

import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api';
import { Sparkles, Loader2 } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ElonScoreBadgeProps {
  candidateId: string;
  positionId?: string;
  showLabel?: boolean;
}

export function ElonScoreBadge({ candidateId, positionId, showLabel = true }: ElonScoreBadgeProps) {
  const { data: scoreData, isLoading } = useQuery({
    queryKey: ['elonScore', candidateId, positionId],
    queryFn: () => apiClient.getElonScore(candidateId, positionId),
    enabled: !!candidateId,
    retry: false,
  });

  if (isLoading) {
    return (
      <Badge variant="outline" className="gap-1">
        <Loader2 className="h-3 w-3 animate-spin" />
        {showLabel && 'ELON'}
      </Badge>
    );
  }

  if (!scoreData) {
    return null;
  }

  const score = scoreData.elon_score || scoreData.exceptional_score || 0;
  const scorePercent = (score * 100).toFixed(1);

  // Color based on score
  let variant: "default" | "secondary" | "destructive" | "outline" = "outline";
  if (score >= 0.9) variant = "default";
  else if (score >= 0.7) variant = "secondary";
  else if (score >= 0.5) variant = "outline";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant={variant} className="gap-1 cursor-help">
            <Sparkles className="h-3 w-3" />
            {showLabel && 'ELON'} {scorePercent}%
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-md">
          <div className="space-y-2">
            <div className="font-semibold">ELON Score: {scorePercent}%</div>
            {scoreData.signal_breakdown && (
              <div className="text-xs space-y-1">
                <div>arXiv: {(scoreData.signal_breakdown.arxiv_signal * 100).toFixed(0)}%</div>
                <div>GitHub: {(scoreData.signal_breakdown.github_signal * 100).toFixed(0)}%</div>
                <div>X: {(scoreData.signal_breakdown.x_signal * 100).toFixed(0)}%</div>
                {scoreData.signal_breakdown.phone_screen_signal && (
                  <div>Phone: {(scoreData.signal_breakdown.phone_screen_signal * 100).toFixed(0)}%</div>
                )}
              </div>
            )}
            {scoreData.why_exceptional && (
              <div className="text-xs text-muted-foreground mt-2">
                {scoreData.why_exceptional}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

