'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { apiClient, Interviewer, InterviewerUpdateRequest, InterviewerCreateRequest, Team } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Send, Loader2, MessageSquare, FileText } from 'lucide-react';

interface EditInterviewerDialogProps {
  interviewer: Interviewer;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SESSION_STORAGE_KEY_PREFIX = 'interviewer_edit_chat_';

export function EditInterviewerDialog({ interviewer, open, onOpenChange }: EditInterviewerDialogProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'chat' | 'form'>('form');
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<InterviewerUpdateRequest>({});
  const [expertiseInput, setExpertiseInput] = useState('');
  const [specializationsInput, setSpecializationsInput] = useState('');
  const [evaluationFocusInput, setEvaluationFocusInput] = useState('');
  const [preferredTypesInput, setPreferredTypesInput] = useState('');
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: teamsData } = useQuery<Team[]>({
    queryKey: ['teams'],
    queryFn: () => apiClient.getTeams(),
    enabled: open, // Only fetch teams when dialog is open
  });

  const sessionStorageKey = `${SESSION_STORAGE_KEY_PREFIX}${interviewer.id}`;
  
  // Initialize form data when interviewer changes
  useEffect(() => {
    if (interviewer) {
      setFormData({
        name: interviewer.name,
        phone_number: interviewer.phone_number,
        email: interviewer.email,
        team_id: interviewer.team_id || '',
        expertise_level: interviewer.expertise_level,
        interview_style: interviewer.interview_style,
        question_style: interviewer.question_style,
      });
      setExpertiseInput(interviewer.expertise.join(', '));
      setSpecializationsInput(interviewer.specializations.join(', '));
      setEvaluationFocusInput(interviewer.evaluation_focus.join(', '));
      setPreferredTypesInput(interviewer.preferred_interview_types.join(', '));
    }
  }, [interviewer]);

