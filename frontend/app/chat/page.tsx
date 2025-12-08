'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Loader2, Send, Bot, User, Sparkles, History, X } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  results?: any[];
  error?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const [conversations, setConversations] = useState<Array<{ id: string; title: string; lastMessage: string; timestamp: Date }>>([]);
  const [showHistory, setShowHistory] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize session and welcome message on client side only
  useEffect(() => {
    if (typeof window !== 'undefined' && !sessionId) {
      const newSessionId = `session-${Date.now()}`;
      setSessionId(newSessionId);
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: "Hi! I'm your knowledge graph assistant. I can help you explore candidates, teams, positions, and interviewers. Try asking me things like:\n\n• \"Find ML engineers with 5+ arXiv papers\"\n• \"Show me teams that need Python developers\"\n• \"Match this candidate to positions\"\n• \"What's the pipeline status for @username?\"",
          timestamp: new Date(),
        },
      ]);
      
      // Load conversation history from localStorage
      const savedConversations = localStorage.getItem('chat_conversations');
      if (savedConversations) {
        try {
          const parsed = JSON.parse(savedConversations);
          setConversations(parsed.map((c: any) => ({
            ...c,
            timestamp: new Date(c.timestamp),
          })));
        } catch (e) {
          console.error('Error loading conversations:', e);
        }
      }
    }
  }, [sessionId]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId && messages.length > 1) {
      const conversationData = {
        id: sessionId,
        messages: messages.map(m => ({
          ...m,
          timestamp: m.timestamp.toISOString(),
        })),
        title: messages.find(m => m.role === 'user')?.content.slice(0, 50) || 'New Conversation',
        lastMessage: messages[messages.length - 1]?.content.slice(0, 100) || '',
        timestamp: new Date().toISOString(),
      };
      
      // Save full conversation
      const conversationKey = `chat_${sessionId}`;
      localStorage.setItem(conversationKey, JSON.stringify(conversationData));
      
      // Update conversations list
      const savedConversations = localStorage.getItem('chat_conversations');
      const conversationsList = savedConversations ? JSON.parse(savedConversations) : [];
      const filtered = conversationsList.filter((c: any) => c.id !== sessionId);
      const updated = [{
        id: sessionId,
        title: conversationData.title,
        lastMessage: conversationData.lastMessage,
        timestamp: conversationData.timestamp,
      }, ...filtered].slice(0, 20);
      localStorage.setItem('chat_conversations', JSON.stringify(updated));
      setConversations(updated.map((c: any) => ({
        ...c,
        timestamp: new Date(c.timestamp),
      })));
    }
  }, [messages, sessionId]);

  const chatMutation = useMutation({
    mutationFn: async (query: string) => {
      return apiClient.chatWithGraph(query, sessionId, messages.slice(-10)); // Last 10 messages for context
    },
    onSuccess: (response) => {
      const newMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        results: response.results,
      };
      setMessages((prev) => [...prev, newMessage]);
    },
    onError: (error: Error) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}. Please try rephrasing your question.`,
        timestamp: new Date(),
        error: error.message,
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    chatMutation.mutate(input.trim());
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Scroll to bottom when messages change
      setTimeout(() => {
        const viewport = scrollRef.current?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement;
        if (viewport) {
          viewport.scrollTop = viewport.scrollHeight;
        }
      }, 100);
    }
  }, [messages]);

  const startNewConversation = () => {
    const newSessionId = `session-${Date.now()}`;
    setSessionId(newSessionId);
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: "Hi! I'm your knowledge graph assistant. I can help you explore candidates, teams, positions, and interviewers. Try asking me things like:\n\n• \"Find ML engineers with 5+ arXiv papers\"\n• \"Show me teams that need Python developers\"\n• \"Match this candidate to positions\"\n• \"What's the pipeline status for @username?\"",
        timestamp: new Date(),
      },
    ]);
    setShowHistory(false);
  };

  const loadConversation = (convId: string) => {
    if (typeof window === 'undefined') return;
    
    try {
      // Load full conversation from localStorage
      const conversationKey = `chat_${convId}`;
      const saved = localStorage.getItem(conversationKey);
      
      if (saved) {
        const conversation = JSON.parse(saved);
        setSessionId(convId);
        // Restore messages with proper Date objects
        const restoredMessages = conversation.messages.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp),
        }));
        setMessages(restoredMessages);
        
        // Scroll to bottom after messages are loaded
        setTimeout(() => {
          const viewport = scrollRef.current?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement;
          if (viewport) {
            viewport.scrollTop = viewport.scrollHeight;
          }
        }, 100);
      } else {
        // Fallback: start new conversation if saved data not found
        startNewConversation();
      }
    } catch (e) {
      console.error('Error loading conversation:', e);
      startNewConversation();
    }
    
    setShowHistory(false);
  };

  if (!sessionId) {
    return null; // Prevent hydration mismatch
  }

  return (
    <div className="container mx-auto p-6 h-screen flex flex-col max-w-6xl">
      <div className="mb-6 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <Sparkles className="h-6 w-6 text-primary" />
            <h1 className="text-3xl font-bold">Knowledge Graph Chat</h1>
          </div>
          <DropdownMenu open={showHistory} onOpenChange={setShowHistory}>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="relative">
                <History className="h-4 w-4" />
                {conversations.length > 0 && (
                  <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
                    {conversations.length}
                  </span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <div className="p-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold">Conversation History</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={startNewConversation}
                    className="h-7 text-xs"
                  >
                    New Chat
                  </Button>
                </div>
              </div>
              <DropdownMenuSeparator />
              {conversations.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No previous conversations
                </div>
              ) : (
                <div className="max-h-96 overflow-y-auto">
                  {conversations.map((conv) => (
                    <DropdownMenuItem
                      key={conv.id}
                      onClick={() => loadConversation(conv.id)}
                      className="flex flex-col items-start p-3 cursor-pointer"
                    >
                      <div className="font-medium text-sm truncate w-full">{conv.title}</div>
                      <div className="text-xs text-muted-foreground truncate w-full mt-1">
                        {conv.lastMessage}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {conv.timestamp.toLocaleDateString()} {conv.timestamp.toLocaleTimeString()}
                      </div>
                    </DropdownMenuItem>
                  ))}
                </div>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <p className="text-muted-foreground">
          Ask me anything about your candidates, teams, positions, and interviewers. I'll search the knowledge graph and give you intelligent answers.
        </p>
      </div>

      <Card className="flex-1 flex flex-col border-2 min-h-0 overflow-hidden">
        <CardHeader className="border-b flex-shrink-0">
          <CardTitle className="text-lg">Conversation</CardTitle>
          <CardDescription>
            {messages.length} messages • Session: {sessionId.slice(-8)}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col p-0 min-h-0 overflow-hidden">
          <div className="flex-1 min-h-0 overflow-hidden">
            <ScrollArea className="h-full p-6" ref={scrollRef}>
            <div className="space-y-4">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                      {message.results && message.results.length > 0 && (
                        <div className="mt-4 space-y-2">
                          {message.results.map((result, idx) => (
                            <div
                              key={idx}
                              className="bg-background/50 rounded p-3 text-xs border"
                            >
                              <div className="font-semibold mb-1">
                                {result.type}: {result.name || result.id}
                              </div>
                              {result.similarity && (
                                <Badge variant="secondary" className="text-xs">
                                  {(result.similarity * 100).toFixed(1)}% match
                                </Badge>
                              )}
                              {result.details && (
                                <div className="mt-2 text-muted-foreground">
                                  {Object.entries(result.details).slice(0, 3).map(([key, value]) => (
                                    <div key={key}>
                                      <span className="font-medium">{key}:</span> {String(value)}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      {message.error && (
                        <div className="mt-2 text-xs text-destructive">{message.error}</div>
                      )}
                      <div className="text-xs text-muted-foreground mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                    {message.role === 'user' && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-4 w-4 text-primary" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {chatMutation.isPending && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3 justify-start"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Searching knowledge graph...</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
            </ScrollArea>
          </div>

          <form onSubmit={handleSubmit} className="border-t p-4 flex-shrink-0 bg-background">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything about your knowledge graph..."
                disabled={chatMutation.isPending}
                className="flex-1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <Button
                type="submit"
                disabled={!input.trim() || chatMutation.isPending}
                size="icon"
              >
                {chatMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

