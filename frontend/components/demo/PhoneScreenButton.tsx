'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Phone, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
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

interface PhoneScreenButtonProps {
  candidateId: string;
  positionId: string;
  candidateName?: string;
  onSuccess?: () => void;
}

export function PhoneScreenButton({ candidateId, positionId, candidateName, onSuccess }: PhoneScreenButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { toast } = useToast();

  const handlePhoneScreen = async () => {
    setIsLoading(true);
    try {
      const result = await apiClient.phoneScreenAndMatch(candidateId, positionId);
      setResult(result);
      
      if (result.decision === 'PASS') {
        toast({
          title: '✅ Phone Screen Passed!',
          description: `Candidate matched to team and interviewer. Pipeline updated.`,
        });
        onSuccess?.();
      } else {
        toast({
          title: '❌ Phone Screen Failed',
          description: result.analysis?.reasoning || 'Candidate did not pass phone screen.',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to conduct phone screen',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="default" size="sm" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              Calling...
            </>
          ) : (
            <>
              <Phone className="h-4 w-4 mr-1" />
              Phone Screen
            </>
          )}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle>Conduct Phone Screen</AlertDialogTitle>
          <AlertDialogDescription>
            {candidateName 
              ? `Conduct automated phone screen interview for ${candidateName}?`
              : `Conduct automated phone screen interview?`}
            <br />
            <br />
            This will:
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Call the candidate via Vapi</li>
              <li>Analyze the transcript with Grok</li>
              <li>Determine pass/fail decision</li>
              <li>If pass: Automatically match to team and interviewer</li>
            </ul>
          </AlertDialogDescription>
        </AlertDialogHeader>
        
        {result && (
          <div className="my-4 p-4 rounded-lg border">
            <div className="flex items-center gap-2 mb-2">
              {result.decision === 'PASS' ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600" />
              )}
              <span className="font-semibold">Decision: {result.decision}</span>
            </div>
            {result.analysis?.reasoning && (
              <p className="text-sm text-muted-foreground">{result.analysis.reasoning}</p>
            )}
            {result.team_match && (
              <div className="mt-2 text-sm">
                <strong>Matched Team:</strong> {result.team_match.team_id}
              </div>
            )}
            {result.interviewer_match && (
              <div className="mt-1 text-sm">
                <strong>Matched Interviewer:</strong> {result.interviewer_match.interviewer_id}
              </div>
            )}
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handlePhoneScreen}
            disabled={isLoading}
            className="bg-primary"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              'Start Phone Screen'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

