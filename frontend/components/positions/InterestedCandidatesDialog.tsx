'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Position } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Loader2, RefreshCw, User, MessageSquare, Calendar, Sparkles, FileText, ExternalLink } from 'lucide-react';
import { PositionDistributionDialog } from './PositionDistributionDialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface InterestedCandidatesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  position: Position;
}

interface InterestedCandidate {
  id: string;
  x_handle: string;
  x_user_id?: string;
  comment_text: string;
  comment_id?: string;
  commented_at?: string;
  created_at?: string;
  x_post_id: string;
  post_text?: string;
}

interface XPost {
  id: string;
  x_post_id: string;
  post_text: string;
  posted_at?: string;
  created_at?: string;
  updated_at?: string;
}

export function InterestedCandidatesDialog({
  open,
  onOpenChange,
  position,
}: InterestedCandidatesDialogProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [showDistributionDialog, setShowDistributionDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<'candidates' | 'posts'>('candidates');

  const { data: candidates, isLoading, error } = useQuery<InterestedCandidate[]>({
    queryKey: ['interestedCandidates', position.id],
    queryFn: () => apiClient.getInterestedCandidates(position.id),
    enabled: open && !!position.id,
  });

  const { data: xPosts, isLoading: postsLoading } = useQuery<XPost[]>({
    queryKey: ['positionXPosts', position.id],
    queryFn: () => apiClient.getPositionXPosts(position.id),
    enabled: open && !!position.id,
  });

  const syncMutation = useMutation({
    mutationFn: () => apiClient.syncInterestedCandidates(position.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interestedCandidates', position.id] });
      queryClient.invalidateQueries({ queryKey: ['positionXPosts', position.id] });
      toast({
        title: 'Sync complete',
        description: data.message || `Found ${data.new_candidates} new candidates`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to sync interested candidates',
        variant: 'destructive',
      });
    },
  });

  const formatDate = (dateString?: string) => {
    if (!dateString) return '—';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-w-4xl max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle>Position Management: {position.title}</DialogTitle>
              <DialogDescription>
                Manage interested candidates and X posts for this position
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowDistributionDialog(true)}
                variant="outline"
                size="sm"
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Distribute
              </Button>
              {activeTab === 'candidates' && (
                <Button
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                  variant="outline"
                  size="sm"
                >
                  {syncMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Sync from X
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'candidates' | 'posts')} className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="px-6 border-b">
            <TabsList>
              <TabsTrigger value="candidates">
                <User className="mr-2 h-4 w-4" />
                Interested Candidates
                {candidates && candidates.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {candidates.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="posts">
                <FileText className="mr-2 h-4 w-4" />
                X Posts
                {xPosts && xPosts.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {xPosts.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="candidates" className="flex-1 overflow-y-auto px-6 py-4 min-h-0 mt-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-destructive">
              Failed to load interested candidates
            </div>
          ) : !candidates || candidates.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No interested candidates yet</p>
              <p className="text-sm mt-2">
                Click &quot;Sync from X&quot; to check for new comments
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>X Handle</TableHead>
                  <TableHead>Comment</TableHead>
                  <TableHead>Commented At</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {candidates.map((candidate) => (
                  <TableRow key={candidate.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">@{candidate.x_handle}</span>
                        {candidate.x_user_id && (
                          <Badge variant="outline" className="text-xs">
                            {candidate.x_user_id.substring(0, 8)}...
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-start gap-2 max-w-md">
                        <MessageSquare className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        <p className="text-sm line-clamp-2">{candidate.comment_text || '—'}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        {formatDate(candidate.commented_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            window.open(`https://x.com/${candidate.x_handle}`, '_blank');
                          }}
                        >
                          View Profile
                        </Button>
                        {candidate.comment_id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              window.open(`https://x.com/${candidate.x_handle}/status/${candidate.comment_id}`, '_blank');
                            }}
                          >
                            View Comment
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          </TabsContent>

          <TabsContent value="posts" className="flex-1 overflow-y-auto px-6 py-4 min-h-0 mt-0">
            {postsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : !xPosts || xPosts.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">No X posts yet</p>
                <p className="text-sm mt-2">
                  Click &quot;Distribute&quot; to create and post to X
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {xPosts.map((post) => (
                  <div
                    key={post.id}
                    className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="font-mono text-xs">
                            {post.x_post_id.substring(0, 16)}...
                          </Badge>
                          {post.posted_at && (
                            <span className="text-sm text-muted-foreground">
                              {formatDate(post.posted_at)}
                            </span>
                          )}
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{post.post_text}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          window.open(`https://x.com/i/web/status/${post.x_post_id}`, '_blank');
                        }}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View on X
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Distribution Dialog */}
        <PositionDistributionDialog
          open={showDistributionDialog}
          onOpenChange={(open) => {
            setShowDistributionDialog(open);
            // Refresh X posts when dialog closes (in case a new post was created)
            if (!open) {
              queryClient.invalidateQueries({ queryKey: ['positionXPosts', position.id] });
            }
          }}
          positionId={position.id}
        />
      </DialogContent>
    </Dialog>
  );
}

