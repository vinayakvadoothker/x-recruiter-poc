'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, TeamCreateRequest } from '@/lib/api';
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { Send, Loader2, MessageSquare, FileText } from 'lucide-react';

interface CreateTeamDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SESSION_STORAGE_KEY = 'team_creation_data';
const FORM_STORAGE_KEY = 'team_creation_form';

export function CreateTeamDialog({ open, onOpenChange }: CreateTeamDialogProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'chat' | 'form'>('chat');
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatComplete, setChatComplete] = useState(false);
  const [chatTeamData, setChatTeamData] = useState<TeamCreateRequest | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<TeamCreateRequest>({
    name: '',
    department: '',
    needs: [],
    expertise: [],
    stack: [],
    domains: [],
    culture: '',
    work_style: '',
    hiring_priorities: [],
  });
  const [needsInput, setNeedsInput] = useState('');
  const [expertiseInput, setExpertiseInput] = useState('');
  const [stackInput, setStackInput] = useState('');
  const [domainsInput, setDomainsInput] = useState('');
  const [prioritiesInput, setPrioritiesInput] = useState('');
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load session from storage on mount/open
  useEffect(() => {
    if (open) {
      // Load chat data
      const savedChat = sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (savedChat) {
        try {
          const data = JSON.parse(savedChat);
          setMessages(data.messages || []);
          setSessionId(data.sessionId || null);
          setChatComplete(data.chatComplete || false);
          setChatTeamData(data.chatTeamData || null);
        } catch (e) {
          console.error('Failed to load chat session:', e);
        }
      }
      
      // Load form data
      const savedForm = sessionStorage.getItem(FORM_STORAGE_KEY);
      if (savedForm) {
        try {
          const data = JSON.parse(savedForm);
          setFormData(data.formData || {
            name: '',
            department: '',
            needs: [],
            expertise: [],
            stack: [],
            domains: [],
            culture: '',
            work_style: '',
            hiring_priorities: [],
          });
          setNeedsInput(data.needsInput || '');
          setExpertiseInput(data.expertiseInput || '');
          setStackInput(data.stackInput || '');
          setDomainsInput(data.domainsInput || '');
          setPrioritiesInput(data.prioritiesInput || '');
        } catch (e) {
          console.error('Failed to load form data:', e);
        }
      }
    }
  }, [open]);

  // Save chat session to storage
  useEffect(() => {
    if (open && (messages.length > 0 || chatTeamData)) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
        messages,
        sessionId,
        chatComplete,
        chatTeamData,
      }));
    }
  }, [messages, sessionId, chatComplete, chatTeamData, open]);

  // Save form data to storage
  useEffect(() => {
    if (open) {
      sessionStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({
        formData,
        needsInput,
        expertiseInput,
        stackInput,
        domainsInput,
        prioritiesInput,
      }));
    }
  }, [formData, needsInput, expertiseInput, stackInput, domainsInput, prioritiesInput, open]);

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
      
      // Build current_data object, only including fields that have values
      const currentData: any = {};
      if (formData.name) currentData.name = formData.name;
      if (formData.department) currentData.department = formData.department;
      if (formData.expertise && formData.expertise.length > 0) currentData.expertise = formData.expertise;
      if (formData.stack && formData.stack.length > 0) currentData.stack = formData.stack;
      if (formData.domains && formData.domains.length > 0) currentData.domains = formData.domains;
      if (formData.needs && formData.needs.length > 0) currentData.needs = formData.needs;
      if (formData.culture) currentData.culture = formData.culture;
      if (formData.work_style) currentData.work_style = formData.work_style;
      if (formData.hiring_priorities && formData.hiring_priorities.length > 0) currentData.hiring_priorities = formData.hiring_priorities;

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
      setChatComplete(data.is_complete || false);
      setIsStreaming(false);

      // Store team data and sync to form
      if (data.team_data) {
        setChatTeamData(data.team_data);
        // Sync chat data to form
        setFormData({
          name: data.team_data.name || '',
          department: data.team_data.department || '',
          needs: data.team_data.needs || [],
          expertise: data.team_data.expertise || [],
          stack: data.team_data.stack || [],
          domains: data.team_data.domains || [],
          culture: data.team_data.culture || '',
          work_style: data.team_data.work_style || '',
          hiring_priorities: data.team_data.hiring_priorities || [],
        });
        setNeedsInput((data.team_data.needs || []).join(', '));
        setExpertiseInput((data.team_data.expertise || []).join(', '));
        setStackInput((data.team_data.stack || []).join(', '));
        setDomainsInput((data.team_data.domains || []).join(', '));
        setPrioritiesInput((data.team_data.hiring_priorities || []).join(', '));
      }

      // Auto-switch to form tab when complete
      if (data.is_complete && data.team_data) {
        setTimeout(() => {
          setActiveTab('form');
        }, 500);
      }

      // Re-focus input after response (unless complete)
      if (!data.is_complete) {
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
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

  const createTeamMutation = useMutation({
    mutationFn: (data: TeamCreateRequest) => apiClient.createTeam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Team created',
        description: 'The team has been created successfully.',
      });
      // Clear all session storage
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
      sessionStorage.removeItem(FORM_STORAGE_KEY);
      // Reset state
      setMessages([]);
      setSessionId(null);
      setChatComplete(false);
      setChatTeamData(null);
      setFormData({
        name: '',
        department: '',
        needs: [],
        expertise: [],
        stack: [],
        domains: [],
        culture: '',
        work_style: '',
        hiring_priorities: [],
      });
      setNeedsInput('');
      setExpertiseInput('');
      setStackInput('');
      setDomainsInput('');
      setPrioritiesInput('');
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create team',
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
      if (!isStreaming && !chatComplete) {
        handleSendMessage();
      }
    }
  };

  const handleClearSession = () => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setMessages([]);
    setSessionId(null);
    setChatComplete(false);
    setChatTeamData(null);
    setStreamingMessage('');
    setIsStreaming(false);
  };

  const handleClearForm = () => {
    sessionStorage.removeItem(FORM_STORAGE_KEY);
    setFormData({
      name: '',
      department: '',
      needs: [],
      expertise: [],
      stack: [],
      domains: [],
      culture: '',
      work_style: '',
      hiring_priorities: [],
    });
    setNeedsInput('');
    setExpertiseInput('');
    setStackInput('');
    setDomainsInput('');
    setPrioritiesInput('');
  };

  const handleSubmit = async () => {
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

    // Form submission
    if (!formData.name.trim()) {
      toast({
        title: 'Missing Information',
        description: 'Team name is required.',
        variant: 'destructive',
      });
      return;
    }

    // Parse comma-separated lists
    const needs = needsInput.split(',').map(s => s.trim()).filter(Boolean);
    const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
    const stack = stackInput.split(',').map(s => s.trim()).filter(Boolean);
    const domains = domainsInput.split(',').map(s => s.trim()).filter(Boolean);
    const priorities = prioritiesInput.split(',').map(s => s.trim()).filter(Boolean);

    const teamData: TeamCreateRequest = {
      ...formData,
      needs: needs.length > 0 ? needs : undefined,
      expertise: expertise.length > 0 ? expertise : undefined,
      stack: stack.length > 0 ? stack : undefined,
      domains: domains.length > 0 ? domains : undefined,
      hiring_priorities: priorities.length > 0 ? priorities : undefined,
    };

    createTeamMutation.mutate(teamData);
  };

  const getPreviewData = (): TeamCreateRequest | null => {
    if (!formData.name.trim()) return null;
    const needs = needsInput.split(',').map(s => s.trim()).filter(Boolean);
    const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
    const stack = stackInput.split(',').map(s => s.trim()).filter(Boolean);
    const domains = domainsInput.split(',').map(s => s.trim()).filter(Boolean);
    const priorities = prioritiesInput.split(',').map(s => s.trim()).filter(Boolean);
    
    return {
      ...formData,
      needs: needs.length > 0 ? needs : undefined,
      expertise: expertise.length > 0 ? expertise : undefined,
      stack: stack.length > 0 ? stack : undefined,
      domains: domains.length > 0 ? domains : undefined,
      hiring_priorities: priorities.length > 0 ? priorities : undefined,
    };
  };

  const previewData = getPreviewData();
  const canSubmit = formData.name.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Create New Team</DialogTitle>
          <DialogDescription>
            Use chat or form to create your team. Your progress is saved automatically.
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

            {chatComplete && chatTeamData && (
              <div className="px-6 py-2 bg-green-500/10 border-t">
                <p className="text-sm text-green-600 dark:text-green-400">
                  ✓ All information collected! Switching to form tab to review and create...
                </p>
              </div>
            )}

            <div className="px-6 pb-4 pt-4 border-t">
              <div className="flex gap-2">
                <Input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={messages.length === 0 ? "Start by typing the team name..." : "Type your answer or update information..."}
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
            <div className="flex-1 overflow-y-auto px-6 py-4">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Team Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    placeholder="e.g., LLM Inference Team"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department">Department</Label>
                  <Input
                    id="department"
                    value={formData.department || ''}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    placeholder="e.g., Engineering"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expertise">Expertise (comma-separated)</Label>
                  <Input
                    id="expertise"
                    value={expertiseInput}
                    onChange={(e) => setExpertiseInput(e.target.value)}
                    placeholder="e.g., Backend Development, Distributed Systems"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="stack">Tech Stack (comma-separated)</Label>
                  <Input
                    id="stack"
                    value={stackInput}
                    onChange={(e) => setStackInput(e.target.value)}
                    placeholder="e.g., Python, FastAPI, PostgreSQL"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="domains">Domains (comma-separated)</Label>
                  <Input
                    id="domains"
                    value={domainsInput}
                    onChange={(e) => setDomainsInput(e.target.value)}
                    placeholder="e.g., LLM Inference, GPU Computing"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="needs">Needs / Skills Gaps (comma-separated)</Label>
                  <Input
                    id="needs"
                    value={needsInput}
                    onChange={(e) => setNeedsInput(e.target.value)}
                    placeholder="e.g., CUDA, Model Optimization"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="culture">Culture</Label>
                  <Textarea
                    id="culture"
                    value={formData.culture || ''}
                    onChange={(e) => setFormData({ ...formData, culture: e.target.value })}
                    placeholder="Describe the team culture..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="work_style">Work Style</Label>
                  <Textarea
                    id="work_style"
                    value={formData.work_style || ''}
                    onChange={(e) => setFormData({ ...formData, work_style: e.target.value })}
                    placeholder="Describe the team's work style..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priorities">Hiring Priorities (comma-separated)</Label>
                  <Input
                    id="priorities"
                    value={prioritiesInput}
                    onChange={(e) => setPrioritiesInput(e.target.value)}
                    placeholder="e.g., Senior Engineers, Research Experience"
                  />
                </div>
              </div>
            </div>

            <div className="px-6 pb-4 pt-4 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearForm}
                className="text-xs"
              >
                Clear Form
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        {activeTab === 'form' && (
          <DialogFooter className="px-6 pb-6 pt-4 border-t flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit || createTeamMutation.isPending}
            >
              {createTeamMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Team'
              )}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
