'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useRouter } from 'next/navigation';

export function CandidateSearchDialog() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [requiredSkills, setRequiredSkills] = useState('');
  const [excludedSkills, setExcludedSkills] = useState('');
  const [minArxiv, setMinArxiv] = useState('');
  const [minGithub, setMinGithub] = useState('');
  const router = useRouter();

  const { data: results, isLoading, refetch } = useQuery({
    queryKey: ['candidateSearch', query, requiredSkills, excludedSkills, minArxiv, minGithub],
    queryFn: () => apiClient.searchCandidates({
      query: query || undefined,
      required_skills: requiredSkills ? requiredSkills.split(',').map(s => s.trim()).filter(Boolean) : undefined,
      excluded_skills: excludedSkills ? excludedSkills.split(',').map(s => s.trim()).filter(Boolean) : undefined,
      min_arxiv_papers: minArxiv ? parseInt(minArxiv) : undefined,
      min_github_stars: minGithub ? parseInt(minGithub) : undefined,
      top_k: 50,
    }),
    enabled: open,
  });

  const handleSearch = () => {
    refetch();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Search className="h-4 w-4 mr-2" />
          Search Candidates
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Search Candidates</DialogTitle>
          <DialogDescription>
            Search candidates using semantic similarity, skills, and filters
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Semantic Query</label>
              <Input
                placeholder="e.g., CUDA expert with GPU experience"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Required Skills (comma-separated)</label>
              <Input
                placeholder="e.g., CUDA, PyTorch, C++"
                value={requiredSkills}
                onChange={(e) => setRequiredSkills(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Excluded Skills (comma-separated)</label>
              <Input
                placeholder="e.g., React, JavaScript"
                value={excludedSkills}
                onChange={(e) => setExcludedSkills(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Min arXiv Papers</label>
              <Input
                type="number"
                placeholder="e.g., 5"
                value={minArxiv}
                onChange={(e) => setMinArxiv(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Min GitHub Stars</label>
              <Input
                type="number"
                placeholder="e.g., 500"
                value={minGithub}
                onChange={(e) => setMinGithub(e.target.value)}
              />
            </div>
          </div>

          <Button onClick={handleSearch} disabled={isLoading} className="w-full">
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search
              </>
            )}
          </Button>

          {results && (
            <div className="mt-4">
              <div className="text-sm text-muted-foreground mb-2">
                Found {results.count} candidate{results.count !== 1 ? 's' : ''}
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Skills</TableHead>
                    <TableHead>Domains</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.candidates.slice(0, 20).map((candidate: any) => (
                    <TableRow key={candidate.id || candidate.candidate_id}>
                      <TableCell className="font-medium">
                        {candidate.name || candidate.candidate_id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {(candidate.skills || []).slice(0, 3).map((skill: string, idx: number) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {(candidate.domains || []).slice(0, 2).map((domain: string, idx: number) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {domain}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const id = candidate.id || candidate.candidate_id || candidate.x_handle;
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

