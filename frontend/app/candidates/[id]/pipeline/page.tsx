'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Briefcase, Search, Clock } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';

const STAGE_COLORS: Record<string, string> = {
  dm_screening: 'bg-blue-100 text-blue-800',
  dm_screening_completed: 'bg-purple-100 text-purple-800',
  dm_screening_passed: 'bg-green-100 text-green-800',
  dm_screening_failed: 'bg-red-100 text-red-800',
  phone_screen_scheduled: 'bg-yellow-100 text-yellow-800',
  phone_screen_completed: 'bg-orange-100 text-orange-800',
  phone_screen_passed: 'bg-green-100 text-green-800',
  phone_screen_failed: 'bg-red-100 text-red-800',
  matched_to_team: 'bg-indigo-100 text-indigo-800',
  matched_to_interviewer: 'bg-indigo-100 text-indigo-800',
  rejected: 'bg-gray-100 text-gray-800',
  accepted: 'bg-green-100 text-green-800',
};

function formatStage(stage: string): string {
  return stage
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function CandidatePipelinePage() {
  const params = useParams();
  const router = useRouter();
  const candidateId = params.id as string;
  const [selectedPositionId, setSelectedPositionId] = useState<string | null>(null);

  const { data: positions, isLoading } = useQuery({
    queryKey: ['candidatePipeline', candidateId],
    queryFn: () => apiClient.getCandidatePipeline(candidateId),
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['pipelineHistory', candidateId, selectedPositionId],
    queryFn: () => apiClient.getPipelineHistory(candidateId, selectedPositionId!),
    enabled: !!selectedPositionId,
  });

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6 flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Candidate Pipelines</h1>
          <p className="text-muted-foreground">All positions this candidate is in pipeline for</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : !positions || positions.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Briefcase className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">No positions in pipeline yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Active Positions</CardTitle>
              <CardDescription>
                {positions.length} position{positions.length !== 1 ? 's' : ''} in pipeline
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Position</TableHead>
                    <TableHead>Current Stage</TableHead>
                    <TableHead>Screening Score</TableHead>
                    <TableHead>Entered</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {positions.map((position: any) => (
                    <TableRow key={position.id}>
                      <TableCell className="font-medium">
                        <div
                          className="cursor-pointer hover:underline"
                          onClick={() => router.push(`/positions/${position.id}/pipeline`)}
                        >
                          {position.title || position.position_title || 'Unknown'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={STAGE_COLORS[position.stage] || 'bg-gray-100 text-gray-800'}>
                          {formatStage(position.stage || 'unknown')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {position.stage_metadata?.screening_score !== null &&
                        position.stage_metadata?.screening_score !== undefined ? (
                          <Badge
                            variant={
                              position.stage_metadata.screening_score >= 0.5 ? 'default' : 'destructive'
                            }
                          >
                            {(position.stage_metadata.screening_score * 100).toFixed(0)}%
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {position.stage_entered_at
                          ? format(new Date(position.stage_entered_at), 'MMM d, yyyy')
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            setSelectedPositionId(
                              selectedPositionId === position.id ? null : position.id
                            )
                          }
                        >
                          <Clock className="h-4 w-4 mr-2" />
                          {selectedPositionId === position.id ? 'Hide' : 'View'} History
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {selectedPositionId && (
            <Card>
              <CardHeader>
                <CardTitle>Pipeline History</CardTitle>
                <CardDescription>
                  Stage transitions for selected position
                </CardDescription>
              </CardHeader>
              <CardContent>
                {historyLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : !history || history.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No history available</p>
                ) : (
                  <div className="space-y-4">
                    {history.map((entry: any, idx: number) => (
                      <div
                        key={entry.id || idx}
                        className="flex items-center gap-4 p-4 border rounded-lg"
                      >
                        <Badge className={STAGE_COLORS[entry.stage] || 'bg-gray-100 text-gray-800'}>
                          {formatStage(entry.stage)}
                        </Badge>
                        <div className="flex-1">
                          <div className="text-sm text-muted-foreground">
                            Entered: {format(new Date(entry.entered_at), 'MMM d, yyyy HH:mm')}
                          </div>
                          {entry.exited_at && (
                            <div className="text-sm text-muted-foreground">
                              Exited: {format(new Date(entry.exited_at), 'MMM d, yyyy HH:mm')}
                            </div>
                          )}
                        </div>
                        {entry.metadata?.screening_score !== null &&
                          entry.metadata?.screening_score !== undefined && (
                            <Badge
                              variant={entry.metadata.screening_score >= 0.5 ? 'default' : 'destructive'}
                            >
                              Score: {(entry.metadata.screening_score * 100).toFixed(0)}%
                            </Badge>
                          )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

