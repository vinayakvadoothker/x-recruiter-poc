'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Users, Briefcase, UserCheck, TrendingUp, ArrowUpRight } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import { motion } from 'framer-motion';

interface StatsCardsProps {
  teams: number;
  positions: number;
  candidates: number;
  interviewers: number;
  isLoading: boolean;
}

export function StatsCards({ teams, positions, candidates, interviewers, isLoading }: StatsCardsProps) {
  const stats = [
    {
      label: 'Teams',
      value: teams,
      icon: Users,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      href: '/teams',
    },
    {
      label: 'Positions',
      value: positions,
      icon: Briefcase,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
      href: '/positions',
    },
    {
      label: 'Candidates',
      value: candidates,
      icon: TrendingUp,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      href: '/candidates',
    },
    {
      label: 'Interviewers',
      value: interviewers,
      icon: UserCheck,
      color: 'text-amber-500',
      bgColor: 'bg-amber-500/10',
      href: '/interviewers',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Link href={stat.href}>
              <Card className="border-2 hover:border-primary/50 transition-all hover:shadow-lg cursor-pointer group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-6 relative">
                  <div className="flex items-center justify-between">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                      {isLoading ? (
                        <Skeleton className="h-8 w-16" />
                      ) : (
                        <motion.p
                          className="text-3xl font-bold"
                          initial={{ scale: 0.8 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: index * 0.1 + 0.2 }}
                        >
                          {stat.value}
                        </motion.p>
                      )}
                    </div>
                    <div className={`${stat.bgColor} p-3 rounded-lg group-hover:scale-110 transition-transform`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                  </div>
                  <div className="mt-4 flex items-center text-xs text-muted-foreground group-hover:text-primary transition-colors">
                    <span>View all</span>
                    <ArrowUpRight className="h-3 w-3 ml-1" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        );
      })}
    </div>
  );
}

