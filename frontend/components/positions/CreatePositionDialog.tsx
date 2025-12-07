'use client';

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, PositionCreateRequest, Team } from '@/lib/api';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { Send, Loader2, MessageSquare, FileText, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { PositionDistributionDialog } from './PositionDistributionDialog';

interface CreatePositionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SESSION_STORAGE_KEY = 'position_creation_data';
const FORM_STORAGE_KEY = 'position_creation_form';

export function CreatePositionDialog({ open, onOpenChange }: CreatePositionDialogProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'chat' | 'form'>('chat');
  const [createdPositionId, setCreatedPositionId] = useState<string | null>(null);
  const [showDistributionDialog, setShowDistributionDialog] = useState(false);
  
  // Fetch teams for dropdown
  const { data: teamsData } = useQuery<Team[]>({
    queryKey: ['teams'],
    queryFn: () => apiClient.getTeams(),
    enabled: open, // Only fetch teams when dialog is open
  });
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatComplete, setChatComplete] = useState(false);
  const [chatPositionData, setChatPositionData] = useState<PositionCreateRequest | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<PositionCreateRequest>({
    title: '',
    team_id: '',
    description: '',
    requirements: [],
    must_haves: [],
    nice_to_haves: [],
    experience_level: '',
    responsibilities: [],
    tech_stack: [],
    domains: [],
    team_context: '',
    reporting_to: '',
    collaboration: [],
    priority: 'medium',
    status: 'open',
  });
  const [requirementsInput, setRequirementsInput] = useState('');
  const [mustHavesInput, setMustHavesInput] = useState('');
  const [niceToHavesInput, setNiceToHavesInput] = useState('');
  const [responsibilitiesInput, setResponsibilitiesInput] = useState('');
  const [techStackInput, setTechStackInput] = useState('');
  const [domainsInput, setDomainsInput] = useState('');
  const [collaborationInput, setCollaborationInput] = useState('');
  
  // Similarity check state
  const [similarPositions, setSimilarPositions] = useState<any[]>([]);
  const [checkingSimilarity, setCheckingSimilarity] = useState(false);
  const [similarityWarningShown, setSimilarityWarningShown] = useState(false);
  const [pendingPositionData, setPendingPositionData] = useState<PositionCreateRequest | null>(null);
  
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
          setChatPositionData(data.chatPositionData || null);
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
            title: '',
            team_id: '',
            description: '',
            requirements: [],
            must_haves: [],
            nice_to_haves: [],
            experience_level: '',
            responsibilities: [],
            tech_stack: [],
            domains: [],
            team_context: '',
            reporting_to: '',
            collaboration: [],
            priority: 'medium',
            status: 'open',
          });
          setRequirementsInput(data.requirementsInput || '');
          setMustHavesInput(data.mustHavesInput || '');
          setNiceToHavesInput(data.niceToHavesInput || '');
          setResponsibilitiesInput(data.responsibilitiesInput || '');
          setTechStackInput(data.techStackInput || '');
          setDomainsInput(data.domainsInput || '');
          setCollaborationInput(data.collaborationInput || '');
        } catch (e) {
          console.error('Failed to load form data:', e);
        }
      }
    }
  }, [open]);

  // Save chat session to storage
  useEffect(() => {
    if (open && (messages.length > 0 || chatPositionData)) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
        messages,
        sessionId,
        chatComplete,
        chatPositionData,
      }));
    }
  }, [messages, sessionId, chatComplete, chatPositionData, open]);

  // Save form data to storage
  useEffect(() => {
    if (open) {
      sessionStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({
        formData,
        requirementsInput,
        mustHavesInput,
        niceToHavesInput,
        responsibilitiesInput,
        techStackInput,
        domainsInput,
        collaborationInput,
      }));
    }
  }, [formData, requirementsInput, mustHavesInput, niceToHavesInput, responsibilitiesInput, techStackInput, domainsInput, collaborationInput, open]);

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
      if (formData.title) currentData.title = formData.title;
      if (formData.team_id) currentData.team_id = formData.team_id;
      if (formData.description) currentData.description = formData.description;
      if (formData.requirements && formData.requirements.length > 0) currentData.requirements = formData.requirements;
      if (formData.must_haves && formData.must_haves.length > 0) currentData.must_haves = formData.must_haves;
      if (formData.nice_to_haves && formData.nice_to_haves.length > 0) currentData.nice_to_haves = formData.nice_to_haves;
      if (formData.experience_level) currentData.experience_level = formData.experience_level;
      if (formData.responsibilities && formData.responsibilities.length > 0) currentData.responsibilities = formData.responsibilities;
      if (formData.tech_stack && formData.tech_stack.length > 0) currentData.tech_stack = formData.tech_stack;
      if (formData.domains && formData.domains.length > 0) currentData.domains = formData.domains;
      if (formData.team_context) currentData.team_context = formData.team_context;
      if (formData.reporting_to) currentData.reporting_to = formData.reporting_to;
      if (formData.collaboration && formData.collaboration.length > 0) currentData.collaboration = formData.collaboration;
      if (formData.priority) currentData.priority = formData.priority;

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
      setChatComplete(data.is_complete || false);
      setIsStreaming(false);

      // Store position data and sync to form
      if (data.position_data) {
        setChatPositionData(data.position_data);
        // Sync chat data to form
        setFormData({
          title: data.position_data.title || '',
          team_id: data.position_data.team_id || '',
          description: data.position_data.description || '',
          requirements: data.position_data.requirements || [],
          must_haves: data.position_data.must_haves || [],
          nice_to_haves: data.position_data.nice_to_haves || [],
          experience_level: data.position_data.experience_level || '',
          responsibilities: data.position_data.responsibilities || [],
          tech_stack: data.position_data.tech_stack || [],
          domains: data.position_data.domains || [],
          team_context: data.position_data.team_context || '',
          reporting_to: data.position_data.reporting_to || '',
          collaboration: data.position_data.collaboration || [],
          priority: data.position_data.priority || 'medium',
          status: data.position_data.status || 'open',
        });
        setRequirementsInput((data.position_data.requirements || []).join(', '));
        setMustHavesInput((data.position_data.must_haves || []).join(', '));
        setNiceToHavesInput((data.position_data.nice_to_haves || []).join(', '));
        setResponsibilitiesInput((data.position_data.responsibilities || []).join(', '));
        setTechStackInput((data.position_data.tech_stack || []).join(', '));
        setDomainsInput((data.position_data.domains || []).join(', '));
        setCollaborationInput((data.position_data.collaboration || []).join(', '));
      }

      // Auto-switch to form tab when complete
      if (data.is_complete && data.position_data) {
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

  const checkSimilarityMutation = useMutation({
    mutationFn: (data: PositionCreateRequest) => apiClient.checkPositionSimilarity(data),
    onSuccess: (response) => {
      setSimilarPositions(response.similar_positions);
      if (response.has_duplicates) {
        toast({
          title: 'Similar Positions Found',
          description: `Found ${response.similar_positions.length} similar position(s). Please review before creating.`,
          variant: 'default',
        });
      }
      setCheckingSimilarity(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to check for similar positions',
        variant: 'destructive',
      });
      setCheckingSimilarity(false);
    },
  });

  const createPositionMutation = useMutation({
    mutationFn: (data: PositionCreateRequest) => apiClient.createPosition(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      toast({
        title: 'Position created',
        description: 'The position has been created successfully.',
      });
      // Store the created position ID and open distribution dialog
      setCreatedPositionId(data.id);
      setShowDistributionDialog(true);
      // Clear all session storage
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
      sessionStorage.removeItem(FORM_STORAGE_KEY);
      // Reset state
      setMessages([]);
      setSessionId(null);
      setChatComplete(false);
      setChatPositionData(null);
      setSimilarPositions([]);
      setSimilarityWarningShown(false);
      setPendingPositionData(null);
      setFormData({
        title: '',
        team_id: '',
        description: '',
        requirements: [],
        must_haves: [],
        nice_to_haves: [],
        experience_level: '',
        responsibilities: [],
        tech_stack: [],
        domains: [],
        team_context: '',
        reporting_to: '',
        collaboration: [],
        priority: 'medium',
        status: 'open',
      });
      setRequirementsInput('');
      setMustHavesInput('');
      setNiceToHavesInput('');
      setResponsibilitiesInput('');
      setTechStackInput('');
      setDomainsInput('');
      setCollaborationInput('');
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create position',
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
    setChatPositionData(null);
    setStreamingMessage('');
    setIsStreaming(false);
  };

  const handleClearForm = () => {
    sessionStorage.removeItem(FORM_STORAGE_KEY);
    setFormData({
      title: '',
      team_id: '',
      description: '',
      requirements: [],
      must_haves: [],
      nice_to_haves: [],
      experience_level: '',
      responsibilities: [],
      tech_stack: [],
      domains: [],
      team_context: '',
      reporting_to: '',
      collaboration: [],
      priority: 'medium',
      status: 'open',
    });
    setRequirementsInput('');
    setMustHavesInput('');
    setNiceToHavesInput('');
    setResponsibilitiesInput('');
    setTechStackInput('');
    setDomainsInput('');
    setCollaborationInput('');
    setSimilarPositions([]);
    setSimilarityWarningShown(false);
    setPendingPositionData(null);
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
    if (!formData.title.trim()) {
      toast({
        title: 'Missing Information',
        description: 'Position title is required.',
        variant: 'destructive',
      });
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

    const positionData: PositionCreateRequest = {
      ...formData,
      requirements: requirements.length > 0 ? requirements : undefined,
      must_haves: mustHaves.length > 0 ? mustHaves : undefined,
      nice_to_haves: niceToHaves.length > 0 ? niceToHaves : undefined,
      responsibilities: responsibilities.length > 0 ? responsibilities : undefined,
      tech_stack: techStack.length > 0 ? techStack : undefined,
      domains: domains.length > 0 ? domains : undefined,
      collaboration: collaboration.length > 0 ? collaboration : undefined,
      team_id: formData.team_id || undefined,
    };

    // If similarity warning was already shown, proceed with creation
    if (similarityWarningShown && pendingPositionData) {
      createPositionMutation.mutate(positionData);
      return;
    }

    // Check for similar positions before creating
    setCheckingSimilarity(true);
    checkSimilarityMutation.mutate(positionData, {
      onSuccess: (response) => {
        setCheckingSimilarity(false);
        setSimilarPositions(response.similar_positions);
        
        if (response.has_duplicates) {
          // Show warning with details
          toast({
            title: 'Similar Positions Found',
            description: `Found ${response.similar_positions.length} similar position(s) with ${(response.threshold * 100).toFixed(0)}%+ similarity. Click "Create Position" again to proceed.`,
            variant: 'default',
          });
          // Scroll to top to show the alert
          setTimeout(() => {
            const formContainer = document.querySelector('[data-form-container]');
            if (formContainer) {
              formContainer.scrollTo({ top: 0, behavior: 'smooth' });
            }
          }, 100);
          // Mark that we've shown the warning and store the position data
          setSimilarityWarningShown(true);
          setPendingPositionData(positionData);
          // Don't proceed automatically - let user review and click again
          return;
        }
        
        // No duplicates found, proceed with creation
        setSimilarityWarningShown(false);
        setPendingPositionData(null);
        createPositionMutation.mutate(positionData);
      },
      onError: (error: Error) => {
        setCheckingSimilarity(false);
        // Log error but still allow creation
        console.error('Similarity check failed:', error);
        toast({
          title: 'Warning',
          description: 'Could not check for similar positions. Proceeding with creation.',
          variant: 'default',
        });
        // Proceed with creation even if check fails
        setSimilarityWarningShown(false);
        setPendingPositionData(null);
        createPositionMutation.mutate(positionData);
      },
    });
  };

  const canSubmit = formData.title.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b flex-shrink-0">
          <DialogTitle>Create New Position</DialogTitle>
          <DialogDescription>
            Use chat or form to create your position. Your progress is saved automatically.
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

            {chatComplete && chatPositionData && (
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
                  placeholder={messages.length === 0 ? "Start by typing the role you're looking to fill..." : "Type your answer or update information..."}
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
            <div className="flex-1 overflow-y-auto px-6 py-4" data-form-container>
              <div className="space-y-4">
                {similarPositions.length > 0 && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="space-y-2">
                        <p className="font-semibold">Similar positions found:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          {similarPositions.map((pos, idx) => (
                            <li key={idx}>
                              {pos.title} ({(pos.similarity * 100).toFixed(1)}% similar)
                            </li>
                          ))}
                        </ul>
                        <p className="text-xs text-muted-foreground mt-2">
                          You can still create this position if it's different.
                        </p>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="title">Position Title *</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    placeholder="e.g., Senior LLM Inference Engineer"
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
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Full job description..."
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="must_haves">Must-Have Skills (comma-separated) *</Label>
                  <Input
                    id="must_haves"
                    value={mustHavesInput}
                    onChange={(e) => setMustHavesInput(e.target.value)}
                    placeholder="e.g., CUDA, C++, PyTorch"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nice_to_haves">Nice-to-Have Skills (comma-separated)</Label>
                  <Input
                    id="nice_to_haves"
                    value={niceToHavesInput}
                    onChange={(e) => setNiceToHavesInput(e.target.value)}
                    placeholder="e.g., TensorFlow, Distributed Systems"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="requirements">Requirements (comma-separated)</Label>
                  <Input
                    id="requirements"
                    value={requirementsInput}
                    onChange={(e) => setRequirementsInput(e.target.value)}
                    placeholder="e.g., 5+ years CUDA, PhD in CS"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="experience_level">Experience Level</Label>
                  <Select
                    value={formData.experience_level || 'none'}
                    onValueChange={(value) => setFormData({ ...formData, experience_level: value === 'none' ? undefined : value })}
                  >
                    <SelectTrigger id="experience_level">
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
                  <Label htmlFor="responsibilities">Responsibilities (comma-separated)</Label>
                  <Input
                    id="responsibilities"
                    value={responsibilitiesInput}
                    onChange={(e) => setResponsibilitiesInput(e.target.value)}
                    placeholder="e.g., Optimize LLM inference, Build GPU systems"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tech_stack">Tech Stack (comma-separated)</Label>
                  <Input
                    id="tech_stack"
                    value={techStackInput}
                    onChange={(e) => setTechStackInput(e.target.value)}
                    placeholder="e.g., Python, CUDA, PyTorch"
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
                  <Label htmlFor="team_context">Team Context</Label>
                  <Textarea
                    id="team_context"
                    value={formData.team_context || ''}
                    onChange={(e) => setFormData({ ...formData, team_context: e.target.value })}
                    placeholder="How this role fits in the team..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reporting_to">Reporting To</Label>
                  <Input
                    id="reporting_to"
                    value={formData.reporting_to || ''}
                    onChange={(e) => setFormData({ ...formData, reporting_to: e.target.value })}
                    placeholder="e.g., Engineering Manager"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="collaboration">Collaboration (comma-separated)</Label>
                  <Input
                    id="collaboration"
                    value={collaborationInput}
                    onChange={(e) => setCollaborationInput(e.target.value)}
                    placeholder="e.g., Research Team, Infrastructure Team"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <Select
                    value={formData.priority || 'medium'}
                    onValueChange={(value) => setFormData({ ...formData, priority: value })}
                  >
                    <SelectTrigger id="priority">
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
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
              disabled={!canSubmit || createPositionMutation.isPending || checkingSimilarity}
            >
              {checkingSimilarity ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking...
                </>
              ) : createPositionMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : similarityWarningShown ? (
                'Create Position Anyway'
              ) : (
                'Create Position'
              )}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>

      {/* Distribution Dialog */}
      {createdPositionId && (
        <PositionDistributionDialog
          open={showDistributionDialog}
          onOpenChange={(open) => {
            setShowDistributionDialog(open);
            if (!open) {
              setCreatedPositionId(null);
            }
          }}
          positionId={createdPositionId}
        />
      )}
    </Dialog>
  );
}

