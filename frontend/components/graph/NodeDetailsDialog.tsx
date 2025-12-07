'use client';

import { useQuery } from '@tanstack/react-query';
import { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { apiClient } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle, Search, X, ChevronDown } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface NodeDetailsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  node: {
    id: string;
    profileType: string;
    metadata: Record<string, unknown>;
  } | null;
}

export function NodeDetailsDialog({
  open,
  onOpenChange,
  node,
}: NodeDetailsDialogProps) {
  const profileType = node?.profileType || '';
  const profileId = node?.id || '';

  // Filter state
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set(['candidates', 'teams', 'interviewers', 'positions']));
  const [minSimilarity, setMinSimilarity] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<'similarity' | 'name'>('similarity');
  const [filtersOpen, setFiltersOpen] = useState<boolean>(false);

  // Get embedding
  const { data: embeddingData, isLoading: embeddingLoading, error: embeddingError } = useQuery({
    queryKey: ['node-embedding', profileType, profileId],
    queryFn: async () => {
      if (profileType === 'candidate') {
        return apiClient.getCandidateEmbedding(profileId);
      } else if (profileType === 'team') {
        return apiClient.getTeamEmbedding(profileId);
      } else if (profileType === 'interviewer') {
        return apiClient.getInterviewerEmbedding(profileId);
      } else if (profileType === 'position') {
        return apiClient.getPositionEmbedding(profileId);
      }
      throw new Error(`Unsupported profile type: ${profileType}`);
    },
    enabled: open && !!node && !!profileType && !!profileId,
  });

  // Get similar embeddings (cross-type by default)
  const { data: similarData, isLoading: similarLoading, error: similarError } = useQuery({
    queryKey: ['similar-embeddings', profileType, profileId],
    queryFn: () => apiClient.getSimilarEmbeddings(profileType, profileId, 20, true),
    enabled: open && !!node && !!profileType && !!profileId,
  });

  const nodeName = node?.metadata?.name || node?.metadata?.title || node?.id || 'Unknown';

  // Filter and sort profiles
  const filteredAndSortedProfiles = useMemo(() => {
    if (!similarData || !similarData.cross_type) return null;

    const grouped = similarData.similar_profiles as {
      candidates: Array<any>;
      teams: Array<any>;
      interviewers: Array<any>;
      positions: Array<any>;
    };

    const result: Record<string, Array<any>> = {
      candidates: [],
      teams: [],
      interviewers: [],
      positions: []
    };

    // Filter by type, similarity, and search query
    Object.entries(grouped).forEach(([type, profiles]) => {
      if (!selectedTypes.has(type)) return;
      if (!profiles || !Array.isArray(profiles)) return;

      const filtered = profiles.filter((profile: any) => {
        // Filter by similarity threshold
        if (profile.similarity < minSimilarity / 100) return false;

        // Filter by search query
        if (searchQuery) {
          const name = (profile.metadata?.name || profile.metadata?.title || profile.profile_id || '').toLowerCase();
          const query = searchQuery.toLowerCase();
          if (!name.includes(query)) return false;
        }

        return true;
      });

      // Sort
      const sorted = [...filtered].sort((a, b) => {
        if (sortBy === 'similarity') {
          return b.similarity - a.similarity;
        } else {
          const nameA = (a.metadata?.name || a.metadata?.title || a.profile_id || '').toLowerCase();
          const nameB = (b.metadata?.name || b.metadata?.title || b.profile_id || '').toLowerCase();
          return nameA.localeCompare(nameB);
        }
      });

      result[type] = sorted;
    });

    return result;
  }, [similarData, selectedTypes, minSimilarity, searchQuery, sortBy]);

  const toggleProfileType = (type: string) => {
    const newSet = new Set(selectedTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setSelectedTypes(newSet);
  };

  const totalFilteredCount = filteredAndSortedProfiles
    ? Object.values(filteredAndSortedProfiles).reduce((sum, profiles) => sum + profiles.length, 0)
    : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>
            {`${profileType.charAt(0).toUpperCase() + profileType.slice(1)}: ${nodeName}`}
          </DialogTitle>
          <DialogDescription>
            {"View embedding details and similar profiles"}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4 min-h-0">
          <Tabs defaultValue="embedding" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="embedding">Embedding</TabsTrigger>
              <TabsTrigger value="similar">Similar Profiles</TabsTrigger>
            </TabsList>

            <TabsContent value="embedding" className="mt-4">
              {embeddingLoading && (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-32 w-full" />
                  <Skeleton className="h-64 w-full" />
                </div>
              )}

              {embeddingError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {embeddingError instanceof Error ? embeddingError.message : 'Failed to load embedding'}
                    {embeddingError instanceof Error && embeddingError.message.includes('404') && (
                      <div className="mt-2 text-sm">
                        This position may not have an embedding yet. Generate one from the positions page.
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}

              {!embeddingLoading && !embeddingError && !embeddingData && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No embedding data available. This position may not have an embedding yet. Generate one from the positions page.
                  </AlertDescription>
                </Alert>
              )}

              {embeddingData && (() => {
                // Normalize embedding data structure (some APIs return 'dimension', others 'embedding_dimension')
                const dimension = (embeddingData as any).dimension || (embeddingData as any).embedding_dimension || embeddingData.embedding?.length || 0;
                const embedding = embeddingData.embedding || [];
                const stats = (embeddingData as any).statistics || {};
                
                // Calculate statistics if not provided
                const min = stats.min !== undefined ? stats.min : (embedding.length > 0 ? Math.min(...embedding) : 0);
                const max = stats.max !== undefined ? stats.max : (embedding.length > 0 ? Math.max(...embedding) : 0);
                const mean = stats.mean !== undefined ? stats.mean : (embedding.length > 0 ? embedding.reduce((a, b) => a + b, 0) / embedding.length : 0);
                const magnitude = stats.magnitude !== undefined ? stats.magnitude : (embedding.length > 0 ? Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0)) : 0);
                
                return (
                  <div className="space-y-6">
                    {/* Embedding Info */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Embedding Dimension:</span>
                        <Badge variant="secondary">{dimension}</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Profile Type:</span>
                        <Badge variant="outline">{embeddingData.profile_type}</Badge>
                      </div>
                    </div>

                    {/* Embedding Vector Preview */}
                    {embedding.length > 0 ? (
                      <div className="space-y-2">
                        <h3 className="text-sm font-semibold">Embedding Vector (First 50 dimensions)</h3>
                        <div className="bg-muted rounded-lg p-4 font-mono text-xs overflow-x-auto">
                          <div className="flex flex-wrap gap-1">
                            {embedding.slice(0, 50).map((value, idx) => (
                              <span
                                key={idx}
                                className="inline-block px-1.5 py-0.5 rounded bg-background"
                                title={`Dimension ${idx + 1}: ${value.toFixed(6)}`}
                              >
                                {value.toFixed(4)}
                              </span>
                            ))}
                          </div>
                          {embedding.length > 50 && (
                            <div className="mt-2 text-muted-foreground text-xs">
                              ... and {embedding.length - 50} more dimensions
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          No embedding vector data available.
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Statistics */}
                    {embedding.length > 0 && (
                      <div className="space-y-2">
                        <h3 className="text-sm font-semibold">Vector Statistics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Min</div>
                            <div className="text-sm font-medium">
                              {min.toFixed(6)}
                            </div>
                          </div>
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Max</div>
                            <div className="text-sm font-medium">
                              {max.toFixed(6)}
                            </div>
                          </div>
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Mean</div>
                            <div className="text-sm font-medium">
                              {mean.toFixed(6)}
                            </div>
                          </div>
                          <div className="space-y-1">
                            <div className="text-xs text-muted-foreground">Magnitude</div>
                            <div className="text-sm font-medium">
                              {magnitude.toFixed(6)}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    {embeddingData.metadata && Object.keys(embeddingData.metadata).length > 0 && (
                      <div className="space-y-2">
                        <h3 className="text-sm font-semibold">Metadata</h3>
                        <div className="bg-muted rounded-lg p-4">
                          <pre className="text-xs overflow-x-auto">
                            {JSON.stringify(embeddingData.metadata, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </TabsContent>

            <TabsContent value="similar" className="mt-4">
              {similarLoading && (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-32 w-full" />
                </div>
              )}

              {similarError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {similarError instanceof Error ? similarError.message : 'Failed to load similar profiles'}
                  </AlertDescription>
                </Alert>
              )}

              {!similarLoading && !similarError && !similarData && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No similar profiles data available. The embedding may not exist yet.
                  </AlertDescription>
                </Alert>
              )}

              {similarData && (
                <div className="space-y-6">
                  {similarData.cross_type ? (
                    // Cross-type results with filters
                    (() => {
                      const profileTypeLabels = {
                        candidates: 'Candidates',
                        teams: 'Teams',
                        interviewers: 'Interviewers',
                        positions: 'Positions'
                      };

                      const originalGrouped = similarData.similar_profiles as {
                        candidates?: Array<any>;
                        teams?: Array<any>;
                        interviewers?: Array<any>;
                        positions?: Array<any>;
                      };

                      const originalTotalCount = 
                        (originalGrouped.candidates?.length || 0) +
                        (originalGrouped.teams?.length || 0) +
                        (originalGrouped.interviewers?.length || 0) +
                        (originalGrouped.positions?.length || 0);
                      
                      // If no results at all, show a helpful message
                      if (originalTotalCount === 0) {
                        return (
                          <Alert>
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                              No similar profiles found. This might be because:
                              <ul className="list-disc list-inside mt-2 space-y-1">
                                <li>This profile doesn't have an embedding yet</li>
                                <li>There are no other profiles in the system</li>
                                <li>The embedding hasn't been synced yet</li>
                              </ul>
                            </AlertDescription>
                          </Alert>
                        );
                      }
                      
                      return (
                        <>
                          {/* Filters - Collapsible */}
                          <Collapsible open={filtersOpen} onOpenChange={setFiltersOpen}>
                            <div className="border rounded-lg bg-muted/50">
                              <CollapsibleTrigger className="w-full">
                                <div className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
                                  <h3 className="text-sm font-semibold">Filters</h3>
                                  <div className="flex items-center gap-2">
                                    <ChevronDown className={`h-4 w-4 transition-transform ${filtersOpen ? 'transform rotate-180' : ''}`} />
                                  </div>
                                </div>
                              </CollapsibleTrigger>
                              <CollapsibleContent>
                                <div className="space-y-4 p-4 pt-0">
                                  <div className="flex items-center justify-end">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => {
                                        setSelectedTypes(new Set(['candidates', 'teams', 'interviewers', 'positions']));
                                        setMinSimilarity(0);
                                        setSearchQuery('');
                                      }}
                                      className="h-7 text-xs"
                                    >
                                      <X className="h-3 w-3 mr-1" />
                                      Reset
                                    </Button>
                                  </div>

                            {/* Profile Type Filter */}
                            <div className="space-y-2">
                              <Label className="text-xs">Profile Types</Label>
                              <div className="flex flex-wrap gap-3">
                                {Object.entries(profileTypeLabels).map(([type, label]) => (
                                  <div key={type} className="flex items-center space-x-2">
                                    <Checkbox
                                      id={`filter-${type}`}
                                      checked={selectedTypes.has(type)}
                                      onCheckedChange={() => toggleProfileType(type)}
                                    />
                                    <Label
                                      htmlFor={`filter-${type}`}
                                      className="text-xs font-normal cursor-pointer"
                                    >
                                      {label}
                                    </Label>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Search and Similarity Filter */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label htmlFor="search" className="text-xs">Search</Label>
                                <div className="relative">
                                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                  <Input
                                    id="search"
                                    placeholder="Search by name..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-8"
                                  />
                                </div>
                              </div>

                              <div className="space-y-2">
                                <Label htmlFor="similarity" className="text-xs">
                                  Min Similarity: {minSimilarity}%
                                </Label>
                                <div className="flex items-center gap-2">
                                  <input
                                    id="similarity"
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={minSimilarity}
                                    onChange={(e) => setMinSimilarity(Number(e.target.value))}
                                    className="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                                  />
                                  <Input
                                    type="number"
                                    min="0"
                                    max="100"
                                    value={minSimilarity}
                                    onChange={(e) => setMinSimilarity(Math.min(100, Math.max(0, Number(e.target.value) || 0)))}
                                    className="w-20 h-8"
                                  />
                                </div>
                              </div>
                            </div>

                            {/* Sort */}
                            <div className="space-y-2">
                              <Label htmlFor="sort" className="text-xs">Sort By</Label>
                              <Select value={sortBy} onValueChange={(value: 'similarity' | 'name') => setSortBy(value)}>
                                <SelectTrigger id="sort" className="w-full">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="similarity">Similarity (High to Low)</SelectItem>
                                  <SelectItem value="name">Name (A to Z)</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                                </div>
                              </CollapsibleContent>
                            </div>
                          </Collapsible>

                          {/* Results Summary */}
                          <div className="text-sm text-muted-foreground">
                            Showing {totalFilteredCount} of {originalTotalCount} similar profiles
                          </div>

                          {/* Filtered Results */}
                          {totalFilteredCount === 0 ? (
                            <Alert>
                              <AlertCircle className="h-4 w-4" />
                              <AlertDescription>
                                No profiles match the current filters. Try adjusting your search criteria.
                              </AlertDescription>
                            </Alert>
                          ) : (
                            <div className="space-y-6">
                              {filteredAndSortedProfiles && Object.entries(filteredAndSortedProfiles).map(([type, profiles]) => {
                                if (profiles.length === 0) return null;
                                
                                return (
                                  <div key={type} className="space-y-3">
                                    <h3 className="text-sm font-semibold flex items-center gap-2">
                                      {profileTypeLabels[type as keyof typeof profileTypeLabels]}
                                      <Badge variant="outline">{profiles.length}</Badge>
                                    </h3>
                                    <div className="space-y-2">
                                      {profiles.map((similar: any) => (
                                        <div
                                          key={similar.profile_id}
                                          className="border rounded-lg p-4 space-y-2"
                                        >
                                          <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                              <span className="font-medium">
                                                {similar.metadata?.name || similar.metadata?.title || similar.profile_id}
                                              </span>
                                              <Badge variant="outline">{similar.profile_type}</Badge>
                                            </div>
                                            <div className="flex items-center gap-2">
                                              <Badge variant="secondary" className="font-mono">
                                                {(similar.similarity * 100).toFixed(1)}% similar
                                              </Badge>
                                            </div>
                                          </div>
                                          {similar.metadata && Object.keys(similar.metadata).length > 0 && (
                                            <div className="text-xs text-muted-foreground">
                                              <details>
                                                <summary className="cursor-pointer hover:text-foreground">
                                                  View metadata
                                                </summary>
                                                <pre className="mt-2 bg-muted p-2 rounded text-xs overflow-x-auto">
                                                  {JSON.stringify(similar.metadata, null, 2)}
                                                </pre>
                                              </details>
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </>
                      );
                    })()
                  ) : (
                    // Same-type results - flat list (no filters for now)
                    (() => {
                      const profiles = similarData.similar_profiles as Array<any>;
                      return (
                        <>
                          <div className="text-sm text-muted-foreground">
                            Found {profiles.length} similar {profileType}s
                          </div>
                          
                          {profiles.length === 0 ? (
                            <Alert>
                              <AlertCircle className="h-4 w-4" />
                              <AlertDescription>
                                No similar profiles found. This might be the only {profileType} in the system.
                              </AlertDescription>
                            </Alert>
                          ) : (
                            <div className="space-y-3">
                              {profiles.map((similar) => (
                                <div
                                  key={similar.profile_id}
                                  className="border rounded-lg p-4 space-y-2"
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <span className="font-medium">
                                        {similar.metadata?.name || similar.metadata?.title || similar.profile_id}
                                      </span>
                                      <Badge variant="outline">{similar.profile_type}</Badge>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <Badge variant="secondary" className="font-mono">
                                        {(similar.similarity * 100).toFixed(1)}% similar
                                      </Badge>
                                    </div>
                                  </div>
                                  {similar.metadata && Object.keys(similar.metadata).length > 0 && (
                                    <div className="text-xs text-muted-foreground">
                                      <details>
                                        <summary className="cursor-pointer hover:text-foreground">
                                          View metadata
                                        </summary>
                                        <pre className="mt-2 bg-muted p-2 rounded text-xs overflow-x-auto">
                                          {JSON.stringify(similar.metadata, null, 2)}
                                        </pre>
                                      </details>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      );
                    })()
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>
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

