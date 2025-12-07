'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient, Position } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Sparkles, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useRouter } from 'next/navigation';

interface ExceptionalTalentButtonProps {
  positionId?: string;
}

export function ExceptionalTalentButton({ positionId: initialPositionId }: ExceptionalTalentButtonProps) {
  const [open, setOpen] = useState(false);
  const [posId, setPosId] = useState(initialPositionId || '');
  const { toast } = useToast();
  const router = useRouter();

  // Fetch positions for dropdown
  const { data: positions } = useQuery({
    queryKey: ['positions'],
    queryFn: () => apiClient.getPositions(),
    enabled: open, // Only fetch when dialog is open
  });

  const mutation = useMutation({
    mutationFn: ({ positionId, minScore, topK }: { positionId: string; minScore: number; topK: number }) =>
      apiClient.findExceptionalTalent(positionId, minScore, topK),
    onSuccess: () => {
      toast({
        title: '✅ Exceptional Talent Found',
        description: 'The "next Elon" candidates have been identified!',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to find exceptional talent',
        variant: 'destructive',
      });
    },
  });

  const handleSearch = () => {
    if (!posId) {
      toast({
        title: 'Error',
        description: 'Please enter a position ID',
        variant: 'destructive',
      });
      return;
    }
    mutation.mutate({ positionId: posId, minScore: 0.90, topK: 20 });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Sparkles className="h-4 w-4 mr-2" />
          Find "Next Elon"
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Find Exceptional Talent</DialogTitle>
          <DialogDescription>
            Find the "next Elon" - truly exceptional candidates (0.0001% pass rate) for a specific position
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="position-select">Select Position</Label>
            <Select
              value={posId}
              onValueChange={setPosId}
            >
              <SelectTrigger id="position-select">
                <SelectValue placeholder="Choose a position..." />
              </SelectTrigger>
              <SelectContent>
                {positions?.map((position: Position) => (
                  <SelectItem key={position.id} value={position.id}>
                    {position.title} ({position.id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleSearch}
            disabled={mutation.isPending || !posId}
            className="w-full"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Find Exceptional Talent
              </>
            )}
          </Button>

          {mutation.data && (
            <div className="mt-4">
              <div className="text-sm text-muted-foreground mb-2">
                Found {mutation.data.count} exceptional candidate{mutation.data.count !== 1 ? 's' : ''}
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>ELON Score</TableHead>
                    <TableHead>Position Fit</TableHead>
                    <TableHead>Why Exceptional</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mutation.data.candidates.map((candidate: any) => (
                    <TableRow key={candidate.candidate_id || candidate.id}>
                      <TableCell className="font-medium">
                        {candidate.name || candidate.candidate_id}
                      </TableCell>
                      <TableCell>
                        <Badge variant="default">
                          {((candidate.combined_score || candidate.exceptional_score || 0) * 100).toFixed(1)}%
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {candidate.position_fit && (
                          <Badge variant="secondary">
                            {(candidate.position_fit * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground max-w-md">
                        {candidate.why_exceptional || 'Truly exceptional candidate'}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const id = candidate.candidate_id || candidate.id;
                            if (id) {
                              router.push(`/candidates/${id}`);
                              setOpen(false);
                            }
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

