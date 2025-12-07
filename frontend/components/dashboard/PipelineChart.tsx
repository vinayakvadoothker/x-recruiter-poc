'use client';

import { useQueries } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';

interface Position {
  id: string;
  title: string;
}

interface Candidate {
  id?: string;
  x_handle: string;
}

interface PipelineChartProps {
  positions: Position[];
  candidates: Candidate[];
}

const STAGE_COLORS: Record<string, string> = {
  'dm_screening': '#3b82f6',
  'dm_screening_completed': '#06b6d4',
  'dm_screening_passed': '#10b981',
  'phone_screen_scheduled': '#8b5cf6',
  'phone_screen_completed': '#ec4899',
  'phone_screen_passed': '#059669',
  'matched_to_team': '#f59e0b',
  'accepted': '#84cc16',
  'rejected': '#ef4444',
};

const STAGE_LABELS: Record<string, string> = {
  'dm_screening': 'DM Screening',
  'dm_screening_completed': 'Screening Done',
  'dm_screening_passed': 'Passed Screening',
  'phone_screen_scheduled': 'Phone Scheduled',
  'phone_screen_completed': 'Phone Done',
  'phone_screen_passed': 'Passed Phone',
  'matched_to_team': 'Matched',
  'accepted': 'Accepted',
  'rejected': 'Rejected',
};

export function PipelineChart({ positions, candidates }: PipelineChartProps) {
  // Fetch pipeline data for all positions
  const pipelineQueries = useQueries({
    queries: positions.map(position => ({
      queryKey: ['position-pipeline', position.id],
      queryFn: () => apiClient.getPositionPipeline(position.id),
      enabled: positions.length > 0,
    })),
  });

  const isLoading = pipelineQueries.some(q => q.isLoading);

  // Aggregate all pipeline data by stage
  const stageCounts: Record<string, number> = {};
  
  pipelineQueries.forEach(query => {
    const pipeline = query.data || [];
    pipeline.forEach((candidate: any) => {
      const stage = candidate.stage || 'dm_screening';
      stageCounts[stage] = (stageCounts[stage] || 0) + 1;
    });
  });

  // Prepare chart data
  const chartData = Object.entries(stageCounts).map(([stage, count]) => ({
    stage: STAGE_LABELS[stage] || stage,
    count,
    color: STAGE_COLORS[stage] || '#888888',
  })).sort((a, b) => b.count - a.count);

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No pipeline data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
        <XAxis 
          dataKey="stage" 
          angle={-45}
          textAnchor="end"
          height={100}
          className="text-xs"
        />
        <YAxis className="text-xs" />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

