'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, ExternalLink, Loader2, User, GitBranch, FileText, Mail, Phone, Github, Linkedin, MessageSquare, Brain, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ElonScoreBadge } from '@/components/demo/ElonScoreBadge';

const STAGE_COLORS: Record<string, string> = {
  'dm_screening': 'bg-blue-100 text-blue-800',
  'dm_screening_completed': 'bg-yellow-100 text-yellow-800',
  'dm_screening_passed': 'bg-green-100 text-green-800',
  'dm_screening_failed': 'bg-red-100 text-red-800',
  'phone_screen_scheduled': 'bg-purple-100 text-purple-800',
  'phone_screen_completed': 'bg-indigo-100 text-indigo-800',
  'phone_screen_passed': 'bg-emerald-100 text-emerald-800',
  'phone_screen_failed': 'bg-rose-100 text-rose-800',
  'matched_to_team': 'bg-teal-100 text-teal-800',
  'matched_to_interviewer': 'bg-cyan-100 text-cyan-800',
  'rejected': 'bg-gray-100 text-gray-800',
  'accepted': 'bg-lime-100 text-lime-800',
};

function formatStage(stage: string): string {
  return stage
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function CandidateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const identifier = params.id as string; // Can be x_handle or candidate ID

  // Try to get candidate by handle first (most common case)
  const { data: candidate, isLoading, error } = useQuery({
    queryKey: ['candidate', identifier],
    queryFn: () => apiClient.getCandidateByHandle(identifier),
    enabled: !!identifier,
  });

  const { data: pipelines, isLoading: pipelinesLoading } = useQuery({
    queryKey: ['candidate-pipeline', candidate?.id || candidate?.x_handle],
    queryFn: () => {
      // Try candidate.id first, fallback to x_handle if id doesn't exist
      const candidateId = candidate?.id || candidate?.x_handle;
      return apiClient.getCandidatePipeline(candidateId);
    },
    enabled: !!candidate && (!!candidate.id || !!candidate.x_handle),
  });

  const candidateId = candidate?.id || candidate?.x_handle;
  const { data: embeddingData, isLoading: embeddingLoading, error: embeddingError } = useQuery({
    queryKey: ['candidateEmbedding', candidateId],
    queryFn: () => apiClient.getCandidateEmbedding(candidateId),
    enabled: !!candidateId,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Skeleton className="h-12 w-64 mb-4" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Button variant="ghost" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Candidate not found or error loading candidate.
          </CardContent>
        </Card>
      </div>
    );
  }

  const skills = Array.isArray(candidate.skills) ? candidate.skills : [];
  const domains = Array.isArray(candidate.domains) ? candidate.domains : [];
  const repos = Array.isArray(candidate.repos) ? candidate.repos : [];
  const papers = Array.isArray(candidate.papers) ? candidate.papers : [];

  return (
    <div className="container mx-auto py-8 px-4">
      <Button variant="ghost" onClick={() => router.back()} className="mb-4">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                {candidate.name || `@${candidate.x_handle}`}
              </CardTitle>
              <CardDescription className="mt-1">
                {candidate.x_handle && (
                  <a
                    href={`https://x.com/${candidate.x_handle}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1"
                  >
                    @{candidate.x_handle}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="info" className="space-y-4">
        <TabsList>
          <TabsTrigger value="info">Candidate Info</TabsTrigger>
          <TabsTrigger value="pipelines">
            Pipelines
            {pipelines && pipelines.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {pipelines.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="info" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {candidate.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{candidate.email}</span>
                  </div>
                )}
                {candidate.phone_number && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{candidate.phone_number}</span>
                  </div>
                )}
                {candidate.experience_years && (
                  <div>
                    <span className="text-sm font-medium">Experience: </span>
                    <span className="text-sm">{candidate.experience_years} years</span>
                  </div>
                )}
                {candidate.expertise_level && (
                  <div>
                    <span className="text-sm font-medium">Level: </span>
                    <Badge variant="outline">{candidate.expertise_level}</Badge>
                  </div>
                )}
                {candidate.screening_score !== null && candidate.screening_score !== undefined && (
                  <div>
                    <span className="text-sm font-medium">Screening Score: </span>
                    <Badge variant={candidate.screening_score >= 0.5 ? 'default' : 'destructive'}>
                      {(candidate.screening_score * 100).toFixed(0)}%
                    </Badge>
                  </div>
                )}
                {candidateId && (
                  <div>
                    <span className="text-sm font-medium">ELON Score: </span>
                    <ElonScoreBadge candidateId={candidateId} />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Links */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Links & Profiles</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {candidate.github_handle && (
                  <a
                    href={`https://github.com/${candidate.github_handle}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:underline"
                  >
                    <Github className="h-4 w-4" />
                    <span className="text-sm">{candidate.github_handle}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {candidate.linkedin_url && (
                  <a
                    href={candidate.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:underline"
                  >
                    <Linkedin className="h-4 w-4" />
                    <span className="text-sm">LinkedIn Profile</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {candidate.x_handle && (
                  <a
                    href={`https://x.com/${candidate.x_handle}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:underline"
                  >
                    <MessageSquare className="h-4 w-4" />
                    <span className="text-sm">@{candidate.x_handle}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Skills & Domains */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Skills & Expertise</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {skills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Technical Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill: string, idx: number) => (
                      <Badge key={idx} variant="secondary">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {domains.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Domains</h4>
                  <div className="flex flex-wrap gap-2">
                    {domains.map((domain: string, idx: number) => (
                      <Badge key={idx} variant="outline">
                        {domain}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* GitHub Repos */}
          {repos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Github className="h-5 w-5" />
                  GitHub Repositories ({repos.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {repos.slice(0, 10).map((repo: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <a
                          href={`https://github.com/${candidate.github_handle}/${repo.name}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline font-medium"
                        >
                          {repo.name}
                        </a>
                        {repo.description && (
                          <p className="text-sm text-muted-foreground mt-1">{repo.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {repo.language && (
                          <Badge variant="outline" className="text-xs">
                            {repo.language}
                          </Badge>
                        )}
                        {repo.stars !== undefined && (
                          <span className="text-sm text-muted-foreground">⭐ {repo.stars}</span>
                        )}
                      </div>
                    </div>
                  ))}
                  {repos.length > 10 && (
                    <p className="text-sm text-muted-foreground text-center">
                      +{repos.length - 10} more repositories
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* arXiv Papers */}
          {papers.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  arXiv Papers ({papers.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {papers.slice(0, 10).map((paper: any, idx: number) => (
                    <div key={idx} className="p-2 border rounded">
                      <a
                        href={paper.pdf_url || `https://arxiv.org/abs/${paper.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline font-medium"
                      >
                        {paper.title}
                      </a>
                      {paper.authors && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}
                        </p>
                      )}
                      {paper.published && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Published: {format(new Date(paper.published), 'MMM d, yyyy')}
                        </p>
                      )}
                    </div>
                  ))}
                  {papers.length > 10 && (
                    <p className="text-sm text-muted-foreground text-center">
                      +{papers.length - 10} more papers
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Resume */}
          {candidate.resume_text && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Resume</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="whitespace-pre-wrap text-sm bg-muted p-4 rounded">
                  {candidate.resume_text}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Embedding Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Embedding Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              {embeddingLoading ? (
                <div className="flex items-center justify-center gap-2 py-4 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading embedding...</span>
                </div>
              ) : embeddingError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {embeddingError instanceof Error ? embeddingError.message : 'Failed to load embedding'}
                    {embeddingError instanceof Error && embeddingError.message.includes('404') && (
                      <div className="mt-2 text-sm">
                        This candidate may not have an embedding yet. Generate one using the button below.
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              ) : !embeddingData ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No embedding data available. This candidate may not have an embedding yet.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  {/* Embedding Info */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Dimension</div>
                      <div className="text-lg font-semibold">{embeddingData.embedding_dimension}</div>
                    </div>
                    {embeddingData.statistics && (
                      <>
                        <div>
                          <div className="text-sm font-medium text-muted-foreground">Min</div>
                          <div className="text-lg font-semibold">{embeddingData.statistics.min.toFixed(4)}</div>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-muted-foreground">Max</div>
                          <div className="text-lg font-semibold">{embeddingData.statistics.max.toFixed(4)}</div>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-muted-foreground">Norm</div>
                          <div className="text-lg font-semibold">{embeddingData.statistics.norm.toFixed(4)}</div>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Embedding Vector Preview */}
                  {embeddingData.embedding && embeddingData.embedding.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold">Embedding Vector (First 50 dimensions)</h4>
                      <div className="bg-muted rounded-lg p-4 font-mono text-xs overflow-x-auto">
                        <div className="flex flex-wrap gap-1">
                          {embeddingData.embedding.slice(0, 50).map((value, idx) => (
                            <span
                              key={idx}
                              className="inline-block px-1.5 py-0.5 rounded bg-background"
                              title={`Dimension ${idx + 1}: ${value.toFixed(6)}`}
                            >
                              {value.toFixed(4)}
                            </span>
                          ))}
                        </div>
                        {embeddingData.embedding.length > 50 && (
                          <div className="mt-2 text-muted-foreground text-xs">
                            ... and {embeddingData.embedding.length - 50} more dimensions
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pipelines">
          {pipelinesLoading ? (
            <Card>
              <CardContent className="py-8">
                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading pipelines...</span>
                </div>
              </CardContent>
            </Card>
          ) : !pipelines || pipelines.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                This candidate is not in any pipelines yet.
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="h-5 w-5" />
                  Pipeline Status
                </CardTitle>
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
                    {pipelines.map((position: any) => (
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
                            onClick={() => {
                              // Use candidate.id if available, otherwise use x_handle
                              const candidateId = candidate.id || candidate.x_handle;
                              router.push(`/candidates/${candidateId}/pipeline`);
                            }}
                          >
                            View History
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

