'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { apiClient, Position, PositionUpdateRequest, Team } from '@/lib/api';
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

interface EditPositionDialogProps {
  position: Position;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SESSION_STORAGE_KEY_PREFIX = 'position_edit_chat_';

export function EditPositionDialog({ position, open, onOpenChange }: EditPositionDialogProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'chat' | 'form'>('form');
  
  // Fetch teams for dropdown
  const { data: teamsData } = useQuery<Team[]>({
    queryKey: ['teams'],
    queryFn: () => apiClient.getTeams(),
    enabled: open,
  });
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<PositionUpdateRequest>({});
  const [requirementsInput, setRequirementsInput] = useState('');
  const [mustHavesInput, setMustHavesInput] = useState('');
  const [niceToHavesInput, setNiceToHavesInput] = useState('');
  const [responsibilitiesInput, setResponsibilitiesInput] = useState('');
  const [techStackInput, setTechStackInput] = useState('');
  const [domainsInput, setDomainsInput] = useState('');
  const [collaborationInput, setCollaborationInput] = useState('');
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const sessionStorageKey = `${SESSION_STORAGE_KEY_PREFIX}${position.id}`;

  // Initialize form data when position changes
  useEffect(() => {
    if (position && open) {
      setFormData({
        title: position.title,
        team_id: position.team_id || undefined,
        description: position.description,
        experience_level: position.experience_level,
        team_context: position.team_context,
        reporting_to: position.reporting_to,
        priority: position.priority,
        status: position.status,
      });
      setRequirementsInput((position.requirements || []).join(', '));
      setMustHavesInput((position.must_haves || []).join(', '));
      setNiceToHavesInput((position.nice_to_haves || []).join(', '));
      setResponsibilitiesInput((position.responsibilities || []).join(', '));
      setTechStackInput((position.tech_stack || []).join(', '));
      setDomainsInput((position.domains || []).join(', '));
      setCollaborationInput((position.collaboration || []).join(', '));
    }
  }, [position, open]);

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
  }, [open, position.id]);

  // Save chat session to storage
  useEffect(() => {
    if (open && messages.length > 0) {
      sessionStorage.setItem(sessionStorageKey, JSON.stringify({
        messages,
        sessionId,
      }));
    }
  }, [messages, sessionId, open, position.id]);

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
      const requirements = requirementsInput.split(',').map(s => s.trim()).filter(Boolean);
      const mustHaves = mustHavesInput.split(',').map(s => s.trim()).filter(Boolean);
      const niceToHaves = niceToHavesInput.split(',').map(s => s.trim()).filter(Boolean);
      const responsibilities = responsibilitiesInput.split(',').map(s => s.trim()).filter(Boolean);
      const techStack = techStackInput.split(',').map(s => s.trim()).filter(Boolean);
      const domains = domainsInput.split(',').map(s => s.trim()).filter(Boolean);
      const collaboration = collaborationInput.split(',').map(s => s.trim()).filter(Boolean);

      // Build current_data object, only including fields that have values
      const currentData: any = {};
      if (formData.title) currentData.title = formData.title;
      if (formData.team_id) currentData.team_id = formData.team_id;
      if (formData.description) currentData.description = formData.description;
      if (requirements.length > 0) currentData.requirements = requirements;
      if (mustHaves.length > 0) currentData.must_haves = mustHaves;
      if (niceToHaves.length > 0) currentData.nice_to_haves = niceToHaves;
      if (formData.experience_level) currentData.experience_level = formData.experience_level;
      if (responsibilities.length > 0) currentData.responsibilities = responsibilities;
      if (techStack.length > 0) currentData.tech_stack = techStack;
      if (domains.length > 0) currentData.domains = domains;
      if (formData.team_context) currentData.team_context = formData.team_context;
      if (formData.reporting_to) currentData.reporting_to = formData.reporting_to;
      if (collaboration.length > 0) currentData.collaboration = collaboration;
      if (formData.priority) currentData.priority = formData.priority;
      if (formData.status) currentData.status = formData.status;
      
      const requestBody: any = {
        messages: chatMessages.map(m => ({ role: m.role, content: m.content })),
      };
      if (sessionId) requestBody.session_id = sessionId;
      if (Object.keys(currentData).length > 0) requestBody.current_data = currentData;
      
      // Use streaming endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/positions/chat/stream`, {
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
      if (data.position_data) {
        setFormData(prev => ({
          ...prev,
          title: data.position_data.title !== undefined ? data.position_data.title : prev.title,
          team_id: data.position_data.team_id !== undefined ? data.position_data.team_id : prev.team_id,
          description: data.position_data.description !== undefined ? data.position_data.description : prev.description,
          experience_level: data.position_data.experience_level !== undefined ? data.position_data.experience_level : prev.experience_level,
          team_context: data.position_data.team_context !== undefined ? data.position_data.team_context : prev.team_context,
          reporting_to: data.position_data.reporting_to !== undefined ? data.position_data.reporting_to : prev.reporting_to,
          priority: data.position_data.priority !== undefined ? data.position_data.priority : prev.priority,
          status: data.position_data.status !== undefined ? data.position_data.status : prev.status,
        }));
        if (data.position_data.requirements) {
          setRequirementsInput(data.position_data.requirements.join(', '));
        }
        if (data.position_data.must_haves) {
          setMustHavesInput(data.position_data.must_haves.join(', '));
        }
        if (data.position_data.nice_to_haves) {
          setNiceToHavesInput(data.position_data.nice_to_haves.join(', '));
        }
        if (data.position_data.responsibilities) {
          setResponsibilitiesInput(data.position_data.responsibilities.join(', '));
        }
        if (data.position_data.tech_stack) {
          setTechStackInput(data.position_data.tech_stack.join(', '));
        }
        if (data.position_data.domains) {
          setDomainsInput(data.position_data.domains.join(', '));
        }
        if (data.position_data.collaboration) {
          setCollaborationInput(data.position_data.collaboration.join(', '));
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
    mutationFn: (data: PositionUpdateRequest) => apiClient.updatePosition(position.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      toast({
        title: 'Position updated',
        description: 'The position has been updated successfully.',
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
        description: error.message || 'Failed to update position',
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
    const requirements = requirementsInput.split(',').map(s => s.trim()).filter(Boolean);
    const mustHaves = mustHavesInput.split(',').map(s => s.trim()).filter(Boolean);
    const niceToHaves = niceToHavesInput.split(',').map(s => s.trim()).filter(Boolean);
    const responsibilities = responsibilitiesInput.split(',').map(s => s.trim()).filter(Boolean);
    const techStack = techStackInput.split(',').map(s => s.trim()).filter(Boolean);
    const domains = domainsInput.split(',').map(s => s.trim()).filter(Boolean);
    const collaboration = collaborationInput.split(',').map(s => s.trim()).filter(Boolean);

    updateMutation.mutate({
      ...formData,
      requirements: requirements.length > 0 ? requirements : undefined,
      must_haves: mustHaves.length > 0 ? mustHaves : undefined,
      nice_to_haves: niceToHaves.length > 0 ? niceToHaves : undefined,
      responsibilities: responsibilities.length > 0 ? responsibilities : undefined,
      tech_stack: techStack.length > 0 ? techStack : undefined,
      domains: domains.length > 0 ? domains : undefined,
      collaboration: collaboration.length > 0 ? collaboration : undefined,
      team_id: formData.team_id || undefined,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Edit Position: {position.title}</DialogTitle>
          <DialogDescription>
            Use chat or form to update position information. Your progress is saved automatically.
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
                  placeholder={messages.length === 0 ? "Ask me to help update the position..." : "Type your answer or update information..."}
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
                    <Label htmlFor="edit-title">Position Title *</Label>
                    <Input
                      id="edit-title"
                      value={formData.title || position.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      required
                      placeholder="e.g., Senior LLM Inference Engineer"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-team_id">Team (optional)</Label>
                    <Select
                      value={formData.team_id !== undefined ? (formData.team_id || 'none') : (position.team_id || 'none')}
                      onValueChange={(value) => setFormData({ ...formData, team_id: value === 'none' ? undefined : value })}
                    >
                      <SelectTrigger id="edit-team_id">
                        <SelectValue placeholder="Select a team (optional)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No team</SelectItem>
                        {teamsData?.map((team) => (
                          <SelectItem key={team.id} value={team.id}>
                            {team.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-description">Description</Label>
                    <Textarea
                      id="edit-description"
                      value={formData.description !== undefined ? (formData.description || '') : (position.description || '')}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Full job description..."
                      rows={4}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-must_haves">Must-Have Skills (comma-separated)</Label>
                    <Input
                      id="edit-must_haves"
                      value={mustHavesInput}
                      onChange={(e) => setMustHavesInput(e.target.value)}
                      placeholder="e.g., CUDA, C++, PyTorch"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-nice_to_haves">Nice-to-Have Skills (comma-separated)</Label>
                    <Input
                      id="edit-nice_to_haves"
                      value={niceToHavesInput}
                      onChange={(e) => setNiceToHavesInput(e.target.value)}
                      placeholder="e.g., TensorFlow, Distributed Systems"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-requirements">Requirements (comma-separated)</Label>
                    <Input
                      id="edit-requirements"
                      value={requirementsInput}
                      onChange={(e) => setRequirementsInput(e.target.value)}
                      placeholder="e.g., 5+ years CUDA, PhD in CS"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-experience_level">Experience Level</Label>
                    <Select
                      value={formData.experience_level !== undefined ? (formData.experience_level || 'none') : (position.experience_level || 'none')}
                      onValueChange={(value) => setFormData({ ...formData, experience_level: value === 'none' ? undefined : value })}
                    >
                      <SelectTrigger id="edit-experience_level">
                        <SelectValue placeholder="Select experience level" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Not specified</SelectItem>
                        <SelectItem value="Junior">Junior</SelectItem>
                        <SelectItem value="Mid">Mid</SelectItem>
                        <SelectItem value="Senior">Senior</SelectItem>
                        <SelectItem value="Staff">Staff</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-responsibilities">Responsibilities (comma-separated)</Label>
                    <Input
                      id="edit-responsibilities"
                      value={responsibilitiesInput}
                      onChange={(e) => setResponsibilitiesInput(e.target.value)}
                      placeholder="e.g., Optimize LLM inference, Build GPU systems"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-tech_stack">Tech Stack (comma-separated)</Label>
                    <Input
                      id="edit-tech_stack"
                      value={techStackInput}
                      onChange={(e) => setTechStackInput(e.target.value)}
                      placeholder="e.g., Python, CUDA, PyTorch"
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
                    <Label htmlFor="edit-team_context">Team Context</Label>
                    <Textarea
                      id="edit-team_context"
                      value={formData.team_context !== undefined ? (formData.team_context || '') : (position.team_context || '')}
                      onChange={(e) => setFormData({ ...formData, team_context: e.target.value })}
                      placeholder="How this role fits in the team..."
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-reporting_to">Reporting To</Label>
                    <Input
                      id="edit-reporting_to"
                      value={formData.reporting_to !== undefined ? (formData.reporting_to || '') : (position.reporting_to || '')}
                      onChange={(e) => setFormData({ ...formData, reporting_to: e.target.value })}
                      placeholder="e.g., Engineering Manager"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-collaboration">Collaboration (comma-separated)</Label>
                    <Input
                      id="edit-collaboration"
                      value={collaborationInput}
                      onChange={(e) => setCollaborationInput(e.target.value)}
                      placeholder="e.g., Research Team, Infrastructure Team"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-priority">Priority</Label>
                    <Select
                      value={formData.priority !== undefined ? (formData.priority || 'medium') : (position.priority || 'medium')}
                      onValueChange={(value) => setFormData({ ...formData, priority: value })}
                    >
                      <SelectTrigger id="edit-priority">
                        <SelectValue placeholder="Select priority" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-status">Status</Label>
                    <Select
                      value={formData.status !== undefined ? (formData.status || 'open') : (position.status || 'open')}
                      onValueChange={(value) => setFormData({ ...formData, status: value })}
                    >
                      <SelectTrigger id="edit-status">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">Open</SelectItem>
                        <SelectItem value="in-progress">In Progress</SelectItem>
                        <SelectItem value="on-hold">On Hold</SelectItem>
                        <SelectItem value="filled">Filled</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <DialogFooter className="px-6 pb-6 pt-4 border-t flex-shrink-0">
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                >
                  {updateMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    'Update Position'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
