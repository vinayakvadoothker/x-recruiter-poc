'use client';

import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Briefcase, User, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Position {
  id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
}

interface Candidate {
  id?: string;
  x_handle: string;
  name?: string;
  latest_comment_at?: string | null;
  first_seen_at?: string | null;
}

interface ActivityTimelineProps {
  positions: Position[];
  candidates: Candidate[];
}

export function ActivityTimeline({ positions, candidates }: ActivityTimelineProps) {
  const activities = useMemo(() => {
    const items: Array<{
      type: 'position' | 'candidate';
      title: string;
      subtitle: string;
      time: string;
      timestamp: Date;
    }> = [];

    // Add position activities
    positions.forEach(position => {
      if (position.created_at) {
        items.push({
          type: 'position',
          title: position.title,
          subtitle: 'Position created',
          time: formatDistanceToNow(new Date(position.created_at), { addSuffix: true }),
          timestamp: new Date(position.created_at),
        });
      }
      if (position.updated_at && position.updated_at !== position.created_at) {
        items.push({
          type: 'position',
          title: position.title,
          subtitle: 'Position updated',
          time: formatDistanceToNow(new Date(position.updated_at), { addSuffix: true }),
          timestamp: new Date(position.updated_at),
        });
      }
    });

    // Add candidate activities
    candidates.forEach(candidate => {
      if (candidate.latest_comment_at) {
        items.push({
          type: 'candidate',
          title: candidate.name || candidate.x_handle,
          subtitle: 'Latest activity',
          time: formatDistanceToNow(new Date(candidate.latest_comment_at), { addSuffix: true }),
          timestamp: new Date(candidate.latest_comment_at),
        });
      } else if (candidate.first_seen_at) {
        items.push({
          type: 'candidate',
          title: candidate.name || candidate.x_handle,
          subtitle: 'First seen',
          time: formatDistanceToNow(new Date(candidate.first_seen_at), { addSuffix: true }),
          timestamp: new Date(candidate.first_seen_at),
        });
      }
    });

    // Sort by timestamp (most recent first)
    return items.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()).slice(0, 5);
  }, [positions, candidates]);

  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center space-y-2">
        <Clock className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, index) => (
        <div key={index} className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors">
          <div className={`p-2 rounded-lg ${
            activity.type === 'position' 
              ? 'bg-purple-500/10 text-purple-500' 
              : 'bg-blue-500/10 text-blue-500'
          }`}>
            {activity.type === 'position' ? (
              <Briefcase className="h-4 w-4" />
            ) : (
              <User className="h-4 w-4" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <p className="font-medium text-sm truncate">{activity.title}</p>
              <Badge variant="outline" className="text-xs shrink-0">
                {activity.type}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">{activity.subtitle}</p>
            <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

