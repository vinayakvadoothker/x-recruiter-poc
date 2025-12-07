'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ExternalLink, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface CandidatePostsDialogProps {
  xHandle: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CandidatePostsDialog({ xHandle, open, onOpenChange }: CandidatePostsDialogProps) {
  const { data: posts, isLoading, error } = useQuery({
    queryKey: ['candidatePosts', xHandle],
    queryFn: () => apiClient.getCandidatePosts(xHandle),
    enabled: open && !!xHandle,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0 max-w-4xl">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Posts by @{xHandle}</DialogTitle>
          <DialogDescription>
            All position posts this candidate has commented "interested" on
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-hidden">
          {isLoading ? (
            <div className="px-6 py-4 space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="px-6 py-8 text-center text-muted-foreground">
              Error loading posts. Please try again.
            </div>
          ) : !posts || posts.length === 0 ? (
            <div className="px-6 py-8 text-center text-muted-foreground">
              No posts found for this candidate.
            </div>
          ) : (
            <ScrollArea className="flex-1">
              <div className="px-6 py-4 space-y-4">
                <div className="text-sm text-muted-foreground">
                  Found {posts.length} post{posts.length !== 1 ? 's' : ''}
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Position</TableHead>
                      <TableHead>Post Text</TableHead>
                      <TableHead>Comment</TableHead>
                      <TableHead>Commented</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {posts.map((post) => (
                      <TableRow key={post.id}>
                        <TableCell className="font-medium">
                          {post.position_title}
                        </TableCell>
                        <TableCell className="max-w-xs">
                          <div className="truncate text-sm text-muted-foreground" title={post.post_text}>
                            {post.post_text || 'N/A'}
                          </div>
                        </TableCell>
                        <TableCell className="max-w-xs">
                          <div className="truncate text-sm" title={post.comment_text}>
                            {post.comment_text || 'N/A'}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {post.commented_at
                            ? format(new Date(post.commented_at), 'MMM d, yyyy HH:mm')
                            : 'N/A'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            asChild
                          >
                            <a
                              href={post.post_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1"
                            >
                              View on X
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </ScrollArea>
          )}
        </div>

        <DialogFooter className="px-6 pb-6 pt-4 border-t flex-shrink-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

