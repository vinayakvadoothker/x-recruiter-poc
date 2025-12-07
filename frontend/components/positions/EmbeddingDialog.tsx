'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { apiClient, Position } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface PositionEmbeddingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  position: Position;
}

export function PositionEmbeddingDialog({
  open,
  onOpenChange,
  position,
}: PositionEmbeddingDialogProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['positionEmbedding', position.id],
    queryFn: () => apiClient.getPositionEmbedding(position.id),
    enabled: open && !!position.id,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Position Embedding: {position.title}</DialogTitle>
          <DialogDescription>
            View the 768-dimensional embedding vector for this position
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4 min-h-0">
          <div className="pr-4">
            {isLoading && (
              <div className="space-y-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-64 w-full" />
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {error instanceof Error ? error.message : 'Failed to load embedding'}
                </AlertDescription>
              </Alert>
            )}

            {data && (
              <div className="space-y-6">
                {/* Embedding Info */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Embedding Dimension:</span>
                    <Badge variant="secondary">{data.dimension}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Profile Type:</span>
                    <Badge variant="outline">{data.profile_type}</Badge>
                  </div>
                </div>

                {/* Embedding Vector Preview */}
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold">Embedding Vector (First 50 dimensions)</h3>
                  <div className="bg-muted rounded-lg p-4 font-mono text-xs overflow-x-auto">
                    <div className="flex flex-wrap gap-1">
                      {data.embedding.slice(0, 50).map((value, idx) => (
                        <span
                          key={idx}
                          className="inline-block px-1.5 py-0.5 rounded bg-background"
                          title={`Dimension ${idx + 1}: ${value.toFixed(6)}`}
                        >
                          {value.toFixed(4)}
                        </span>
                      ))}
                    </div>
                    {data.embedding.length > 50 && (
                      <div className="mt-2 text-muted-foreground text-xs">
                        ... and {data.embedding.length - 50} more dimensions
                      </div>
                    )}
                  </div>
                </div>

                {/* Statistics */}
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold">Vector Statistics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Min</div>
                      <div className="text-sm font-medium">
                        {data.statistics.min.toFixed(6)}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Max</div>
                      <div className="text-sm font-medium">
                        {data.statistics.max.toFixed(6)}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Mean</div>
                      <div className="text-sm font-medium">
                        {data.statistics.mean.toFixed(6)}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Magnitude</div>
                      <div className="text-sm font-medium">
                        {data.statistics.magnitude.toFixed(6)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Metadata */}
                {data.metadata && Object.keys(data.metadata).length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold">Metadata</h3>
                    <div className="bg-muted rounded-lg p-4">
                      <pre className="text-xs overflow-x-auto">
                        {JSON.stringify(data.metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
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

