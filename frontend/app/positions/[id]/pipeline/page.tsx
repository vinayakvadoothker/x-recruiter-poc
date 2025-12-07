'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Users, Search, MessageSquare, Loader2, Phone, CheckCircle2, XCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';
import { PhoneScreenButton } from '@/components/demo/PhoneScreenButton';
import { useToast } from '@/hooks/use-toast';

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

export default function PositionPipelinePage() {
  const params = useParams();
  const router = useRouter();
  const positionId = params.id as string;
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null);
  const [phoneScreenResult, setPhoneScreenResult] = useState<any>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: candidates, isLoading } = useQuery({
    queryKey: ['positionPipeline', positionId],
    queryFn: () => apiClient.getPositionPipeline(positionId),
  });

  const manualScreenMutation = useMutation({
    mutationFn: (xHandle: string) => apiClient.manualScreenCandidate(xHandle),
    onSuccess: () => {
      // Refetch pipeline data after screening
      queryClient.invalidateQueries({ queryKey: ['positionPipeline', positionId] });
    },
  });

  const handleManualScreen = async (e: React.MouseEvent, xHandle: string, candidateName: string) => {
    e.stopPropagation(); // Prevent row click
    if (confirm(`Send DM screening to ${candidateName} (@${xHandle})?`)) {
      try {
        await manualScreenMutation.mutateAsync(xHandle);
        alert('DM screening initiated successfully!');
      } catch (error: any) {
        alert(`Error: ${error.message || 'Failed to initiate DM screening'}`);
      }
    }
  };

  const filteredCandidates = candidates?.filter((candidate: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      candidate.name?.toLowerCase().includes(query) ||
      candidate.x_handle?.toLowerCase().includes(query) ||
      candidate.stage?.toLowerCase().includes(query)
    );
  }) || [];

  const groupedByStage = filteredCandidates.reduce((acc: Record<string, any[]>, candidate: any) => {
    const stage = candidate.stage || 'unknown';
    if (!acc[stage]) acc[stage] = [];
    acc[stage].push(candidate);
    return acc;
  }, {});

  // Get candidates ready for phone screen (ONLY dm_screening_passed - NOT phone_screen_passed)
  // These are candidates who passed DM screening but haven't been phone screened yet
  const phoneScreenReady = filteredCandidates.filter((c: any) => 
    c.stage === 'dm_screening_passed'
  ).slice(0, 10);

  const phoneScreenMutation = useMutation({
    mutationFn: async ({ candidateId, positionId }: { candidateId: string; positionId: string }) => {
      return await apiClient.phoneScreenAndMatch(candidateId, positionId);
    },
    onSuccess: (data) => {
      setPhoneScreenResult(data);
      queryClient.invalidateQueries({ queryKey: ['positionPipeline', positionId] });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to conduct phone screen',
        variant: 'destructive',
      });
    },
  });

  const judgePassMutation = useMutation({
    mutationFn: async ({ candidateId, positionId }: { candidateId: string; positionId: string }) => {
      return await apiClient.updatePipelineStage(candidateId, positionId, 'matched_to_team', {
        judged_by: 'manual',
        judged_at: new Date().toISOString(),
        phone_screen_result: phoneScreenResult,
      });
    },
    onSuccess: () => {
      toast({
        title: '✅ Candidate Passed!',
        description: 'Candidate has been matched to team and interviewer.',
      });
      setSelectedCandidate(null);
      setPhoneScreenResult(null);
      queryClient.invalidateQueries({ queryKey: ['positionPipeline', positionId] });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update pipeline',
        variant: 'destructive',
      });
    },
  });

  const judgeFailMutation = useMutation({
    mutationFn: async ({ candidateId, positionId }: { candidateId: string; positionId: string }) => {
      return await apiClient.updatePipelineStage(candidateId, positionId, 'phone_screen_failed', {
        judged_by: 'manual',
        judged_at: new Date().toISOString(),
      });
    },
    onSuccess: () => {
      toast({
        title: '❌ Candidate Failed',
        description: 'Candidate marked as failed.',
      });
      setSelectedCandidate(null);
      setPhoneScreenResult(null);
      queryClient.invalidateQueries({ queryKey: ['positionPipeline', positionId] });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update pipeline',
        variant: 'destructive',
      });
    },
  });

  const handleSelectCandidate = (candidate: any) => {
    setSelectedCandidate(candidate);
    setPhoneScreenResult(null);
  };

  const handleConductPhoneScreen = async () => {
    if (!selectedCandidate) return;
    const candidateId = selectedCandidate.id || selectedCandidate.candidate_id;
    if (!candidateId) {
      toast({
        title: 'Error',
        description: 'Missing candidate ID',
        variant: 'destructive',
      });
      return;
    }
    await phoneScreenMutation.mutateAsync({ candidateId, positionId });
  };

  const handleJudgePass = async () => {
    if (!selectedCandidate) return;
    const candidateId = selectedCandidate.id || selectedCandidate.candidate_id;
    await judgePassMutation.mutateAsync({ candidateId, positionId });
  };

  const handleJudgeFail = async () => {
    if (!selectedCandidate) return;
    const candidateId = selectedCandidate.id || selectedCandidate.candidate_id;
    await judgeFailMutation.mutateAsync({ candidateId, positionId });
  };

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
          <h1 className="text-3xl font-bold">Position Pipeline</h1>
          <p className="text-muted-foreground">Candidates in pipeline for this position</p>
        </div>
      </div>

      {/* Phone Screen Selection Section */}
      {phoneScreenReady.length > 0 && (
        <Card className="mb-6 border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5" />
              Phone Screen Selection
            </CardTitle>
            <CardDescription>
              Select a candidate to conduct phone screen interview. {phoneScreenReady.length} candidate{phoneScreenReady.length !== 1 ? 's' : ''} ready.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Left: Candidate Selection */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {phoneScreenReady.map((candidate: any) => {
                  const candidateId = candidate.id || candidate.candidate_id;
                  const isSelected = selectedCandidate?.id === candidateId;
                  const screeningScore = candidate.stage_metadata?.screening_score || candidate.screening_score || 0;
                  
                  return (
                    <Card
                      key={candidateId}
                      className={`cursor-pointer transition-all ${
                        isSelected ? 'ring-2 ring-primary' : 'hover:bg-muted/50'
                      }`}
                      onClick={() => handleSelectCandidate(candidate)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="font-semibold">{candidate.name || `@${candidate.x_handle}`}</div>
                            <div className="text-sm text-muted-foreground">@{candidate.x_handle}</div>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="secondary" className="text-xs">
                                Score: {(screeningScore * 100).toFixed(0)}%
                              </Badge>
                            </div>
                          </div>
                          {isSelected && <CheckCircle2 className="h-4 w-4 text-primary" />}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              {/* Right: Phone Screen Action */}
              <div className="space-y-4">
                {selectedCandidate ? (
                  <>
                    <div className="space-y-2">
                      <div><strong>Candidate:</strong> {selectedCandidate.name || `@${selectedCandidate.x_handle}`}</div>
                      <div>
                        <strong>Screening Score:</strong>{' '}
                        <Badge variant="secondary">
                          {((selectedCandidate.stage_metadata?.screening_score || selectedCandidate.screening_score || 0) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>

                    {!phoneScreenResult ? (
                      <Button
                        onClick={handleConductPhoneScreen}
                        disabled={phoneScreenMutation.isPending}
                        className="w-full"
                        size="lg"
                      >
                        {phoneScreenMutation.isPending ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Conducting Phone Screen...
                          </>
                        ) : (
                          <>
                            <Phone className="h-4 w-4 mr-2" />
                            Conduct Phone Screen
                          </>
                        )}
                      </Button>
                    ) : (
                      <Card className="border-2">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            {phoneScreenResult.decision === 'PASS' ? (
                              <CheckCircle2 className="h-5 w-5 text-green-600" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-600" />
                            )}
                            Result: {phoneScreenResult.decision}
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {phoneScreenResult.analysis && (
                            <div>
                              <strong>Analysis:</strong>
                              <p className="text-sm text-muted-foreground mt-1">
                                {phoneScreenResult.analysis.reasoning || 'Analysis complete'}
                              </p>
                            </div>
                          )}

                          {phoneScreenResult.team_match && (
                            <div>
                              <strong>Matched Team:</strong>{' '}
                              <Badge>{phoneScreenResult.team_match.team_id}</Badge>
                            </div>
                          )}

                          {phoneScreenResult.interviewer_match && (
                            <div>
                              <strong>Matched Interviewer:</strong>{' '}
                              <Badge>{phoneScreenResult.interviewer_match.interviewer_id}</Badge>
                            </div>
                          )}

                          <div className="flex gap-2 pt-2">
                            <Button
                              onClick={handleJudgePass}
                              disabled={judgePassMutation.isPending || phoneScreenResult.decision === 'FAIL'}
                              variant="default"
                              className="flex-1"
                            >
                              <CheckCircle2 className="h-4 w-4 mr-2" />
                              Confirm Pass
                            </Button>
                            <Button
                              onClick={handleJudgeFail}
                              disabled={judgeFailMutation.isPending || phoneScreenResult.decision === 'PASS'}
                              variant="destructive"
                              className="flex-1"
                            >
                              <XCircle className="h-4 w-4 mr-2" />
                              Mark as Fail
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Select a candidate to conduct phone screen
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="mb-6 flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search candidates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Badge variant="outline" className="ml-auto">
          {filteredCandidates.length} candidate{filteredCandidates.length !== 1 ? 's' : ''}
        </Badge>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : filteredCandidates.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">No candidates in pipeline yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedByStage)
            .filter(([stage]) => stage !== 'phone_screen_passed') // Hide phone_screen_passed stage
            .map(([stage, stageCandidates]) => (
            <Card key={stage}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Badge className={STAGE_COLORS[stage] || 'bg-gray-100 text-gray-800'}>
                    {formatStage(stage)}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    ({stageCandidates.length})
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>X Handle</TableHead>
                      <TableHead>Skills</TableHead>
                      <TableHead>Screening Score</TableHead>
                      <TableHead>Entered</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stageCandidates.map((candidate: any) => {
                      // Ensure skills is always an array
                      let skills: string[] = [];
                      if (Array.isArray(candidate.skills)) {
                        skills = candidate.skills;
                      } else if (candidate.skills) {
                        try {
                          skills = typeof candidate.skills === 'string' 
                            ? JSON.parse(candidate.skills) 
                            : [];
                        } catch {
                          skills = [];
                        }
                      }
                      
                      return (
                        <TableRow
                          key={candidate.id}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => router.push(`/candidates/${candidate.id}/pipeline`)}
                        >
                          <TableCell className="font-medium">{candidate.name || 'Unknown'}</TableCell>
                          <TableCell>@{candidate.x_handle || 'N/A'}</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {skills.slice(0, 3).map((skill: string, idx: number) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                              {skills.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{skills.length - 3}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                        <TableCell>
                          {candidate.screening_score !== null && candidate.screening_score !== undefined ? (
                            <Badge
                              variant={candidate.screening_score >= 0.5 ? 'default' : 'destructive'}
                            >
                              {(candidate.screening_score * 100).toFixed(0)}%
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {candidate.stage_entered_at
                            ? format(new Date(candidate.stage_entered_at), 'MMM d, yyyy')
                            : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => handleManualScreen(e, candidate.x_handle, candidate.name || 'Unknown')}
                              disabled={manualScreenMutation.isPending || !candidate.x_handle}
                            >
                              {manualScreenMutation.isPending ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                  Sending...
                                </>
                              ) : (
                                <>
                                  <MessageSquare className="h-4 w-4 mr-1" />
                                  Send DM
                                </>
                              )}
                            </Button>
                            {candidate.stage === 'dm_screening_passed' && (candidate.id || candidate.candidate_id) && (
                              <PhoneScreenButton
                                candidateId={candidate.id || candidate.candidate_id}
                                positionId={positionId}
                                candidateName={candidate.name}
                                onSuccess={() => {
                                  queryClient.invalidateQueries({ queryKey: ['positionPipeline', positionId] });
                                }}
                              />
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

