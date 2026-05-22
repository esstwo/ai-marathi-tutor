import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, User, Sparkles, Square, Zap, Volume2, Mic, MicOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Logo } from "@/components/Logo";
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
  const [playingId, setPlayingId] = useState<number | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // ── TTS ──────────────────────────────────────────────────────────────

  const playTTS = useCallback(async (text: string, messageId: number) => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      setPlayingId(messageId);
      const blob = await api.speakMarathiTTS(text);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        setPlayingId(null);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };
      audio.onerror = () => {
        setPlayingId(null);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };

      await audio.play();
    } catch {
      setPlayingId(null);
    }
  }, []);

  // ── Conversation lifecycle ──────────────────────────────────────────

  // Start conversation on mount
  useEffect(() => {
    if (!activeChild) return;

    let cancelled = false;
    (async () => {
      try {
        const res = await api.startConversation(activeChild.id);
        if (cancelled) return;
        const msgId = Date.now();
        setConversationId(res.conversation_id);
        setMessages([
          {
            id: msgId,
            role: "assistant",
            content: res.marathi_text,
            hint: res.english_hint ?? undefined,
          },
        ]);
        // Auto-play greeting
        playTTS(res.marathi_text, msgId);
      } catch (err: any) {
        if (!cancelled) {
          toast.error("Failed to start conversation");
        }
      } finally {
        if (!cancelled) setIsStarting(false);
      }
    })();

    return () => { cancelled = true; };
  }, [activeChild, playTTS]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      api.sendMessage(conversationId!, message),
    onSuccess: (data) => {
      const msgId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        {
          id: msgId,
          role: "assistant",
          content: data.marathi_text,
          hint: data.english_hint ?? undefined,
        },
      ]);
      setIsTyping(false);
      // Auto-play Mitra's reply
      playTTS(data.marathi_text, msgId);
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
      // Stop any playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
        setPlayingId(null);
      }
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

    // Stop any playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setPlayingId(null);
    }

    (async () => {
      try {
        const res = await api.startConversation(activeChild!.id);
        const msgId = Date.now();
        setConversationId(res.conversation_id);
        setMessages([
          {
            id: msgId,
            role: "assistant",
            content: res.marathi_text,
            hint: res.english_hint ?? undefined,
          },
        ]);
        playTTS(res.marathi_text, msgId);
      } catch {
        toast.error("Failed to start new conversation");
      } finally {
        setIsStarting(false);
      }
    })();
  };

  // ── Voice recording ──────────────────────────────────────────────────

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size === 0) return;

        setIsTranscribing(true);
        try {
          const text = await api.transcribeAudio(blob);
          if (text) setInput((prev) => (prev ? prev + " " + text : text));
        } catch {
          toast.error("Could not transcribe audio");
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      toast.error("Microphone access denied");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full">
        {/* Header */}
        <div className="px-4 py-4 border-b flex items-center gap-3">
          <Logo size={48} />
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
                      <Logo size={20} />
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
                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-2 mt-1 ml-2">
                      {msg.hint && (
                        <p className="text-xs text-muted-foreground italic">
                          {msg.hint}
                        </p>
                      )}
                      <button
                        onClick={() => playTTS(msg.content, msg.id)}
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-full transition-colors ${
                          playingId === msg.id
                            ? "text-primary animate-pulse"
                            : "text-muted-foreground hover:text-primary"
                        }`}
                        title="Play audio"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3 animate-pop">
                <Avatar className="h-9 w-9 shrink-0 mt-0.5">
                  <AvatarFallback className="bg-primary/15 text-primary rounded-xl">
                    <Logo size={20} />
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
                placeholder={isTranscribing ? "Transcribing..." : "Type or tap mic to speak..."}
                className="flex-1 rounded-2xl bg-muted/50 border-border/50 h-12 text-base font-medium"
                disabled={isTyping || isTranscribing || !conversationId}
              />
              <Button
                type="button"
                size="icon"
                variant={isRecording ? "destructive" : "outline"}
                className={`rounded-2xl shrink-0 w-12 h-12 ${isRecording ? "animate-pulse" : ""}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isTyping || isTranscribing || !conversationId}
              >
                {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </Button>
              <Button
                type="submit"
                size="icon"
                variant="hero"
                className="rounded-2xl shrink-0 w-12 h-12 fun-shadow"
                disabled={!input.trim() || isTyping || isTranscribing || !conversationId}
              >
                <Send className="h-5 w-5" />
              </Button>
            </form>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Chats;
