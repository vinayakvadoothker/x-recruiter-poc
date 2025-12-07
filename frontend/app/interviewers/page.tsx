'use client';

import { useState, ReactElement } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Interviewer, Team } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Plus, Pencil, Trash, Brain, Sparkles, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { CreateInterviewerDialog } from '@/components/interviewers/CreateInterviewerDialog';
import { EditInterviewerDialog } from '@/components/interviewers/EditInterviewerDialog';
import { InterviewerEmbeddingDialog } from '@/components/interviewers/EmbeddingDialog';
import { useToast } from '@/hooks/use-toast';

// Interviewer row component that can use hooks
function InterviewerRow({
  interviewer,
  teams,
  onEdit,
  onDelete,
  onViewEmbedding,
  generateEmbeddingMutation,
  getTeamName,
  renderBadge,
  TruncatedText,
}: {
  interviewer: Interviewer;
  teams: Team[];
  onEdit: (interviewer: Interviewer) => void;
  onDelete: (interviewerId: string) => void;
  onViewEmbedding: (interviewer: Interviewer) => void;
  generateEmbeddingMutation: any;
  getTeamName: (teamId?: string) => string | null;
  renderBadge: (items: string[], maxItems?: number, maxLength?: number) => ReactElement;
  TruncatedText: ({ text, maxLength }: { text: string; maxLength?: number }) => ReactElement;
}) {
  // Check if embedding exists for this interviewer
  const { data: embeddingData, isLoading: embeddingLoading } = useQuery({
    queryKey: ['interviewerEmbedding', interviewer.id],
    queryFn: () => apiClient.getInterviewerEmbedding(interviewer.id),
    retry: false,
    refetchOnWindowFocus: false,
  });
  
  const hasEmbedding = !!embeddingData && !embeddingLoading;
  
  return (
    <TableRow key={interviewer.id}>
      <TableCell className="font-medium">
        <TruncatedText text={interviewer.name} maxLength={25} />
      </TableCell>
      <TableCell>
        <TruncatedText text={interviewer.email} maxLength={30} />
      </TableCell>
      <TableCell>
        <TruncatedText text={interviewer.phone_number} maxLength={15} />
      </TableCell>
      <TableCell>
        {interviewer.team_id ? (
          <TruncatedText text={getTeamName(interviewer.team_id) || interviewer.team_id} maxLength={20} />
        ) : (
          <span className="text-muted-foreground text-sm">No team</span>
        )}
      </TableCell>
      <TableCell>{renderBadge(interviewer.expertise)}</TableCell>
      <TableCell>{renderBadge(interviewer.specializations)}</TableCell>
      <TableCell>
        {interviewer.interview_style ? (
          <TruncatedText text={interviewer.interview_style} maxLength={30} />
        ) : (
          <span className="text-muted-foreground">Not specified</span>
        )}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          {hasEmbedding ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewEmbedding(interviewer)}
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
                    onClick={() => generateEmbeddingMutation.mutate(interviewer.id)}
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
            onClick={() => onEdit(interviewer)}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                <Trash className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete the interviewer &quot;{interviewer.name}&quot; and remove their data from our servers.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => onDelete(interviewer.id)}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </TableCell>
    </TableRow>
  );
}

