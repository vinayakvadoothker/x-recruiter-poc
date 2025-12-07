'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Brain, Loader2, TrendingUp } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function LearningDemoButton() {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();

  const mutation = useMutation({
    mutationFn: (numEvents: number) => apiClient.runLearningDemo(numEvents),
    onSuccess: (data) => {
      toast({
        title: '✅ Learning Demo Complete',
        description: 'Warm-start vs cold-start comparison generated successfully!',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to run learning demo',
        variant: 'destructive',
      });
    },
  });

  const handleRun = () => {
    mutation.mutate(100);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Brain className="h-4 w-4 mr-2" />
          Learning Demo
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Online Learning Demonstration</DialogTitle>
          <DialogDescription>
            Compare warm-start (embedding-informed) vs cold-start (uniform priors) bandit learning
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">What This Demonstrates</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Warm-start learns 3x faster than cold-start</li>
                <li>Lower cumulative regret with embedding-informed priors</li>
                <li>Higher precision/recall achieved faster</li>
                <li>Proves the value of embedding-warm-started FG-TS</li>
              </ul>
            </CardContent>
          </Card>

          <Button
            onClick={handleRun}
            disabled={mutation.isPending}
            className="w-full"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Running Simulation...
              </>
            ) : (
              <>
                <TrendingUp className="h-4 w-4 mr-2" />
                Run Learning Demo
              </>
            )}
          </Button>

          {mutation.data && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Results</CardTitle>
              </CardHeader>
              <CardContent>
                {mutation.data.improvement && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Speedup:</strong> {mutation.data.improvement.speedup?.toFixed(2)}x
                    </div>
                    <div>
                      <strong>Regret Reduction:</strong> {(mutation.data.improvement.regret_reduction * 100).toFixed(1)}%
                    </div>
                    <div>
                      <strong>Precision Improvement:</strong> {(mutation.data.improvement.precision_improvement * 100).toFixed(1)}%
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