  // Load chat session from storage
  useEffect(() => {
    if (open) {
      const saved = sessionStorage.getItem(sessionStorageKey);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          setMessages(data.messages || []);
          setSessionId(data.sessionId || null);
        } catch (e) {
          console.error('Failed to load chat session:', e);
        }
      }
    }
  }, [open, interviewer.id]);

  // Save chat session to storage
  useEffect(() => {
    if (open && messages.length > 0) {
      sessionStorage.setItem(sessionStorageKey, JSON.stringify({
        messages,
        sessionId,
      }));
    }
  }, [messages, sessionId, open, interviewer.id]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMessage]);

  // Auto-focus input when dialog opens or tab changes
  useEffect(() => {
    if (open && activeTab === 'chat') {
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [open, activeTab]);

  const chatMutation = useMutation({
    mutationFn: async (userMessage: string) => {
      const chatMessages = userMessage 
        ? [...messages, { role: 'user' as const, content: userMessage, timestamp: new Date() }]
        : messages;
      
      // Get current form data for context
      const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
      const specializations = specializationsInput.split(',').map(s => s.trim()).filter(Boolean);
      const evaluationFocus = evaluationFocusInput.split(',').map(s => s.trim()).filter(Boolean);
      const preferredTypes = preferredTypesInput.split(',').map(s => s.trim()).filter(Boolean);

      // Build current_data object, only including fields that have values
      const currentData: any = {};
      if (formData.name) currentData.name = formData.name;
      if (formData.phone_number) currentData.phone_number = formData.phone_number;
      if (formData.email) currentData.email = formData.email;
      if (formData.team_id) currentData.team_id = formData.team_id;
      if (expertise.length > 0) currentData.expertise = expertise;
      if (formData.expertise_level) currentData.expertise_level = formData.expertise_level;
      if (specializations.length > 0) currentData.specializations = specializations;
      if (formData.interview_style) currentData.interview_style = formData.interview_style;
      if (evaluationFocus.length > 0) currentData.evaluation_focus = evaluationFocus;
      if (formData.question_style) currentData.question_style = formData.question_style;
      if (preferredTypes.length > 0) currentData.preferred_interview_types = preferredTypes;
      
      const requestBody: any = {
        messages: chatMessages.map(m => ({ role: m.role, content: m.content })),
      };
      if (sessionId) requestBody.session_id = sessionId;
      if (Object.keys(currentData).length > 0) requestBody.current_data = currentData;
      
      // Use streaming endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/interviewers/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullMessage = '';
      let finalData: any = null;

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                fullMessage += parsed.content;
                setStreamingMessage(fullMessage);
              }
              if (parsed.final) {
                finalData = parsed.final;
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }

      return finalData || { message: fullMessage, session_id: sessionId, is_complete: false };
    },
    onSuccess: (data) => {
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.message || streamingMessage,
        timestamp: new Date(),
      };

      setMessages(prev => {
        const newMessages = [...prev];
        if (input.trim()) {
          newMessages.push({
            role: 'user',
            content: input.trim(),
            timestamp: new Date(),
          });
        }
        newMessages.push(assistantMessage);
        return newMessages;
      });

      setInput('');
      setStreamingMessage('');
      setSessionId(data.session_id);
      setIsStreaming(false);

      // Sync chat data to form if provided
      if (data.interviewer_data) {
        setFormData(prev => ({
          ...prev,
          name: data.interviewer_data.name || prev.name,
          phone_number: data.interviewer_data.phone_number || prev.phone_number,
          email: data.interviewer_data.email || prev.email,
          team_id: data.interviewer_data.team_id !== undefined ? data.interviewer_data.team_id : prev.team_id,
          expertise_level: data.interviewer_data.expertise_level !== undefined ? data.interviewer_data.expertise_level : prev.expertise_level,
          interview_style: data.interviewer_data.interview_style !== undefined ? data.interviewer_data.interview_style : prev.interview_style,
          question_style: data.interviewer_data.question_style !== undefined ? data.interviewer_data.question_style : prev.question_style,
        }));
        if (data.interviewer_data.expertise) {
          setExpertiseInput(data.interviewer_data.expertise.join(', '));
        }
        if (data.interviewer_data.specializations) {
          setSpecializationsInput(data.interviewer_data.specializations.join(', '));
        }
        if (data.interviewer_data.evaluation_focus) {
          setEvaluationFocusInput(data.interviewer_data.evaluation_focus.join(', '));
        }
        if (data.interviewer_data.preferred_interview_types) {
          setPreferredTypesInput(data.interviewer_data.preferred_interview_types.join(', '));
        }
      }

      // Re-focus input after response
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to get response from AI',
        variant: 'destructive',
      });
      setIsStreaming(false);
      setStreamingMessage('');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: InterviewerUpdateRequest) => apiClient.updateInterviewer(interviewer.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviewers'] });
      toast({
        title: 'Interviewer updated',
        description: 'The interviewer has been updated successfully.',
      });
      // Clear chat session
      sessionStorage.removeItem(sessionStorageKey);
      setMessages([]);
      setSessionId(null);
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update interviewer',
        variant: 'destructive',
      });
    },
  });

  const handleSendMessage = async (message?: string) => {
    const messageToSend = message || input.trim();
    
    if (!messageToSend) return;

    setIsStreaming(true);
    setStreamingMessage('');
    chatMutation.mutate(messageToSend);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming) {
        handleSendMessage();
      }
    }
  };

  const handleClearSession = () => {
    sessionStorage.removeItem(sessionStorageKey);
    setMessages([]);
    setSessionId(null);
    setStreamingMessage('');
    setIsStreaming(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only allow submission from form tab
    if (activeTab !== 'form') {
      toast({
        title: 'Switch to Form',
        description: 'Please review and submit from the Form tab.',
        variant: 'destructive',
      });
      setActiveTab('form');
      return;
    }
    
    // Parse comma-separated lists
    const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
    const specializations = specializationsInput.split(',').map(s => s.trim()).filter(Boolean);
    const evaluationFocus = evaluationFocusInput.split(',').map(s => s.trim()).filter(Boolean);
    const preferredTypes = preferredTypesInput.split(',').map(s => s.trim()).filter(Boolean);

    updateMutation.mutate({
      ...formData,
      team_id: formData.team_id || null,
      expertise: expertise.length > 0 ? expertise : undefined,
      specializations: specializations.length > 0 ? specializations : undefined,
      evaluation_focus: evaluationFocus.length > 0 ? evaluationFocus : undefined,
      preferred_interview_types: preferredTypes.length > 0 ? preferredTypes : undefined,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Edit Interviewer: {interviewer.name}</DialogTitle>
          <DialogDescription>
            Chat with AI or use the form to update interviewer information.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'chat' | 'form')} className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="px-6 border-b">
            <TabsList>
              <TabsTrigger value="chat">
                <MessageSquare className="mr-2 h-4 w-4" />
                Chat
              </TabsTrigger>
              <TabsTrigger value="form">
                <FileText className="mr-2 h-4 w-4" />
                Form
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="chat" className="flex-1 flex flex-col min-h-0 m-0 overflow-hidden">
            <div className="flex-1 overflow-y-auto px-6 py-4" ref={scrollAreaRef}>
              <div className="space-y-4">
                {messages.map((message, idx) => (
                  <div
                    key={idx}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))}
                {isStreaming && streamingMessage && (
                  <div className="flex justify-start">
                    <div className="bg-muted text-muted-foreground rounded-lg px-4 py-2 max-w-[80%]">
                      <p className="text-sm whitespace-pre-wrap">{streamingMessage}</p>
                    </div>
                  </div>
                )}
                {isStreaming && !streamingMessage && (
                  <div className="flex justify-start">
                    <div className="bg-muted text-muted-foreground rounded-lg px-4 py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <div className="px-6 pb-4 pt-4 border-t">
              <div className="flex gap-2">
                <Input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={messages.length === 0 ? "Ask me to help update the interviewer..." : "Type your answer or update information..."}
                  disabled={isStreaming}
                  className="flex-1"
                />
                <Button
                  onClick={() => handleSendMessage()}
                  disabled={isStreaming || !input.trim()}
                >
                  {isStreaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearSession}
                  className="mt-2 text-xs"
                >
                  Start Over
                </Button>
              )}
            </div>
          </TabsContent>

          <TabsContent value="form" className="flex-1 flex flex-col min-h-0 m-0 overflow-hidden">
            <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0 overflow-hidden">
              <div className="flex-1 overflow-y-auto px-6 py-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-name">Name *</Label>
                    <Input
                      id="edit-name"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., John Doe"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-phone_number">Phone Number *</Label>
                    <Input
                      id="edit-phone_number"
                      value={formData.phone_number || ''}
                      onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                      placeholder="e.g., +1-555-123-4567"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-email">Email *</Label>
                    <Input
                      id="edit-email"
                      type="email"
                      value={formData.email || ''}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="e.g., john@example.com"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-team_id">Team (optional)</Label>
                    <Select
                      value={formData.team_id !== undefined ? (formData.team_id || 'none') : (interviewer.team_id || 'none')}
                      onValueChange={(value) => setFormData({ ...formData, team_id: value === 'none' ? undefined : value })}
                    >
                      <SelectTrigger id="edit-team_id">
                        <SelectValue placeholder="Select a team (optional)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Team</SelectItem>
                        {teamsData?.map((team) => (
                          <SelectItem key={team.id} value={team.id}>
                            {team.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-expertise">Expertise (comma-separated)</Label>
                    <Input
                      id="edit-expertise"
                      value={expertiseInput}
                      onChange={(e) => setExpertiseInput(e.target.value)}
                      placeholder="e.g., Python, Machine Learning, Distributed Systems"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-expertise_level">Expertise Level</Label>
                    <Input
                      id="edit-expertise_level"
                      value={formData.expertise_level || ''}
                      onChange={(e) => setFormData({ ...formData, expertise_level: e.target.value })}
                      placeholder="e.g., Senior, Expert, Staff"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-specializations">Specializations (comma-separated)</Label>
                    <Input
                      id="edit-specializations"
                      value={specializationsInput}
                      onChange={(e) => setSpecializationsInput(e.target.value)}
                      placeholder="e.g., LLM Inference, GPU Computing"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-interview_style">Interview Style</Label>
                    <Textarea
                      id="edit-interview_style"
                      value={formData.interview_style || ''}
                      onChange={(e) => setFormData({ ...formData, interview_style: e.target.value })}
                      placeholder="e.g., Technical deep-dive, Behavioral focus"
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-evaluation_focus">Evaluation Focus (comma-separated)</Label>
                    <Input
                      id="edit-evaluation_focus"
                      value={evaluationFocusInput}
                      onChange={(e) => setEvaluationFocusInput(e.target.value)}
                      placeholder="e.g., Problem-solving, System design, Code quality"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-question_style">Question Style</Label>
                    <Input
                      id="edit-question_style"
                      value={formData.question_style || ''}
                      onChange={(e) => setFormData({ ...formData, question_style: e.target.value })}
                      placeholder="e.g., Open-ended, Structured, Case-based"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-preferred_interview_types">Preferred Interview Types (comma-separated)</Label>
                    <Input
                      id="edit-preferred_interview_types"
                      value={preferredTypesInput}
                      onChange={(e) => setPreferredTypesInput(e.target.value)}
                      placeholder="e.g., Technical, System Design, Behavioral"
                    />
                  </div>
                </div>
              </div>
              {activeTab === 'form' && (
                <DialogFooter className="px-6 pb-6 pt-4 border-t flex-shrink-0">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => onOpenChange(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? 'Updating...' : 'Update Interviewer'}
                  </Button>
                </DialogFooter>
              )}
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
