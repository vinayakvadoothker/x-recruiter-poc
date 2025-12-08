'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Search, Github, FileText, Twitter, Sparkles, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function OutboundSignalsPage() {
  const [githubUrl, setGithubUrl] = useState('');
  const [arxivId, setArxivId] = useState('');
  const [xHandle, setXHandle] = useState('');
  const [positionId, setPositionId] = useState('');

  // Fetch positions for dropdown
  const { data: positions, isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: () => apiClient.getPositions(),
  });

  const analysisMutation = useMutation({
    mutationFn: async (data: {
      github_url?: string;
      arxiv_id?: string;
      x_handle?: string;
      position_id?: string;
    }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/outbound-signals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl && !arxivId && !xHandle) return;

    analysisMutation.mutate({
      github_url: githubUrl || undefined,
      arxiv_id: arxivId || undefined,
      x_handle: xHandle || undefined,
      position_id: positionId || undefined,
    });
  };

  const result = analysisMutation.data;

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <h1 className="text-3xl font-bold">Outbound Signals Analysis</h1>
        </div>
        <p className="text-muted-foreground">
          Analyze candidates from GitHub, arXiv, and X. Generate embeddings and match to positions instantly.
        </p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Input Sources</CardTitle>
          <CardDescription>
            Provide at least one source to analyze. All sources will be merged into a unified profile.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Github className="h-4 w-4" />
                  GitHub URL or Username
                </label>
                <Input
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="github.com/username or username"
                  disabled={analysisMutation.isPending}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  arXiv Author ID or Paper ID
                </label>
                <Input
                  value={arxivId}
                  onChange={(e) => setArxivId(e.target.value)}
                  placeholder="warner_s_1 or 2301.12345"
                  disabled={analysisMutation.isPending}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Twitter className="h-4 w-4" />
                  X Handle
                </label>
                <Input
                  value={xHandle}
                  onChange={(e) => setXHandle(e.target.value)}
                  placeholder="@username or username"
                  disabled={analysisMutation.isPending}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Position (Optional)</label>
              <Select
                value={positionId || 'all'}
                onValueChange={(value) => setPositionId(value === 'all' ? '' : value)}
                disabled={analysisMutation.isPending || positionsLoading}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a position or leave for all positions">
                    {positionId
                      ? positions?.find((p) => p.id === positionId)?.title || 'Selected position'
                      : 'All open positions'}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All open positions</SelectItem>
                  {positionsLoading ? (
                    <SelectItem value="loading" disabled>
                      Loading positions...
                    </SelectItem>
                  ) : (
                    positions
                      ?.filter((p) => p.status === 'open')
                      .map((position) => (
                        <SelectItem key={position.id} value={position.id}>
                          {position.title}
                        </SelectItem>
                      ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <Button
              type="submit"
              disabled={analysisMutation.isPending || (!githubUrl && !arxivId && !xHandle)}
              className="w-full"
            >
              {analysisMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Analyze Signals
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <AnimatePresence>
        {analysisMutation.isPending && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mb-6"
          >
            <Card>
              <CardContent className="p-12 text-center">
                <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
                <p className="text-lg font-medium">Gathering data from sources...</p>
                <p className="text-sm text-muted-foreground mt-2">
                  This may take a few moments as we fetch data from GitHub, arXiv, and X
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Candidate Profile */}
            <Card>
              <CardHeader>
                <CardTitle>Candidate Profile</CardTitle>
                <CardDescription>Merged profile from all sources</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">{result.candidate_profile?.name}</h3>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {result.sources?.github && (
                        <Badge variant="secondary">
                          <Github className="h-3 w-3 mr-1" />
                          GitHub
                        </Badge>
                      )}
                      {result.sources?.arxiv && (
                        <Badge variant="secondary">
                          <FileText className="h-3 w-3 mr-1" />
                          arXiv
                        </Badge>
                      )}
                      {result.sources?.x && (
                        <Badge variant="secondary">
                          <Twitter className="h-3 w-3 mr-1" />
                          X
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Experience</div>
                      <div className="text-lg font-semibold">
                        {result.candidate_profile?.experience_years} years
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Level</div>
                      <div className="text-lg font-semibold">
                        {result.candidate_profile?.expertise_level}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Papers</div>
                      <div className="text-lg font-semibold">
                        {result.candidate_profile?.papers_count || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Repos</div>
                      <div className="text-lg font-semibold">
                        {result.candidate_profile?.repos_count || 0}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-medium mb-2">Skills</div>
                    <div className="flex flex-wrap gap-2">
                      {result.candidate_profile?.skills?.map((skill: string, idx: number) => (
                        <Badge key={idx} variant="outline">{skill}</Badge>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-medium mb-2">Domains</div>
                    <div className="flex flex-wrap gap-2">
                      {result.candidate_profile?.domains?.map((domain: string, idx: number) => (
                        <Badge key={idx} variant="secondary">{domain}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Embedding */}
            <Card>
              <CardHeader>
                <CardTitle>Embedding</CardTitle>
                <CardDescription>
                  {result.embedding?.dimensions}-dimensional vector representation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">
                    First 10 dimensions (of {result.embedding?.dimensions}):
                  </div>
                  <div className="font-mono text-xs bg-muted p-3 rounded overflow-x-auto">
                    [{result.embedding?.vector?.map((v: number) => v.toFixed(4)).join(', ')}]
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Position Matches */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Position Matches
                </CardTitle>
                <CardDescription>
                  Top matches based on embedding similarity
                </CardDescription>
              </CardHeader>
              <CardContent>
                {result.position_matches?.length > 0 ? (
                  <div className="space-y-4">
                    {result.position_matches.map((match: any, idx: number) => (
                      <motion.div
                        key={match.position_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-lg">{match.title}</h4>
                            <div className="text-sm text-muted-foreground">
                              Match: {match.match_percentage}%
                            </div>
                          </div>
                          <Badge
                            variant={match.match_percentage > 80 ? 'default' : match.match_percentage > 60 ? 'secondary' : 'outline'}
                          >
                            {match.match_percentage}% match
                          </Badge>
                        </div>
                        <div className="space-y-2">
                          {match.experience_level && (
                            <div className="text-sm">
                              <span className="text-muted-foreground">Level: </span>
                              <Badge variant="outline" className="ml-1">{match.experience_level}</Badge>
                            </div>
                          )}
                          {match.tech_stack && match.tech_stack.length > 0 && (
                            <div>
                              <div className="text-sm text-muted-foreground mb-1">Tech Stack:</div>
                              <div className="flex flex-wrap gap-1">
                                {match.tech_stack.map((tech: string, i: number) => (
                                  <Badge key={i} variant="outline" className="text-xs">{tech}</Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          {match.domains && match.domains.length > 0 && (
                            <div>
                              <div className="text-sm text-muted-foreground mb-1">Domains:</div>
                              <div className="flex flex-wrap gap-1">
                                {match.domains.map((domain: string, i: number) => (
                                  <Badge key={i} variant="secondary" className="text-xs">{domain}</Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No position matches found
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {analysisMutation.isError && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-6"
          >
            <Card className="border-destructive">
              <CardContent className="p-6">
                <div className="text-destructive font-medium">
                  Error: {analysisMutation.error?.message || 'Failed to analyze signals'}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

