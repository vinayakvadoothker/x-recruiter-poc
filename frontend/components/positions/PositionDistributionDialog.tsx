'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Sparkles, X as XIcon } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

interface PositionDistributionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  positionId: string;
}

export function PositionDistributionDialog({
  open,
  onOpenChange,
  positionId,
}: PositionDistributionDialogProps) {
  const { toast } = useToast();
  const [availableToGrok, setAvailableToGrok] = useState(false);
  const [postText, setPostText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPosting, setIsPosting] = useState(false);

  const generatePostMutation = useMutation({
    mutationFn: () => apiClient.generateXPost(positionId),
    onSuccess: (data) => {
      // Ensure post ends with "interested" (case-insensitive)
      let text = data.post_text.trim();
      if (!text.toLowerCase().endsWith('interested')) {
        if (!text.endsWith(' ')) {
          text += ' ';
        }
        text += "Comment 'interested' if you're interested";
      }
      setPostText(text);
      setIsGenerating(false);
      toast({
        title: 'Post generated',
        description: 'X post has been generated successfully.',
      });
    },
    onError: (error: Error) => {
      setIsGenerating(false);
      toast({
        title: 'Error',
        description: error.message || 'Failed to generate X post.',
        variant: 'destructive',
      });
    },
  });

  const postToXMutation = useMutation({
    mutationFn: (text: string) => apiClient.postToX(positionId, text),
    onSuccess: () => {
      setIsPosting(false);
      toast({
        title: 'Posted to X',
        description: 'The post has been published to X successfully.',
      });
      // Update distribution flags
      updateDistributionMutation.mutate({
        post_to_x: true,
        available_to_grok: availableToGrok,
      });
    },
    onError: (error: Error) => {
      setIsPosting(false);
      toast({
        title: 'Error',
        description: error.message || 'Failed to post to X.',
        variant: 'destructive',
      });
    },
  });

  const updateDistributionMutation = useMutation({
    mutationFn: (distribution: { post_to_x: boolean; available_to_grok: boolean }) =>
      apiClient.updatePositionDistribution(positionId, distribution),
    onSuccess: () => {
      toast({
        title: 'Settings saved',
        description: 'Distribution settings have been updated.',
      });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update distribution settings.',
        variant: 'destructive',
      });
    },
  });

  const handleGeneratePost = () => {
    setIsGenerating(true);
    generatePostMutation.mutate();
  };

  const handlePostToX = () => {
    // Validate that post ends with "interested" (case-insensitive)
    const trimmedText = postText.trim();
    if (!trimmedText.toLowerCase().endsWith('interested')) {
      toast({
        title: 'Invalid post',
        description: "Post must end with 'interested' (case-insensitive).",
        variant: 'destructive',
      });
      return;
    }

    setIsPosting(true);
    postToXMutation.mutate(trimmedText);
  };

  const handleSave = () => {
    updateDistributionMutation.mutate({
      post_to_x: false, // Only set to true if they actually posted
      available_to_grok: availableToGrok,
    });
  };

  // Validate post text on change
  const handlePostTextChange = (value: string) => {
    setPostText(value);
  };

  const postEndsWithInterested = postText.trim().toLowerCase().endsWith('interested');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Distribute Position</DialogTitle>
          <DialogDescription>
            Configure how this position should be distributed and create an X post.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Add to Grok Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="grok-toggle" className="text-base">
                Add to Grok
              </Label>
              <p className="text-sm text-muted-foreground">
                Make this position available to Grok for candidate matching
              </p>
            </div>
            <Switch
              id="grok-toggle"
              checked={availableToGrok}
              onCheckedChange={setAvailableToGrok}
            />
          </div>

          {/* X Post Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-base">X Post</Label>
                <p className="text-sm text-muted-foreground">
                  Generate and post this position to X (Twitter)
                </p>
              </div>
              <Button
                onClick={handleGeneratePost}
                disabled={isGenerating}
                variant="outline"
                size="sm"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Post
                  </>
                )}
              </Button>
            </div>

            {postText && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="post-text">Post Text (editable)</Label>
                  <Textarea
                    id="post-text"
                    value={postText}
                    onChange={(e) => handlePostTextChange(e.target.value)}
                    rows={6}
                    className="font-mono text-sm"
                    placeholder="Generated post will appear here..."
                  />
                  <p className="text-xs text-muted-foreground">
                    {postText.length} / 280 characters
                  </p>
                </div>

                {!postEndsWithInterested && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Post must end with &quot;interested&quot; (case-insensitive). Please add it
                      before posting.
                    </AlertDescription>
                  </Alert>
                )}

                <Button
                  onClick={handlePostToX}
                  disabled={isPosting || !postEndsWithInterested || postText.length > 280}
                  className="w-full"
                >
                  {isPosting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Posting to X...
                    </>
                  ) : (
                    <>
                      <XIcon className="mr-2 h-4 w-4" />
                      Post to X
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button onClick={handleSave} disabled={updateDistributionMutation.isPending}>
            {updateDistributionMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

