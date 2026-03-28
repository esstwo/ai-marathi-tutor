import { useState, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Flower2, User, Sparkles, Square, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  hint?: string;
}

const Chats = () => {
  const { activeChild } = useAuth();
  const queryClient = useQueryClient();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(true);
  const [chatEnded, setChatEnded] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Start conversation on mount
  useEffect(() => {
    if (!activeChild) return;

    let cancelled = false;
    (async () => {
      try {
        const res = await api.startConversation(activeChild.id);
        if (cancelled) return;
        setConversationId(res.conversation_id);
        setMessages([
          {
            id: Date.now(),
            role: "assistant",
            content: res.marathi_text,
            hint: res.english_hint ?? undefined,
          },
        ]);
      } catch (err: any) {
        if (!cancelled) {
          toast.error("Failed to start conversation");
        }
      } finally {
        if (!cancelled) setIsStarting(false);
      }
    })();

    return () => { cancelled = true; };
  }, [activeChild]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      api.sendMessage(conversationId!, message),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: data.marathi_text,
          hint: data.english_hint ?? undefined,
        },
      ]);
      setIsTyping(false);
    },
    onError: () => {
      toast.error("Failed to send message");
      setIsTyping(false);
    },
  });

  const endMutation = useMutation({
    mutationFn: () => api.endConversation(conversationId!),
    onSuccess: (data) => {
      setChatEnded(true);
      toast.success(
        `Chat ended! +${data.xp_earned} XP earned (${data.duration_minutes} min)`,
        { duration: 5000 }
      );
      queryClient.invalidateQueries({ queryKey: ["progress", activeChild?.id] });
    },
    onError: () => {
      toast.error("Failed to end conversation");
    },
  });

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || !conversationId || isTyping) return;

    setMessages((prev) => [...prev, { id: Date.now(), role: "user", content: msg }]);
    setInput("");
    setIsTyping(true);
    sendMutation.mutate(msg);
  };

  const handleEndChat = () => {
    if (conversationId && !chatEnded) {
      endMutation.mutate();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setChatEnded(false);
    setIsStarting(true);
    setInput("");

    (async () => {
      try {
        const res = await api.startConversation(activeChild!.id);
        setConversationId(res.conversation_id);
        setMessages([
          {
            id: Date.now(),
            role: "assistant",
            content: res.marathi_text,
            hint: res.english_hint ?? undefined,
          },
        ]);
      } catch {
        toast.error("Failed to start new conversation");
      } finally {
        setIsStarting(false);
      }
    })();
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full">
        {/* Header */}
        <div className="px-4 py-4 border-b flex items-center gap-3">
          <div className="h-12 w-12 rounded-2xl bg-primary/15 flex items-center justify-center">
            <Flower2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="font-display text-lg font-bold text-foreground">
              Marathi Mitra
            </h1>
            <p className="text-xs text-muted-foreground flex items-center gap-1 font-medium">
              <Sparkles className="h-3 w-3 text-primary" /> Your Marathi learning buddy
            </p>
          </div>
          <div className="ml-auto">
            {conversationId && !chatEnded && (
              <Button
                variant="outline"
                size="sm"
                className="rounded-xl font-display font-bold text-destructive border-destructive/30 hover:bg-destructive/10"
                onClick={handleEndChat}
                disabled={endMutation.isPending}
              >
                <Square className="w-3 h-3 mr-1" />
                End Chat
              </Button>
            )}
            {chatEnded && (
              <Button
                variant="hero"
                size="sm"
                className="rounded-xl font-bold"
                onClick={handleNewChat}
              >
                <Sparkles className="w-3 h-3 mr-1" />
                New Chat
              </Button>
            )}
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 px-4 py-4" ref={scrollRef}>
          <div className="space-y-4 pb-2">
            {isStarting && messages.length === 0 && (
              <div className="flex justify-center py-20">
                <div className="flex items-center gap-2 text-muted-foreground font-display font-bold">
                  <Sparkles className="w-5 h-5 animate-bounce-gentle text-primary" />
                  Starting conversation...
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 animate-pop ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <Avatar className="h-9 w-9 shrink-0 mt-0.5">
                  <AvatarFallback
                    className={
                      msg.role === "assistant"
                        ? "bg-primary/15 text-primary rounded-xl"
                        : "bg-lavender/50 text-foreground rounded-xl"
                    }
                  >
                    {msg.role === "assistant" ? (
                      <Flower2 className="h-4 w-4" />
                    ) : (
                      <User className="h-4 w-4" />
                    )}
                  </AvatarFallback>
                </Avatar>
                <div className={`max-w-[80%] ${msg.role === "user" ? "" : ""}`}>
                  <div
                    className={`rounded-3xl px-5 py-3 text-sm leading-relaxed whitespace-pre-line ${
                      msg.role === "assistant"
                        ? "bg-muted text-foreground rounded-tl-lg"
                        : "bg-primary text-primary-foreground rounded-tr-lg"
                    }`}
                  >
                    {msg.content}
                  </div>
                  {msg.hint && (
                    <p className="text-xs text-muted-foreground mt-1 ml-2 italic">
                      {msg.hint}
                    </p>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3 animate-pop">
                <Avatar className="h-9 w-9 shrink-0 mt-0.5">
                  <AvatarFallback className="bg-primary/15 text-primary rounded-xl">
                    <Flower2 className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-muted rounded-3xl rounded-tl-lg px-5 py-4 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="border-t p-4">
          {chatEnded ? (
            <div className="text-center py-2">
              <p className="text-sm text-muted-foreground font-display font-bold flex items-center justify-center gap-2">
                <Zap className="w-4 h-4 text-primary" />
                Chat ended. Start a new one to keep learning!
              </p>
            </div>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2"
            >
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type something fun..."
                className="flex-1 rounded-2xl bg-muted/50 border-border/50 h-12 text-base font-medium"
                disabled={isTyping || !conversationId}
              />
              <Button
                type="submit"
                size="icon"
                variant="hero"
                className="rounded-2xl shrink-0 w-12 h-12 fun-shadow"
                disabled={!input.trim() || isTyping || !conversationId}
              >
                <Send className="h-5 w-5" />
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Chats;
