'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { apiClient, InterviewerCreateRequest, Team } from '@/lib/api';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Send, Loader2, MessageSquare, FileText } from 'lucide-react';

interface CreateInterviewerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SESSION_STORAGE_KEY = 'interviewer_creation_data';
const FORM_STORAGE_KEY = 'interviewer_creation_form';

export function CreateInterviewerDialog({ open, onOpenChange }: CreateInterviewerDialogProps) {
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
  const [chatInterviewerData, setChatInterviewerData] = useState<InterviewerCreateRequest | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<InterviewerCreateRequest>({
    name: '',
    phone_number: '',
    email: '',
    team_id: '',
    expertise: [],
    expertise_level: '',
    specializations: [],
    interview_style: '',
    evaluation_focus: [],
    question_style: '',
    preferred_interview_types: [],
  });
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
          setChatInterviewerData(data.chatInterviewerData || null);
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
            phone_number: '',
            email: '',
            team_id: '',
            expertise: [],
            expertise_level: '',
            specializations: [],
            interview_style: '',
            evaluation_focus: [],
            question_style: '',
            preferred_interview_types: [],
          });
          setExpertiseInput(data.expertiseInput || '');
          setSpecializationsInput(data.specializationsInput || '');
          setEvaluationFocusInput(data.evaluationFocusInput || '');
          setPreferredTypesInput(data.preferredTypesInput || '');
        } catch (e) {
          console.error('Failed to load form data:', e);
        }
      }
    }
  }, [open]);

  // Save chat session to storage
  useEffect(() => {
    if (open && (messages.length > 0 || chatInterviewerData)) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
        messages,
        sessionId,
        chatComplete,
        chatInterviewerData,
      }));
    }
  }, [messages, sessionId, chatComplete, chatInterviewerData, open]);

  // Save form data to storage
  useEffect(() => {
    if (open) {
      sessionStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({
        formData,
        expertiseInput,
        specializationsInput,
        evaluationFocusInput,
        preferredTypesInput,
      }));
    }
  }, [formData, expertiseInput, specializationsInput, evaluationFocusInput, preferredTypesInput, open]);

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
      if (formData.phone_number) currentData.phone_number = formData.phone_number;
      if (formData.email) currentData.email = formData.email;
      if (formData.team_id) currentData.team_id = formData.team_id;
      if (formData.expertise && formData.expertise.length > 0) currentData.expertise = formData.expertise;
      if (formData.expertise_level) currentData.expertise_level = formData.expertise_level;
      if (formData.specializations && formData.specializations.length > 0) currentData.specializations = formData.specializations;
      if (formData.interview_style) currentData.interview_style = formData.interview_style;
      if (formData.evaluation_focus && formData.evaluation_focus.length > 0) currentData.evaluation_focus = formData.evaluation_focus;
      if (formData.question_style) currentData.question_style = formData.question_style;
      if (formData.preferred_interview_types && formData.preferred_interview_types.length > 0) currentData.preferred_interview_types = formData.preferred_interview_types;

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
                console.log('Received parsed.final:', parsed.final);
                // Only update if this final message has actual data (not null/empty)
                if (parsed.final.interviewer_data || parsed.final.is_complete) {
                  finalData = parsed.final;
                  console.log('Set finalData to:', finalData);
                } else {
                  console.log('Ignoring final message with null/empty data:', parsed.final);
                }
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }

      const result = finalData || { message: fullMessage, session_id: sessionId, is_complete: false };
      console.log('Returning data from mutation:', result);
      return result;
    },
    onSuccess: (data) => {
      console.log('onSuccess called with data:', data);
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

      // Store interviewer data and sync to form
      console.log('Checking interviewer_data:', { has_interviewer_data: !!data.interviewer_data, interviewer_data: data.interviewer_data });
      if (data.interviewer_data) {
        setChatInterviewerData(data.interviewer_data);
        // Sync chat data to form
        setFormData({
          name: data.interviewer_data.name || '',
          phone_number: data.interviewer_data.phone_number || '',
          email: data.interviewer_data.email || '',
          team_id: data.interviewer_data.team_id && data.interviewer_data.team_id.trim() ? data.interviewer_data.team_id : '',
          expertise: data.interviewer_data.expertise || [],
          expertise_level: data.interviewer_data.expertise_level || '',
          specializations: data.interviewer_data.specializations || [],
          interview_style: data.interviewer_data.interview_style || '',
          evaluation_focus: data.interviewer_data.evaluation_focus || [],
          question_style: data.interviewer_data.question_style || '',
          preferred_interview_types: data.interviewer_data.preferred_interview_types || [],
        });
        setExpertiseInput((data.interviewer_data.expertise || []).join(', '));
        setSpecializationsInput((data.interviewer_data.specializations || []).join(', '));
        setEvaluationFocusInput((data.interviewer_data.evaluation_focus || []).join(', '));
        setPreferredTypesInput((data.interviewer_data.preferred_interview_types || []).join(', '));
      }

      // Auto-switch to form tab when complete (same as team creation)
      if (data.is_complete && data.interviewer_data) {
        console.log('Chat complete, switching to form tab', { is_complete: data.is_complete, has_interviewer_data: !!data.interviewer_data });
        setTimeout(() => {
          setActiveTab('form');
        }, 500);
      } else {
        console.log('Not switching to form', { is_complete: data.is_complete, has_interviewer_data: !!data.interviewer_data, data });
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

  const createInterviewerMutation = useMutation({
    mutationFn: (data: InterviewerCreateRequest) => apiClient.createInterviewer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interviewers'] });
      toast({
        title: 'Interviewer created',
        description: 'The interviewer has been created successfully.',
      });
      // Clear all session storage
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
      sessionStorage.removeItem(FORM_STORAGE_KEY);
      // Reset state
      setMessages([]);
      setSessionId(null);
      setChatComplete(false);
      setChatInterviewerData(null);
      setFormData({
        name: '',
        phone_number: '',
        email: '',
        team_id: '',
        expertise: [],
        expertise_level: '',
        specializations: [],
        interview_style: '',
        evaluation_focus: [],
        question_style: '',
        preferred_interview_types: [],
      });
      setExpertiseInput('');
      setSpecializationsInput('');
      setEvaluationFocusInput('');
      setPreferredTypesInput('');
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create interviewer',
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
      setChatInterviewerData(null);
    setStreamingMessage('');
    setIsStreaming(false);
  };

  const handleClearForm = () => {
    sessionStorage.removeItem(FORM_STORAGE_KEY);
    setFormData({
      name: '',
      phone_number: '',
      email: '',
      team_id: '',
      expertise: [],
      expertise_level: '',
      specializations: [],
      interview_style: '',
      evaluation_focus: [],
      question_style: '',
      preferred_interview_types: [],
    });
    setExpertiseInput('');
    setSpecializationsInput('');
    setEvaluationFocusInput('');
    setPreferredTypesInput('');
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
        description: 'Interviewer name is required.',
        variant: 'destructive',
      });
      return;
    }
    if (!formData.phone_number.trim()) {
      toast({
        title: 'Missing Information',
        description: 'Phone number is required.',
        variant: 'destructive',
      });
      return;
    }
    if (!formData.email.trim()) {
      toast({
        title: 'Missing Information',
        description: 'Email is required.',
        variant: 'destructive',
      });
      return;
    }

    // Parse comma-separated lists
    const expertise = expertiseInput.split(',').map(s => s.trim()).filter(Boolean);
    const specializations = specializationsInput.split(',').map(s => s.trim()).filter(Boolean);
    const evaluationFocus = evaluationFocusInput.split(',').map(s => s.trim()).filter(Boolean);
    const preferredTypes = preferredTypesInput.split(',').map(s => s.trim()).filter(Boolean);

    const interviewerData: InterviewerCreateRequest = {
      ...formData,
      team_id: formData.team_id || undefined,
      expertise: expertise.length > 0 ? expertise : undefined,
      specializations: specializations.length > 0 ? specializations : undefined,
      evaluation_focus: evaluationFocus.length > 0 ? evaluationFocus : undefined,
      preferred_interview_types: preferredTypes.length > 0 ? preferredTypes : undefined,
    };

    createInterviewerMutation.mutate(interviewerData);
  };

  const canSubmit = formData.name.trim().length > 0 && formData.phone_number.trim().length > 0 && formData.email.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Create New Interviewer</DialogTitle>
          <DialogDescription>
            Use chat or form to create an interviewer. Your progress is saved automatically.
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

            {chatComplete && chatInterviewerData && (
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
                  placeholder={messages.length === 0 ? "Start by typing the interviewer name..." : "Type your answer or update information..."}
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
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    placeholder="e.g., John Doe"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone_number">Phone Number *</Label>
                  <Input
                    id="phone_number"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                    required
                    placeholder="e.g., +1-555-123-4567"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    placeholder="e.g., john@example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="team_id">Team (optional)</Label>
                  <Select
                    value={formData.team_id || 'none'}
                    onValueChange={(value) => setFormData({ ...formData, team_id: value === 'none' ? undefined : value })}
                  >
                    <SelectTrigger id="team_id">
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
                  <Label htmlFor="expertise">Expertise (comma-separated)</Label>
                  <Input
                    id="expertise"
                    value={expertiseInput}
                    onChange={(e) => setExpertiseInput(e.target.value)}
                    placeholder="e.g., Python, Machine Learning, Distributed Systems"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expertise_level">Expertise Level</Label>
                  <Input
                    id="expertise_level"
                    value={formData.expertise_level || ''}
                    onChange={(e) => setFormData({ ...formData, expertise_level: e.target.value })}
                    placeholder="e.g., Senior, Expert, Staff"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="specializations">Specializations (comma-separated)</Label>
                  <Input
                    id="specializations"
                    value={specializationsInput}
                    onChange={(e) => setSpecializationsInput(e.target.value)}
                    placeholder="e.g., LLM Inference, GPU Computing"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="interview_style">Interview Style</Label>
                  <Textarea
                    id="interview_style"
                    value={formData.interview_style || ''}
                    onChange={(e) => setFormData({ ...formData, interview_style: e.target.value })}
                    placeholder="e.g., Technical deep-dive, Behavioral focus"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="evaluation_focus">Evaluation Focus (comma-separated)</Label>
                  <Input
                    id="evaluation_focus"
                    value={evaluationFocusInput}
                    onChange={(e) => setEvaluationFocusInput(e.target.value)}
                    placeholder="e.g., Problem-solving, System design, Code quality"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="question_style">Question Style</Label>
                  <Input
                    id="question_style"
                    value={formData.question_style || ''}
                    onChange={(e) => setFormData({ ...formData, question_style: e.target.value })}
                    placeholder="e.g., Open-ended, Structured, Case-based"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="preferred_interview_types">Preferred Interview Types (comma-separated)</Label>
                  <Input
                    id="preferred_interview_types"
                    value={preferredTypesInput}
                    onChange={(e) => setPreferredTypesInput(e.target.value)}
                    placeholder="e.g., Technical, System Design, Behavioral"
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
              disabled={!canSubmit || createInterviewerMutation.isPending}
            >
              {createInterviewerMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Interviewer'
              )}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
