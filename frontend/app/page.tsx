'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Users, 
  Briefcase, 
  UserCheck, 
  TrendingUp, 
  ArrowRight,
  Activity,
  Target,
  Zap
} from 'lucide-react';
import Link from 'next/link';
import { PipelineFlow } from '@/components/dashboard/PipelineFlow';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { PipelineChart } from '@/components/dashboard/PipelineChart';
import { ActivityTimeline } from '@/components/dashboard/ActivityTimeline';

export default function Home() {
  // Fetch all data in parallel
  const { data: teams, isLoading: teamsLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: () => apiClient.getTeams(),
  });

  const { data: positions, isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: () => apiClient.getPositions(),
  });

  const { data: candidates, isLoading: candidatesLoading } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => apiClient.getCandidates(),
  });

  const { data: interviewers, isLoading: interviewersLoading } = useQuery({
    queryKey: ['interviewers'],
    queryFn: () => apiClient.getInterviewers(),
  });

  const isLoading = teamsLoading || positionsLoading || candidatesLoading || interviewersLoading;

  return (
    <div className="p-6 space-y-8 min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Grok Recruiting
            </h1>
            <p className="text-muted-foreground text-lg mt-1">
              AI-powered recruiting platform by xAI
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-muted-foreground">Live</span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <StatsCards 
        teams={teams?.length || 0}
        positions={positions?.length || 0}
        candidates={candidates?.length || 0}
        interviewers={interviewers?.length || 0}
        isLoading={isLoading}
      />

      {/* Main Dashboard Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Pipeline Flow - Takes 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl flex items-center gap-2">
                    <Activity className="h-6 w-6 text-primary" />
                    Pipeline Flow
                  </CardTitle>
                  <CardDescription>
                    Real-time candidate pipeline visualization across all positions
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-64 w-full" />
                </div>
              ) : (
                <PipelineFlow 
                  positions={positions || []}
                  candidates={candidates || []}
                />
              )}
            </CardContent>
          </Card>

          {/* Pipeline Chart */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Target className="h-5 w-5 text-primary" />
                Pipeline Distribution
              </CardTitle>
              <CardDescription>
                Candidate distribution across pipeline stages
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <PipelineChart 
                  positions={positions || []}
                  candidates={candidates || []}
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link href="/teams">
                <div className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <Users className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="font-medium">Teams</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Link>
              <Link href="/positions">
                <div className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <Briefcase className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="font-medium">Positions</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Link>
              <Link href="/candidates">
                <div className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="font-medium">Candidates</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Link>
              <Link href="/graph">
                <div className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <Activity className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="font-medium">Knowledge Graph</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
              </Link>
            </CardContent>
          </Card>

          {/* Activity Timeline */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : (
                <ActivityTimeline 
                  positions={positions || []}
                  candidates={candidates || []}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
