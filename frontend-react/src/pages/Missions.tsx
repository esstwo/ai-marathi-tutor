import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Send, Target, Sparkles, Volume2, ArrowLeft, Star, User, Square, Trophy, Mic, MicOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Logo } from "@/components/Logo";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";
import type { Mission, MissionProgress } from "@/types";

interface MissionMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  hint?: string;
}

type View = "list" | "play";

const Missions = () => {
  const { activeChild } = useAuth();
  const queryClient = useQueryClient();
  const level = activeChild?.current_level ?? 1;

  // ── State ─────────────────────────────────────────────────────────
  const [view, setView] = useState<View>("list");
  const [activeMission, setActiveMission] = useState<Mission | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MissionMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [missionStep, setMissionStep] = useState(1);
  const [totalSteps, setTotalSteps] = useState(5);
  const [missionComplete, setMissionComplete] = useState(false);
  const [completionData, setCompletionData] = useState<{
    xp_earned: number;
    score: number;
  } | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [topic, setTopic] = useState("");
  const [playingId, setPlayingId] = useState<number | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // ── Data fetching ─────────────────────────────────────────────────
  const { data: missions = [], refetch: refetchMissions } = useQuery({
    queryKey: ["missions", level],
    queryFn: () => api.listMissions(level),
    enabled: !!activeChild,
  });

  const { data: progressData = [] } = useQuery({
    queryKey: ["mission-progress", activeChild?.id],
    queryFn: () => api.getMissionProgress(activeChild!.id),
    enabled: !!activeChild,
  });

  const progressMap = new Map(
    progressData.map((p: MissionProgress) => [p.mission_id, p])
  );

  // ── TTS ───────────────────────────────────────────────────────────
  const playTTS = useCallback(async (text: string, messageId: number) => {
    try {
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

  // ── Scroll ────────────────────────────────────────────────────────
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // ── Generate mission ──────────────────────────────────────────────
  const handleGenerate = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!activeChild || isGenerating) return;
    setIsGenerating(true);
    try {
      await api.generateMission(activeChild.id, level, topic.trim() || undefined);
      setTopic("");
      refetchMissions();
      toast.success("New mission created!");
    } catch {
      toast.error("Failed to generate mission");
    } finally {
      setIsGenerating(false);
    }
  };

  // ── Start mission ─────────────────────────────────────────────────
  const handleStartMission = async (mission: Mission) => {
    if (!activeChild) return;
    setActiveMission(mission);
    setView("play");
    setIsStarting(true);
    setMessages([]);
    setMissionComplete(false);
    setCompletionData(null);
    setMissionStep(1);
    setTotalSteps(mission.steps?.length || 5);

    try {
      const res = await api.startMission(activeChild.id, mission.id);
      const msgId = Date.now();
      setConversationId(res.conversation_id);
      setMissionStep(res.mission_step);
      setTotalSteps(res.total_steps);
      setMessages([
        { id: msgId, role: "assistant", content: res.marathi_text, hint: res.english_hint ?? undefined },
      ]);
      playTTS(res.marathi_text, msgId);
    } catch {
      toast.error("Failed to start mission");
      setView("list");
    } finally {
      setIsStarting(false);
    }
  };

  // ── Send message ──────────────────────────────────────────────────
  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      api.sendMissionMessage(conversationId!, message),
    onSuccess: (data) => {
      const msgId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { id: msgId, role: "assistant", content: data.marathi_text, hint: data.english_hint ?? undefined },
      ]);
      setIsTyping(false);
      setMissionStep(data.mission_step);
      playTTS(data.marathi_text, msgId);

      if (data.mission_complete) {
        setMissionComplete(true);
        setCompletionData({
          xp_earned: data.xp_earned ?? 0,
          score: data.score ?? 0,
        });
        queryClient.invalidateQueries({ queryKey: ["mission-progress", activeChild?.id] });
        queryClient.invalidateQueries({ queryKey: ["progress", activeChild?.id] });
      }
    },
    onError: () => {
      toast.error("Failed to send message");
      setIsTyping(false);
    },
  });

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || !conversationId || isTyping || missionComplete) return;
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", content: msg }]);
    setInput("");
    setIsTyping(true);
    sendMutation.mutate(msg);
  };

  // ── Voice recording ──────────────────────────────────────────────
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

  // ── Quit mission ──────────────────────────────────────────────────
  const handleQuit = async () => {
    if (conversationId) {
      try {
        await api.endMission(conversationId);
      } catch { /* ignore */ }
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setPlayingId(null);
    }
    setView("list");
    setActiveMission(null);
    setConversationId(null);
    refetchMissions();
  };

  const handleBackToList = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setPlayingId(null);
    }
    setView("list");
    setActiveMission(null);
    setConversationId(null);
    queryClient.invalidateQueries({ queryKey: ["mission-progress", activeChild?.id] });
  };

  // ── Score stars ───────────────────────────────────────────────────
  const scoreStars = (score: number) => {
    const stars = score >= 80 ? 3 : score >= 50 ? 2 : score > 0 ? 1 : 0;
    return Array.from({ length: 3 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < stars ? "text-yellow-400 fill-yellow-400" : "text-gray-300"}`}
      />
    ));
  };

  // ══════════════════════════════════════════════════════════════════
  // MISSION LIST VIEW
  // ══════════════════════════════════════════════════════════════════
  if (view === "list") {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Navbar />
        <div className="flex-1 container mx-auto max-w-2xl px-4 py-8 space-y-6">
          <div className="text-center animate-pop">
            <h1 className="font-display text-2xl md:text-3xl font-bold text-foreground flex items-center justify-center gap-2">
              <Target className="w-7 h-7 text-primary" />
              Missions
            </h1>
            <p className="text-muted-foreground mt-1 font-display font-medium">
              Complete fun Marathi challenges!
            </p>
          </div>

          <form onSubmit={handleGenerate} className="flex gap-2">
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="What should the mission be about? (e.g. visiting grandma, Diwali…)"
              className="flex-1 rounded-2xl bg-muted/50 border-border/50 h-12 text-base"
              disabled={isGenerating}
            />
            <Button
              type="submit"
              variant="hero"
              className="rounded-2xl font-bold shrink-0 h-12 px-4"
              disabled={isGenerating}
            >
              {isGenerating ? (
                <Sparkles className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
            </Button>
          </form>

          {missions.length === 0 && !isGenerating && (
            <div className="text-center py-8">
              <p className="text-muted-foreground font-display font-bold">
                No missions yet — type a theme above or leave it blank for a surprise!
              </p>
            </div>
          )}

          <div className="space-y-3">
            {missions.map((mission: Mission, i: number) => {
              const prog = progressMap.get(mission.id);
              const isCompleted = prog?.status === "completed";

              return (
                <Card
                  key={mission.id}
                  className="gradient-card rounded-2xl border-2 border-border/50 hover:fun-shadow-hover hover:-translate-y-1 transition-all duration-300 animate-pop cursor-pointer"
                  style={{ animationDelay: `${i * 80}ms` }}
                  onClick={() => handleStartMission(mission)}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className={`h-12 w-12 rounded-2xl flex items-center justify-center shrink-0 ${
                      isCompleted ? "bg-mint/40" : "bg-peach/40"
                    }`}>
                      {isCompleted ? (
                        <Trophy className="h-6 w-6 text-foreground" />
                      ) : (
                        <Target className="h-6 w-6 text-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-display font-bold text-foreground truncate">
                        {mission.title}
                      </p>
                      <p className="text-sm text-muted-foreground truncate">
                        {mission.title_english}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className="text-xs font-display font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                        {mission.xp_reward} XP
                      </span>
                      {isCompleted && (
                        <div className="flex">{scoreStars(prog!.score)}</div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

        </div>
        <Footer />
      </div>
    );
  }

  // ══════════════════════════════════════════════════════════════════
  // MISSION PLAY VIEW
  // ══════════════════════════════════════════════════════════════════
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full">
        {/* Header with step progress */}
        <div className="px-4 py-3 border-b">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-xl shrink-0"
              onClick={missionComplete ? handleBackToList : handleQuit}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex-1 min-w-0">
              <p className="font-display font-bold text-sm text-foreground truncate">
                {activeMission?.title}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {activeMission?.title_english}
              </p>
            </div>
            {!missionComplete && conversationId && (
              <Button
                variant="outline"
                size="sm"
                className="rounded-xl font-display font-bold text-destructive border-destructive/30 hover:bg-destructive/10 shrink-0"
                onClick={handleQuit}
              >
                <Square className="w-3 h-3 mr-1" />
                Quit
              </Button>
            )}
          </div>

          {/* Step progress bar */}
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs font-display font-bold text-muted-foreground shrink-0">
              Step {missionStep}/{totalSteps}
            </span>
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${(missionStep / totalSteps) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Completion overlay */}
        {missionComplete && completionData && (
          <div className="absolute inset-0 z-50 bg-background/90 backdrop-blur-sm flex items-center justify-center animate-pop">
            <div className="text-center space-y-4 p-8">
              <p className="text-6xl">🎉</p>
              <h2 className="font-display text-2xl font-bold text-foreground">
                Mission Complete!
              </h2>
              <div className="flex justify-center gap-1">
                {scoreStars(completionData.score)}
              </div>
              <p className="text-lg font-display font-bold text-primary">
                +{completionData.xp_earned} XP
              </p>
              <p className="text-sm text-muted-foreground">
                Score: {completionData.score}%
              </p>
              <Button
                variant="hero"
                className="rounded-xl font-bold mt-4"
                onClick={handleBackToList}
              >
                Back to Missions
              </Button>
            </div>
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 px-4 py-4" ref={scrollRef}>
          <div className="space-y-4 pb-2">
            {isStarting && messages.length === 0 && (
              <div className="flex justify-center py-20">
                <div className="flex items-center gap-2 text-muted-foreground font-display font-bold">
                  <Sparkles className="w-5 h-5 animate-bounce-gentle text-primary" />
                  Setting the scene...
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
                <div className="max-w-[80%]">
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
                        <p className="text-xs text-muted-foreground italic">{msg.hint}</p>
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
          {missionComplete ? (
            <div className="text-center py-2">
              <p className="text-sm text-muted-foreground font-display font-bold flex items-center justify-center gap-2">
                <Trophy className="w-4 h-4 text-primary" />
                Mission complete! Great job!
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

export default Missions;