export default function InterviewersPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedInterviewer, setSelectedInterviewer] = useState<Interviewer | null>(null);
  const [embeddingInterviewer, setEmbeddingInterviewer] = useState<Interviewer | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: interviewers = [], isLoading } = useQuery({
    queryKey: ['interviewers'],
    queryFn: () => apiClient.getInterviewers(),
  });

  const { data: teams = [] } = useQuery<Team[]>({
    queryKey: ['teams'],
    queryFn: () => apiClient.getTeams(),
  });

  const getTeamName = (teamId?: string) => {
    if (!teamId || !teams) return null;
    const team = teams.find(t => t.id === teamId);
    return team ? team.name : null;
  };

  const truncateText = (text: string, maxLength: number = 30) => {
    if (!text) return text;
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const TruncatedText = ({ text, maxLength = 30 }: { text: string; maxLength?: number }) => {
    if (!text) return <span className="text-muted-foreground">—</span>;
    const truncated = truncateText(text, maxLength);
    const isTruncated = text.length > maxLength;

    if (isTruncated) {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="cursor-help">{truncated}</span>
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs">{text}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return <span>{text}</span>;
  };

  const deleteMutation = useMutation({
    mutationFn: (interviewerId: string) => apiClient.deleteInterviewer(interviewerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviewers'] });
      toast({
        title: 'Interviewer deleted',
        description: 'The interviewer has been deleted successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const generateEmbeddingMutation = useMutation({
    mutationFn: async (interviewerId: string) => {
      return await apiClient.generateInterviewerEmbedding(interviewerId);
    },
    onSuccess: (_, interviewerId) => {
      queryClient.invalidateQueries({ queryKey: ['interviewerEmbedding', interviewerId] });
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

  const handleEdit = (interviewer: Interviewer) => {
    setSelectedInterviewer(interviewer);
    setEditDialogOpen(true);
  };

  const handleDelete = (interviewerId: string) => {
    deleteMutation.mutate(interviewerId);
  };

  const renderBadge = (items: string[], maxItems: number = 3, maxLength: number = 20) => {
    if (items.length === 0) return <span className="text-muted-foreground">None</span>;
    if (items.length <= maxItems) {
      return (
        <TooltipProvider>
          <div className="flex flex-wrap gap-1">
            {items.map((item, idx) => {
              const truncated = truncateText(item, maxLength);
              const isTruncated = item.length > maxLength;
              const badge = (
                <span
                  key={idx}
                  className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium"
                >
                  {truncated}
                </span>
              );
              
              if (isTruncated) {
                return (
                  <Tooltip key={idx}>
                    <TooltipTrigger asChild>
                      {badge}
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{item}</p>
                    </TooltipContent>
                  </Tooltip>
                );
              }
              return badge;
            })}
          </div>
        </TooltipProvider>
      );
    }
    const visible = items.slice(0, maxItems);
    const remaining = items.slice(maxItems);
    return (
      <TooltipProvider>
        <div className="flex flex-wrap gap-1">
          {visible.map((item, idx) => {
            const truncated = truncateText(item, maxLength);
            const isTruncated = item.length > maxLength;
            const badge = (
              <span
                key={idx}
                className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium"
              >
                {truncated}
              </span>
            );
            
            if (isTruncated) {
              return (
                <Tooltip key={idx}>
                  <TooltipTrigger asChild>
                    {badge}
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{item}</p>
                  </TooltipContent>
                </Tooltip>
              );
            }
            return badge;
          })}
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium cursor-help">
                +{remaining.length}
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <div className="flex flex-col gap-1">
                {remaining.map((item, idx) => (
                  <span key={idx}>{item}</span>
                ))}
              </div>
            </TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading interviewers...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Interviewers</h1>
          <p className="text-muted-foreground mt-1">
            Manage interviewers and their expertise
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Interviewer
        </Button>
      </div>

      {interviewers.length === 0 ? (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground mb-4">No interviewers yet</p>
          <p className="text-sm text-muted-foreground mb-4">
            Create your first interviewer to get started
          </p>
        </div>
      ) : (
        <div className="border rounded-lg">
          <div className="p-4 border-b flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {interviewers.length} interviewer{interviewers.length !== 1 ? 's' : ''} total
            </div>
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search interviewers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Team</TableHead>
                <TableHead>Expertise</TableHead>
                <TableHead>Specializations</TableHead>
                <TableHead>Interview Style</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {interviewers
                .filter((interviewer) => {
                  if (!searchQuery.trim()) return true;
                  const query = searchQuery.toLowerCase();
                  return (
                    interviewer.name.toLowerCase().includes(query) ||
                    interviewer.email?.toLowerCase().includes(query) ||
                    interviewer.phone_number?.toLowerCase().includes(query) ||
                    interviewer.expertise?.some(skill => skill.toLowerCase().includes(query)) ||
                    interviewer.specializations?.some(spec => spec.toLowerCase().includes(query))
                  );
                })
                .map((interviewer) => (
                <InterviewerRow
                  key={interviewer.id}
                  interviewer={interviewer}
                  teams={teams}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onViewEmbedding={setEmbeddingInterviewer}
                  generateEmbeddingMutation={generateEmbeddingMutation}
                  getTeamName={getTeamName}
                  renderBadge={renderBadge}
                  TruncatedText={TruncatedText}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <CreateInterviewerDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
      {selectedInterviewer && (
        <EditInterviewerDialog
          interviewer={selectedInterviewer}
          open={editDialogOpen}
          onOpenChange={(open) => {
            setEditDialogOpen(open);
            if (!open) setSelectedInterviewer(null);
          }}
        />
      )}
      {embeddingInterviewer && (
        <InterviewerEmbeddingDialog
          open={!!embeddingInterviewer}
          onOpenChange={(open) => !open && setEmbeddingInterviewer(null)}
          interviewerId={embeddingInterviewer.id}
          interviewerName={embeddingInterviewer.name}
        />
      )}
    </div>
  );
}

