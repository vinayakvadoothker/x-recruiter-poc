'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import dynamic from 'next/dynamic';
import { useState, useMemo } from 'react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Search, ChevronDown, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

// Dynamically import EmbeddingsGraph with SSR disabled
const EmbeddingsGraph = dynamic(
  () => import('@/components/graph/EmbeddingsGraph').then((mod) => mod.EmbeddingsGraph),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[600px] flex items-center justify-center bg-black rounded-lg">
        <div className="text-muted-foreground">Loading 3D visualization...</div>
      </div>
    ),
  }
);

export default function GraphPage() {
  const queryClient = useQueryClient();
  
  // Filter state - must be before any conditional returns
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set(['candidates', 'teams', 'interviewers', 'positions']));
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filtersOpen, setFiltersOpen] = useState<boolean>(false);
  
  // Sync embeddings when manually triggered
  const syncMutation = useMutation({
    mutationFn: () => apiClient.syncEmbeddings(),
    onSuccess: () => {
      // Refetch graph data after sync
      queryClient.invalidateQueries({ queryKey: ['embeddings-graph'] });
    },
  });
  
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['embeddings-graph'],
    queryFn: () => apiClient.getEmbeddingsForGraph(),
  });

  // Filter and transform data - must be before conditional returns
  const filteredData = useMemo(() => {
    if (!data) return null;

    const filtered = {
      ...data,
      embeddings: {
        candidates: [] as typeof data.embeddings.candidates,
        teams: [] as typeof data.embeddings.teams,
        interviewers: [] as typeof data.embeddings.interviewers,
        positions: [] as typeof data.embeddings.positions,
      },
      total_points: 0,
    };

    // Filter by type and search query
    Object.entries(data.embeddings).forEach(([type, points]) => {
      if (!selectedTypes.has(type)) return;

      const filteredPoints = points.filter((point) => {
        // Filter by search query
        if (searchQuery) {
          const name = (point.metadata?.name || point.metadata?.title || point.profile_id || '').toLowerCase();
          const query = searchQuery.toLowerCase();
          if (!name.includes(query)) return false;
        }
        return true;
      });

      filtered.embeddings[type as keyof typeof filtered.embeddings] = filteredPoints as any;
      filtered.total_points += filteredPoints.length;
    });

    return filtered;
  }, [data, selectedTypes, searchQuery]);

  const toggleProfileType = (type: string) => {
    const newSet = new Set(selectedTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setSelectedTypes(newSet);
  };

  const profileTypeLabels = {
    candidates: 'Candidates',
    teams: 'Teams',
    interviewers: 'Interviewers',
    positions: 'Positions'
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-[600px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-destructive">
              <p className="text-lg font-semibold">Error loading embeddings</p>
              <p className="text-sm mt-2">{error instanceof Error ? error.message : 'Unknown error'}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSync = () => {
    syncMutation.mutate();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Recruiting Graph</h1>
          <p className="text-muted-foreground">
            Interactive 3D visualization of all vectors in the knowledge graph.
            Explore candidates, teams, interviewers, and positions in 3D space.
          </p>
        </div>
        <Button
          onClick={handleSync}
          disabled={syncMutation.isPending || isLoading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
          {syncMutation.isPending ? 'Syncing...' : 'Sync Embeddings'}
        </Button>
      </div>

      {syncMutation.isSuccess && syncMutation.data && (
        <Card className="bg-muted/50">
          <CardContent className="p-4">
            <div className="text-sm space-y-1">
              <div className="font-semibold">Sync Complete</div>
              <div className="text-muted-foreground">
                Created: {syncMutation.data.summary.total_created} | 
                Updated: {syncMutation.data.summary.total_updated} | 
                Total: {syncMutation.data.summary.total_processed}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Knowledge Graph Visualization</CardTitle>
              <CardDescription>
                {filteredData?.total_points || 0} of {data?.total_points || 0} total points across all profile types
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0 px-6 pb-6 space-y-4">
          {/* Search and Filters - Same Line */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 space-y-2">
              <Label htmlFor="graph-search" className="text-sm">Search</Label>
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="graph-search"
                  placeholder="Search by name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
                {searchQuery && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 h-7 w-7 p-0"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>

            {/* Filters - Collapsible */}
            <div className="flex-1">
              <Label className="text-sm mb-2 block">Profile Type Filters</Label>
              <Collapsible open={filtersOpen} onOpenChange={setFiltersOpen}>
                <div className="border rounded-lg bg-muted/50">
                  <CollapsibleTrigger className="w-full">
                    <div className="flex items-center justify-between p-3 hover:bg-muted/50 transition-colors">
                      <span className="text-sm font-medium">
                        {Array.from(selectedTypes).length} of {Object.keys(profileTypeLabels).length} types selected
                      </span>
                      <div className="flex items-center gap-2">
                        <ChevronDown className={`h-4 w-4 transition-transform ${filtersOpen ? 'transform rotate-180' : ''}`} />
                      </div>
                    </div>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div className="p-3 pt-0 space-y-3">
                      <div className="flex flex-wrap gap-4">
                        {Object.entries(profileTypeLabels).map(([type, label]) => {
                          const count = data?.embeddings[type as keyof typeof data.embeddings]?.length || 0;
                          return (
                            <div key={type} className="flex items-center space-x-2">
                              <Checkbox
                                id={`filter-${type}`}
                                checked={selectedTypes.has(type)}
                                onCheckedChange={() => toggleProfileType(type)}
                              />
                              <Label
                                htmlFor={`filter-${type}`}
                                className="text-sm font-normal cursor-pointer flex items-center gap-2"
                              >
                                {label}
                                <Badge variant="outline" className="text-xs">
                                  {count}
                                </Badge>
                              </Label>
                            </div>
                          );
                        })}
                      </div>
                      <div className="flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedTypes(new Set(['candidates', 'teams', 'interviewers', 'positions']));
                            setSearchQuery('');
                          }}
                          className="h-7 text-xs"
                        >
                          <X className="h-3 w-3 mr-1" />
                          Reset Filters
                        </Button>
                      </div>
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            </div>
          </div>

          {/* Graph Visualization */}
          <div className="border rounded-lg overflow-hidden">
            {filteredData && <EmbeddingsGraph data={filteredData} />}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

