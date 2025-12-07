'use client';

import { useMemo, useRef, useCallback, useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Focus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { NodeDetailsDialog } from './NodeDetailsDialog';

// Dynamically import to avoid SSR issues
const ForceGraph3D = dynamic(() => import('react-force-graph-3d').then((mod) => mod.default), {
  ssr: false,
});

interface EmbeddingPoint {
  profile_id: string;
  profile_type: string;
  position: { x: number; y: number; z: number };
  explained_variance: { x: number; y: number; z: number };
  metadata: Record<string, unknown>;
}

interface EmbeddingsGraphData {
  embeddings: {
    candidates: EmbeddingPoint[];
    teams: EmbeddingPoint[];
    interviewers: EmbeddingPoint[];
    positions: EmbeddingPoint[];
  };
  total_points: number;
  company_id: string;
}

interface EmbeddingsGraphProps {
  data: EmbeddingsGraphData;
}

// Color mapping for different profile types
const PROFILE_COLORS: Record<string, string> = {
  candidate: '#3b82f6', // Blue
  team: '#10b981', // Green
  interviewer: '#f59e0b', // Amber
  position: '#8b5cf6', // Purple
};

export function EmbeddingsGraph({ data }: EmbeddingsGraphProps) {
  const graphRef = useRef<any>(null);
  const [selectedNode, setSelectedNode] = useState<{
    id: string;
    profileType: string;
    metadata: Record<string, unknown>;
  } | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  // Convert embedding data to graph format (nodes only, no links)
  const graphData = useMemo(() => {
    console.log('📊 EmbeddingsGraph - Raw data received:', data);
    console.log('📊 EmbeddingsGraph - Total points:', data.total_points);
    
    const nodes: any[] = [];
    let skippedCount = 0;
    
    // Add all embedding points as nodes
    Object.entries(data.embeddings).forEach(([type, points]) => {
      console.log(`📊 ${type}: ${points.length} points`);
      points.forEach((point, index) => {
        // Skip points without position data
        if (!point.position || typeof point.position.x !== 'number' || typeof point.position.y !== 'number' || typeof point.position.z !== 'number') {
          skippedCount++;
          if (index < 3) { // Log first few skipped points for debugging
            console.warn(`⚠️ Skipping point without valid position:`, point);
          }
          return;
        }
        
        nodes.push({
          id: point.profile_id,
          profileType: point.profile_type,
          color: PROFILE_COLORS[point.profile_type] || '#888888',
          x: point.position.x,
          y: point.position.y,
          z: point.position.z,
          metadata: point.metadata,
        });
      });
  });

    console.log(`📊 Graph data: ${nodes.length} nodes created, ${skippedCount} skipped`);
    console.log('📊 Sample nodes (first 3):', nodes.slice(0, 3));

    return {
      nodes,
      links: [], // No links for now - just point cloud visualization
    };
  }, [data]);

  // Function to refocus camera on nodes (optionally filtered)
  const handleRefocus = useCallback((nodesToFocus?: any[]) => {
    if (!graphRef.current) return;

    const nodes = nodesToFocus || graphData.nodes;
    if (nodes.length === 0) return;

    // Calculate bounding box of nodes
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;

    nodes.forEach((node: any) => {
      minX = Math.min(minX, node.x);
      maxX = Math.max(maxX, node.x);
      minY = Math.min(minY, node.y);
      maxY = Math.max(maxY, node.y);
      minZ = Math.min(minZ, node.z);
      maxZ = Math.max(maxZ, node.z);
    });

    // Calculate center point
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const centerZ = (minZ + maxZ) / 2;

    // Calculate distance to fit all nodes in view
    const rangeX = maxX - minX;
    const rangeY = maxY - minY;
    const rangeZ = maxZ - minZ;
    const maxRange = Math.max(rangeX, rangeY, rangeZ);
    const distance = maxRange > 0 ? maxRange * 2.5 : 100; // Scale factor to ensure all nodes are visible

    // Set camera position to look at center from a distance
    graphRef.current.cameraPosition(
      { x: centerX, y: centerY, z: centerZ + distance },
      { x: centerX, y: centerY, z: centerZ },
      1000 // Animation duration in ms (faster for search)
    );
  }, [graphData.nodes]);

  // Auto-zoom to filtered nodes when graph data changes
  useEffect(() => {
    if (graphData.nodes.length > 0) {
      // Small delay to ensure graph is rendered
      const timer = setTimeout(() => {
        handleRefocus();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [graphData.nodes, handleRefocus]);

  return (
    <div className="w-full h-[600px] bg-black rounded-lg overflow-hidden relative">
      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        nodeLabel={(node: any) => {
          const metadata = node.metadata || {};
          const name = metadata.name || metadata.title || node.id;
          return `${node.profileType}: ${name}`;
        }}
        nodeColor={(node: any) => node.color}
        nodeOpacity={0.8}
        nodeResolution={8}
        linkOpacity={0}
        backgroundColor="#000000"
        showNavInfo={false}
        nodeVal={(node: any) => 2}
        onNodeHover={(node: any) => {
          if (node) {
            // Optional: show tooltip or highlight
          }
        }}
        onNodeClick={(node: any) => {
          if (node) {
            setSelectedNode({
              id: node.id,
              profileType: node.profileType,
              metadata: node.metadata || {},
            });
            setDialogOpen(true);
          }
        }}
      />
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-black/80 backdrop-blur-sm rounded-lg p-4 space-y-2 z-10">
        <div className="text-sm font-semibold text-white mb-2">Profile Types</div>
        {Object.entries(PROFILE_COLORS).map(([type, color]) => {
          const count = data.embeddings[type === 'candidate' ? 'candidates' : type === 'team' ? 'teams' : type === 'interviewer' ? 'interviewers' : 'positions'].length;
          return (
            <div key={type} className="flex items-center gap-2 text-xs">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-white capitalize">{type}s</span>
              <span className="text-muted-foreground">({count})</span>
            </div>
          );
        })}
      </div>
      
      {/* Controls hint */}
      <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-sm rounded-lg p-3 text-xs text-muted-foreground z-10">
        <div>🖱️ Drag to rotate</div>
        <div>🔍 Scroll to zoom</div>
        <div>👆 Click & drag nodes</div>
      </div>

      {/* Refocus button */}
      <div className="absolute top-4 left-4 z-10">
        <Button
          onClick={() => handleRefocus()}
          size="icon"
          variant="secondary"
          className="bg-black/80 backdrop-blur-sm hover:bg-black/90 border border-white/10"
          title="Refocus on all visible nodes"
        >
          <Focus className="h-4 w-4 text-white" />
        </Button>
      </div>

      {/* Node Details Dialog */}
      <NodeDetailsDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        node={selectedNode}
      />
    </div>
  );
}
