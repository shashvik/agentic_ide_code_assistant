import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Code, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  hasCode?: boolean;
}

interface ChatPanelProps {
  onCodeGenerate?: (code: string, language: string) => void;
}

export function ChatPanel({ onCodeGenerate }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm your AI coding assistant. I can help you write code, debug issues, and answer programming questions. What would you like to build today?",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        role: 'assistant',
        timestamp: new Date(),
        hasCode: !!data.code,
      };

      setMessages((prev) => [...prev, aiMessage]);

      if (data.code && onCodeGenerate) {
        onCodeGenerate(data.code, data.language);
      }
    } catch (error) {
      console.error('There was a problem with the fetch operation:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I had trouble connecting to the backend. Please check the console for details.',
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-chat border-r border-panel-border">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-panel-border bg-chat-bg/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-semibold text-foreground">AI Assistant</h2>
            <p className="text-xs text-muted-foreground">Ready to help with coding</p>
          </div>
        </div>
        <div className="ml-auto">
          <Sparkles className="w-4 h-4 text-accent animate-pulse" />
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 max-w-[85%]",
                message.role === "user" ? "ml-auto flex-row-reverse" : ""
              )}
            >
              <div className={cn(
                "w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0",
                message.role === "user" 
                  ? "bg-message-user text-white" 
                  : "bg-message-ai text-white"
              )}>
                {message.role === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
              </div>
              
              <div className={cn(
                "rounded-lg p-3 break-words",
                message.role === "user"
                  ? "bg-message-user text-white"
                  : "bg-secondary text-secondary-foreground"
              )}>
                {message.hasCode && message.role === "assistant" && (
                  <div className="flex items-center gap-1 mb-2 text-xs text-accent">
                    <Code className="w-3 h-3" />
                    Code generated
                  </div>
                )}
                <p className="text-sm leading-relaxed">{message.content}</p>
                <div className="mt-2 text-xs opacity-70">
                  {message.timestamp.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3 max-w-[85%]">
              <div className="w-7 h-7 rounded-full bg-message-ai flex items-center justify-center">
                <Bot className="w-3 h-3" />
              </div>
              <div className="bg-secondary rounded-lg p-3">
                <div className="flex items-center gap-1">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                  </div>
                  <span className="text-xs text-muted-foreground ml-2">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-panel-border bg-chat-bg/30">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me to create code, debug issues, or answer coding questions..."
            className="bg-code-bg border-border"
            disabled={isTyping}
          />
          <Button 
            onClick={handleSend} 
            disabled={!input.trim() || isTyping}
            className="bg-gradient-primary hover:opacity-90 transition-opacity"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 px-1">
          Pro tip: Ask me to "create a React component" or "write Python code" for instant code generation!
        </p>
      </div>
    </div>
  );
}