'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Position } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus, Edit, Briefcase, Trash2, Brain, Sparkles, Search, Users, GitBranch } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useState, useEffect } from 'react';
import { CreatePositionDialog } from '@/components/positions/CreatePositionDialog';
import { EditPositionDialog } from '@/components/positions/EditPositionDialog';
import { PositionEmbeddingDialog } from '@/components/positions/EmbeddingDialog';
import { InterestedCandidatesDialog } from '@/components/positions/InterestedCandidatesDialog';
import { ExceptionalTalentButton } from '@/components/demo/ExceptionalTalentButton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';

// Position row component that can use hooks
function PositionRow({ 
  position, 
  onDelete, 
  onEdit,
  onViewEmbedding,
  onViewInterestedCandidates,
  generateEmbeddingMutation 
}: { 
  position: Position;
  onDelete: (position: Position) => void;
  onEdit: (position: Position) => void;
  onViewEmbedding: (position: Position) => void;
  onViewInterestedCandidates: (position: Position) => void;
  generateEmbeddingMutation: any;
}) {
  // Check if embedding exists for this position
  const { data: embeddingData, isLoading: embeddingLoading } = useQuery({
    queryKey: ['positionEmbedding', position.id],
    queryFn: () => apiClient.getPositionEmbedding(position.id),
    retry: false,
    refetchOnWindowFocus: false,
  });
  
  const hasEmbedding = !!embeddingData && !embeddingLoading;

  return (
    <TableRow key={position.id}>
      <TableCell className="font-medium">{position.title}</TableCell>
      <TableCell>
        {position.team_id ? (
          <Badge variant="outline">
            <Briefcase className="mr-1 h-3 w-3" />
            {position.team_id.substring(0, 8)}...
          </Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-1">
          {position.must_haves.slice(0, 2).map((skill, idx) => (
            <Badge key={idx} variant="secondary" className="text-xs">
              {skill}
            </Badge>
          ))}
          {position.must_haves.length > 2 && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="secondary" className="text-xs cursor-help">
                    +{position.must_haves.length - 2}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="space-y-1">
                    {position.must_haves.slice(2).map((skill, idx) => (
                      <div key={idx}>{skill}</div>
                    ))}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </TableCell>
      <TableCell>
        <Badge variant={position.status === 'open' ? 'default' : position.status === 'filled' ? 'secondary' : 'outline'}>
          {position.status}
        </Badge>
      </TableCell>
      <TableCell>
        <Badge variant={position.priority === 'high' ? 'destructive' : position.priority === 'medium' ? 'default' : 'secondary'}>
          {position.priority}
        </Badge>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-1">
          {hasEmbedding ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewEmbedding(position)}
                    title="View embedding"
                  >
                    <Brain className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>View embedding</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => generateEmbeddingMutation.mutate(position.id)}
                    disabled={generateEmbeddingMutation.isPending}
                    title="Generate embedding"
                  >
                    <Sparkles className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Generate embedding</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onViewInterestedCandidates(position)}
                  title="View interested candidates"
                >
                  <Users className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>View interested candidates</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.location.href = `/positions/${position.id}/pipeline`}
                  title="View pipeline"
                >
                  <GitBranch className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>View pipeline</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(position)}
            title="Edit position"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(position)}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}

export default function PositionsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [editPosition, setEditPosition] = useState<Position | null>(null);
  const [deletePosition, setDeletePosition] = useState<Position | null>(null);
  const [embeddingPosition, setEmbeddingPosition] = useState<Position | null>(null);
  const [interestedCandidatesPosition, setInterestedCandidatesPosition] = useState<Position | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: positions, isLoading, error } = useQuery({
    queryKey: ['positions'],
    queryFn: () => apiClient.getPositions(),
  });

  const deleteMutation = useMutation({
    mutationFn: async (positionId: string) => {
      await apiClient.deletePosition(positionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      toast({
        title: 'Position deleted',
        description: 'The position has been deleted successfully.',
      });
      setDeletePosition(null);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete position',
        variant: 'destructive',
      });
    },
  });

  const generateEmbeddingMutation = useMutation({
    mutationFn: async (positionId: string) => {
      return await apiClient.generatePositionEmbedding(positionId);
    },
    onSuccess: (_, positionId) => {
      queryClient.invalidateQueries({ queryKey: ['positionEmbedding', positionId] });
      toast({
        title: 'Embedding generated',
        description: 'The embedding has been generated successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to generate embedding',
        variant: 'destructive',
      });
    },
  });

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading positions...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
            <CardDescription>
              {error instanceof Error ? error.message : 'Failed to load positions'}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Positions</h1>
          <p className="text-muted-foreground mt-1">
            Manage job positions and requirements
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ExceptionalTalentButton />
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Position
          </Button>
        </div>
      </div>

      {/* Positions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Positions</CardTitle>
              <CardDescription>
                {positions?.length || 0} position{positions?.length !== 1 ? 's' : ''} total
              </CardDescription>
            </div>
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search positions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {positions && positions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Team</TableHead>
                  <TableHead>Must-Have Skills</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {positions
                  .filter((position) => {
                    if (!searchQuery.trim()) return true;
                    const query = searchQuery.toLowerCase();
                    return (
                      position.title.toLowerCase().includes(query) ||
                      position.description?.toLowerCase().includes(query) ||
                      position.must_haves?.some(skill => skill.toLowerCase().includes(query)) ||
                      position.tech_stack?.some(tech => tech.toLowerCase().includes(query))
                    );
                  })
                  .map((position) => (
                    <PositionRow
                      key={position.id}
                      position={position}
                      onDelete={setDeletePosition}
                      onEdit={setEditPosition}
                      onViewEmbedding={setEmbeddingPosition}
                      onViewInterestedCandidates={setInterestedCandidatesPosition}
                      generateEmbeddingMutation={generateEmbeddingMutation}
                    />
                  ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No positions yet. Create your first position to get started.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <CreatePositionDialog open={createOpen} onOpenChange={setCreateOpen} />

      {/* Edit Dialog */}
      {editPosition && (
        <EditPositionDialog
          position={editPosition}
          open={!!editPosition}
          onOpenChange={(open) => !open && setEditPosition(null)}
        />
      )}

      {/* Embedding Dialog */}
      {embeddingPosition && (
        <PositionEmbeddingDialog
          position={embeddingPosition}
          open={!!embeddingPosition}
          onOpenChange={(open) => !open && setEmbeddingPosition(null)}
        />
      )}

      {/* Interested Candidates Dialog */}
      {interestedCandidatesPosition && (
        <InterestedCandidatesDialog
          position={interestedCandidatesPosition}
          open={!!interestedCandidatesPosition}
          onOpenChange={(open) => !open && setInterestedCandidatesPosition(null)}
        />
      )}

      {/* Delete Confirmation */}
      <AlertDialog open={!!deletePosition} onOpenChange={(open) => !open && setDeletePosition(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Position</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletePosition?.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deletePosition && deleteMutation.mutate(deletePosition.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

