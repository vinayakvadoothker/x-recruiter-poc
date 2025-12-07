'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Team, TeamUpdateRequest, TeamCreateRequest } from '@/lib/api';
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
import { useToast } from '@/hooks/use-toast';
import { Send, Loader2, MessageSquare, FileText } from 'lucide-react';

interface EditTeamDialogProps {
  team: Team;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SESSION_STORAGE_KEY_PREFIX = 'team_edit_chat_';

export function EditTeamDialog({ team, open, onOpenChange }: EditTeamDialogProps) {
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
  const [formData, setFormData] = useState<TeamUpdateRequest>({});
  const [needsInput, setNeedsInput] = useState('');
  const [expertiseInput, setExpertiseInput] = useState('');
  const [stackInput, setStackInput] = useState('');
  const [domainsInput, setDomainsInput] = useState('');
  const [prioritiesInput, setPrioritiesInput] = useState('');
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const sessionStorageKey = `${SESSION_STORAGE_KEY_PREFIX}${team.id}`;

  // Initialize form data when team changes
  useEffect(() => {
    if (team) {
      setFormData({
        name: team.name,
        department: team.department,
        culture: team.culture,
        work_style: team.work_style,
      });
      setNeedsInput(team.needs.join(', '));
      setExpertiseInput(team.expertise.join(', '));
      setStackInput(team.stack.join(', '));
      setDomainsInput(team.domains.join(', '));
      setPrioritiesInput(team.hiring_priorities.join(', '));
    }
  }, [team]);

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
  }, [open, team.id]);

  // Save chat session to storage
  useEffect(() => {
    if (open && messages.length > 0) {
      sessionStorage.setItem(sessionStorageKey, JSON.stringify({
        messages,
        sessionId,
      }));
    }
  }, [messages, sessionId, open, team.id]);

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
      const needs = needsInput.split(',').map(s => s.trim()).filter(Boolean);
      const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
      const stack = stackInput.split(',').map(s => s.trim()).filter(Boolean);
      const domains = domainsInput.split(',').map(s => s.trim()).filter(Boolean);
      const priorities = prioritiesInput.split(',').map(s => s.trim()).filter(Boolean);

      // Build current_data object, only including fields that have values
      const currentData: any = {};
      if (formData.name) currentData.name = formData.name;
      if (formData.department) currentData.department = formData.department;
      if (expertise.length > 0) currentData.expertise = expertise;
      if (stack.length > 0) currentData.stack = stack;
      if (domains.length > 0) currentData.domains = domains;
      if (needs.length > 0) currentData.needs = needs;
      if (formData.culture) currentData.culture = formData.culture;
      if (formData.work_style) currentData.work_style = formData.work_style;
      if (priorities.length > 0) currentData.hiring_priorities = priorities;
      
      const requestBody: any = {
        messages: chatMessages.map(m => ({ role: m.role, content: m.content })),
      };
      if (sessionId) requestBody.session_id = sessionId;
      if (Object.keys(currentData).length > 0) requestBody.current_data = currentData;
      
      // Use streaming endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/teams/chat/stream`, {
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
      if (data.team_data) {
        setFormData(prev => ({
          ...prev,
          name: data.team_data.name || prev.name,
          department: data.team_data.department !== undefined ? data.team_data.department : prev.department,
          culture: data.team_data.culture !== undefined ? data.team_data.culture : prev.culture,
          work_style: data.team_data.work_style !== undefined ? data.team_data.work_style : prev.work_style,
        }));
        if (data.team_data.needs) {
          setNeedsInput(data.team_data.needs.join(', '));
        }
        if (data.team_data.expertise) {
          setExpertiseInput(data.team_data.expertise.join(', '));
        }
        if (data.team_data.stack) {
          setStackInput(data.team_data.stack.join(', '));
        }
        if (data.team_data.domains) {
          setDomainsInput(data.team_data.domains.join(', '));
        }
        if (data.team_data.hiring_priorities) {
          setPrioritiesInput(data.team_data.hiring_priorities.join(', '));
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
    mutationFn: (data: TeamUpdateRequest) => apiClient.updateTeam(team.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Team updated',
        description: 'The team has been updated successfully.',
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
        description: error.message || 'Failed to update team',
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
    const needs = needsInput.split(',').map(s => s.trim()).filter(Boolean);
    const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
    const stack = stackInput.split(',').map(s => s.trim()).filter(Boolean);
    const domains = domainsInput.split(',').map(s => s.trim()).filter(Boolean);
    const priorities = prioritiesInput.split(',').map(s => s.trim()).filter(Boolean);

    updateMutation.mutate({
      ...formData,
      needs: needs.length > 0 ? needs : undefined,
      expertise: expertise.length > 0 ? expertise : undefined,
      stack: stack.length > 0 ? stack : undefined,
      domains: domains.length > 0 ? domains : undefined,
      hiring_priorities: priorities.length > 0 ? priorities : undefined,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Edit Team</DialogTitle>
          <DialogDescription>
            Use chat or form to update your team. Your progress is saved automatically.
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
                  placeholder={messages.length === 0 ? "Ask me to help update the team..." : "Type your answer or update information..."}
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
                    <Label htmlFor="edit-name">Team Name</Label>
                    <Input
                      id="edit-name"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., LLM Inference Team"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-department">Department</Label>
                    <Input
                      id="edit-department"
                      value={formData.department || ''}
                      onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                      placeholder="e.g., Engineering"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-expertise">Expertise (comma-separated)</Label>
                    <Input
                      id="edit-expertise"
                      value={expertiseInput}
                      onChange={(e) => setExpertiseInput(e.target.value)}
                      placeholder="e.g., Backend Development, Distributed Systems"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-stack">Tech Stack (comma-separated)</Label>
                    <Input
                      id="edit-stack"
                      value={stackInput}
                      onChange={(e) => setStackInput(e.target.value)}
                      placeholder="e.g., Python, FastAPI, PostgreSQL"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-domains">Domains (comma-separated)</Label>
                    <Input
                      id="edit-domains"
                      value={domainsInput}
                      onChange={(e) => setDomainsInput(e.target.value)}
                      placeholder="e.g., LLM Inference, GPU Computing"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-needs">Needs / Skills Gaps (comma-separated)</Label>
                    <Input
                      id="edit-needs"
                      value={needsInput}
                      onChange={(e) => setNeedsInput(e.target.value)}
                      placeholder="e.g., CUDA, Model Optimization"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-culture">Culture</Label>
                    <Textarea
                      id="edit-culture"
                      value={formData.culture || ''}
                      onChange={(e) => setFormData({ ...formData, culture: e.target.value })}
                      placeholder="Describe the team culture..."
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-work_style">Work Style</Label>
                    <Textarea
                      id="edit-work_style"
                      value={formData.work_style || ''}
                      placeholder="Describe the team's work style..."
                      rows={3}
                      onChange={(e) => setFormData({ ...formData, work_style: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-priorities">Hiring Priorities (comma-separated)</Label>
                    <Input
                      id="edit-priorities"
                      value={prioritiesInput}
                      onChange={(e) => setPrioritiesInput(e.target.value)}
                      placeholder="e.g., Senior Engineers, Research Experience"
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
                    {updateMutation.isPending ? 'Updating...' : 'Update Team'}
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
