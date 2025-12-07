'use client';

import { useQueries } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowRight, Users, Briefcase } from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';

interface Position {
  id: string;
  title: string;
  status?: string;
}

interface Candidate {
  id?: string;
  x_handle: string;
  name?: string;
}

interface PipelineFlowProps {
  positions: Position[];
  candidates: Candidate[];
}

const STAGES = [
  { id: 'dm_screening', label: 'DM Screening', color: 'bg-blue-500', order: 1 },
  { id: 'dm_screening_completed', label: 'Screening Done', color: 'bg-cyan-500', order: 2 },
  { id: 'dm_screening_passed', label: 'Passed Screening', color: 'bg-green-500', order: 3 },
  { id: 'phone_screen_scheduled', label: 'Phone Scheduled', color: 'bg-purple-500', order: 4 },
  { id: 'phone_screen_completed', label: 'Phone Done', color: 'bg-pink-500', order: 5 },
  { id: 'phone_screen_passed', label: 'Passed Phone', color: 'bg-emerald-500', order: 6 },
  { id: 'matched_to_team', label: 'Matched', color: 'bg-amber-500', order: 7 },
  { id: 'accepted', label: 'Accepted', color: 'bg-lime-500', order: 8 },
];

export function PipelineFlow({ positions, candidates }: PipelineFlowProps) {
  // Fetch pipeline data for each position using useQueries
  const pipelineQueries = useQueries({
    queries: positions.map(position => ({
      queryKey: ['position-pipeline', position.id],
      queryFn: () => apiClient.getPositionPipeline(position.id),
      enabled: positions.length > 0,
    })),
  });

  // Aggregate pipeline data by stage
  const pipelineData = positions.map((position, index) => {
    const pipeline = pipelineQueries[index]?.data || [];
    const stageCounts: Record<string, number> = {};
    
    pipeline.forEach((candidate: any) => {
      const stage = candidate.stage || 'dm_screening';
      stageCounts[stage] = (stageCounts[stage] || 0) + 1;
    });

    return {
      position,
      stageCounts,
      total: pipeline.length,
    };
  });

  const isLoading = pipelineQueries.some(q => q.isLoading);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center space-y-4">
        <Briefcase className="h-12 w-12 text-muted-foreground" />
        <div>
          <p className="text-lg font-semibold">No positions yet</p>
          <p className="text-sm text-muted-foreground">Create your first position to see pipeline flow</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Pipeline visualization for each position */}
      {pipelineData.map(({ position, stageCounts, total }, posIndex) => (
        <motion.div
          key={position.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: posIndex * 0.1 }}
        >
          <Link href={`/positions/${position.id}/pipeline`}>
            <Card className="p-6 hover:bg-accent/50 transition-colors cursor-pointer border-2 group">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Briefcase className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  <h3 className="font-semibold text-lg">{position.title}</h3>
                  <Badge variant="outline">{total} candidates</Badge>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              
              {/* Pipeline stages flow */}
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {STAGES.map((stage, stageIndex) => {
                  const count = stageCounts[stage.id] || 0;
                  const width = total > 0 ? Math.max((count / total) * 100, count > 0 ? 8 : 0) : 0;
                  
                  return (
                    <div key={stage.id} className="flex items-center gap-2 flex-shrink-0">
                      <div className="flex flex-col items-center gap-2 min-w-[80px]">
                        <div className="w-full h-8 rounded-lg overflow-hidden bg-muted relative group/stage">
                          {count > 0 && (
                            <motion.div
                              className={`${stage.color} h-full flex items-center justify-center text-white text-xs font-semibold`}
                              initial={{ width: 0 }}
                              animate={{ width: `${width}%` }}
                              transition={{ delay: posIndex * 0.1 + stageIndex * 0.05 }}
                            >
                              {count > 0 && count}
                            </motion.div>
                          )}
                        </div>
                        <div className="text-xs text-center">
                          <div className="font-medium">{stage.label}</div>
                          <div className="text-muted-foreground">{count}</div>
                        </div>
                      </div>
                      {stageIndex < STAGES.length - 1 && (
                        <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}

