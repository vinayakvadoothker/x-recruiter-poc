'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Users, Search, ExternalLink, Loader2, UserCheck } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CandidatePostsDialog } from '@/components/candidates/CandidatePostsDialog';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';
import { CandidateSearchDialog } from '@/components/demo/CandidateSearchDialog';
import { LearningDemoButton } from '@/components/demo/LearningDemoButton';

export default function CandidatesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHandle, setSelectedHandle] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const router = useRouter();

  // Don't auto-sync - just show candidates from database
  // User can manually sync if needed
  const { data: candidates, isLoading, error } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => apiClient.getCandidates(),
  });

  const filteredCandidates = candidates?.filter(candidate =>
    candidate.x_handle.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const manualScreenMutation = useMutation({
    mutationFn: (xHandle: string) => apiClient.manualScreenCandidate(xHandle),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });

  const handleRowClick = (candidate: any) => {
    // Navigate using id if available, otherwise use x_handle
    const identifier = candidate.id || candidate.x_handle;
    router.push(`/candidates/${encodeURIComponent(identifier)}`);
  };

  const handleManualScreen = async (e: React.MouseEvent, xHandle: string) => {
    e.stopPropagation(); // Prevent row click
    if (confirm(`Manually screen candidate @${xHandle}? This will send a DM with screening questions.`)) {
      try {
        await manualScreenMutation.mutateAsync(xHandle);
        alert('Screening initiated successfully!');
      } catch (error: any) {
        alert(`Error: ${error.message || 'Failed to initiate screening'}`);
      }
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Candidates
              </CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <CandidateSearchDialog />
              <LearningDemoButton />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search by X handle..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2 py-4 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading candidates...</span>
              </div>
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8 text-muted-foreground">
              Error loading candidates. Please try again.
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchQuery ? 'No candidates found matching your search.' : 'No candidates in database yet.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>X Handle</TableHead>
                  <TableHead>User ID</TableHead>
                  <TableHead>Positions</TableHead>
                  <TableHead>Latest Comment</TableHead>
                  <TableHead>First Seen</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCandidates.map((candidate) => (
                  <TableRow 
                    key={candidate.x_handle || candidate.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleRowClick(candidate)}
                  >
                    <TableCell className="font-medium">
                      <div className="flex flex-col">
                        {candidate.name && (
                          <span className="font-semibold">{candidate.name}</span>
                        )}
                        <a
                          href={`https://x.com/${candidate.x_handle}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline flex items-center gap-1"
                          onClick={(e) => e.stopPropagation()}
                        >
                          @{candidate.x_handle}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {candidate.x_user_id || candidate.id || 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{candidate.position_count}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {candidate.latest_comment_at
                        ? format(new Date(candidate.latest_comment_at), 'MMM d, yyyy')
                        : 'N/A'}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {candidate.first_seen_at
                        ? format(new Date(candidate.first_seen_at), 'MMM d, yyyy')
                        : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedHandle(candidate.x_handle);
                          }}
                        >
                          View Posts
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={(e) => handleManualScreen(e, candidate.x_handle)}
                          disabled={manualScreenMutation.isPending}
                        >
                          <UserCheck className="h-4 w-4 mr-1" />
                          Screen
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selectedHandle && (
        <CandidatePostsDialog
          xHandle={selectedHandle}
          open={!!selectedHandle}
          onOpenChange={(open) => !open && setSelectedHandle(null)}
        />
      )}
    </div>
  );
}

