'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Team } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus, Edit, Users, Building2, Trash2, Brain, Sparkles, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import Link from 'next/link';
import { useState } from 'react';
import { CreateTeamDialog } from '@/components/teams/CreateTeamDialog';
import { EditTeamDialog } from '@/components/teams/EditTeamDialog';
import { TeamEmbeddingDialog } from '@/components/teams/EmbeddingDialog';
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

// Team row component that can use hooks
function TeamRow({ 
  team, 
  onEdit, 
  onDelete, 
  onViewEmbedding,
  generateEmbeddingMutation 
}: { 
  team: Team;
  onEdit: (team: Team) => void;
  onDelete: (team: Team) => void;
  onViewEmbedding: (team: Team) => void;
  generateEmbeddingMutation: any;
}) {
  // Check if embedding exists for this team
  const { data: embeddingData, isLoading: embeddingLoading } = useQuery({
    queryKey: ['teamEmbedding', team.id],
    queryFn: () => apiClient.getTeamEmbedding(team.id),
    retry: false,
    refetchOnWindowFocus: false,
  });
  
  const hasEmbedding = !!embeddingData && !embeddingLoading;

  return (
                  <TableRow key={team.id}>
                    <TableCell className="font-medium">{team.name}</TableCell>
                    <TableCell>
                      {team.department ? (
                        <Badge variant="outline">
                          <Building2 className="mr-1 h-3 w-3" />
                          {team.department}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {team.expertise.slice(0, 2).map((exp, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {exp}
                          </Badge>
                        ))}
                        {team.expertise.length > 2 && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge variant="secondary" className="text-xs cursor-help">
                                  +{team.expertise.length - 2}
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <div className="space-y-1">
                                  {team.expertise.slice(2).map((exp, idx) => (
                                    <div key={idx}>{exp}</div>
                                  ))}
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {team.stack.slice(0, 2).map((tech, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {tech}
                          </Badge>
                        ))}
                        {team.stack.length > 2 && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge variant="outline" className="text-xs cursor-help">
                                  +{team.stack.length - 2}
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <div className="space-y-1">
                                  {team.stack.slice(2).map((tech, idx) => (
                                    <div key={idx}>{tech}</div>
                                  ))}
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{team.member_count}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{team.open_positions.length}</Badge>
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
                    onClick={() => onViewEmbedding(team)}
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
                    onClick={() => generateEmbeddingMutation.mutate(team.id)}
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
                        <Button
                          variant="ghost"
                          size="sm"
            onClick={() => onEdit(team)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
            onClick={() => onDelete(team)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
  );
}

export default function TeamsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [editTeam, setEditTeam] = useState<Team | null>(null);
  const [deleteTeam, setDeleteTeam] = useState<Team | null>(null);
  const [embeddingTeam, setEmbeddingTeam] = useState<Team | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: teams, isLoading, error } = useQuery({
    queryKey: ['teams'],
    queryFn: () => apiClient.getTeams(),
  });

  const deleteMutation = useMutation({
    mutationFn: async (teamId: string) => {
      await apiClient.deleteTeam(teamId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Team deleted',
        description: 'The team has been deleted successfully.',
      });
      setDeleteTeam(null);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete team',
        variant: 'destructive',
      });
    },
  });

  const generateEmbeddingMutation = useMutation({
    mutationFn: async (teamId: string) => {
      return await apiClient.generateTeamEmbedding(teamId);
    },
    onSuccess: (_, teamId) => {
      queryClient.invalidateQueries({ queryKey: ['teamEmbedding', teamId] });
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
          <div className="text-muted-foreground">Loading teams...</div>
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
              {error instanceof Error ? error.message : 'Failed to load teams'}
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
          <h1 className="text-3xl font-bold tracking-tight">Teams</h1>
          <p className="text-muted-foreground mt-1">
            Manage teams and their requirements
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Team
        </Button>
      </div>

      {/* Teams Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Teams</CardTitle>
              <CardDescription>
                {teams?.length || 0} team{teams?.length !== 1 ? 's' : ''} total
              </CardDescription>
            </div>
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search teams..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {teams && teams.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Expertise</TableHead>
                  <TableHead>Stack</TableHead>
                  <TableHead>Members</TableHead>
                  <TableHead>Open Positions</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teams
                  .filter((team) => {
                    if (!searchQuery.trim()) return true;
                    const query = searchQuery.toLowerCase();
                    return (
                      team.name.toLowerCase().includes(query) ||
                      team.department?.toLowerCase().includes(query) ||
                      team.expertise?.some(skill => skill.toLowerCase().includes(query)) ||
                      team.stack?.some(tech => tech.toLowerCase().includes(query))
                    );
                  })
                  .map((team) => (
                  <TeamRow
                    key={team.id}
                    team={team}
                    onEdit={setEditTeam}
                    onDelete={setDeleteTeam}
                    onViewEmbedding={setEmbeddingTeam}
                    generateEmbeddingMutation={generateEmbeddingMutation}
                  />
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No teams yet. Click "Create Team" above to get started.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialogs */}
      <CreateTeamDialog open={createOpen} onOpenChange={setCreateOpen} />
      {editTeam && (
        <EditTeamDialog
          team={editTeam}
          open={!!editTeam}
          onOpenChange={(open) => !open && setEditTeam(null)}
        />
      )}
      {embeddingTeam && (
        <TeamEmbeddingDialog
          open={!!embeddingTeam}
          onOpenChange={(open) => !open && setEmbeddingTeam(null)}
          teamId={embeddingTeam.id}
          teamName={embeddingTeam.name}
        />
      )}
      <AlertDialog open={!!deleteTeam} onOpenChange={(open) => !open && setDeleteTeam(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Team</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteTeam?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteTeam && deleteMutation.mutate(deleteTeam.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

