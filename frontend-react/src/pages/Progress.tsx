import { useQuery } from "@tanstack/react-query";
import { Trophy, Flame, BookOpen, MessageCircle, Star, ChevronRight, Target, Zap, Sparkles, Rocket, Award, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress as ProgressBar } from "@/components/ui/progress";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";

const levels = [
  { level: 1, name: "Beginner", xpNeeded: 0 },
  { level: 2, name: "Explorer", xpNeeded: 100 },
  { level: 3, name: "Learner", xpNeeded: 300 },
  { level: 4, name: "Speaker", xpNeeded: 600 },
  { level: 5, name: "Fluent", xpNeeded: 1000 },
];

function getCurrentLevel(xp: number) {
  let current = levels[0];
  for (const l of levels) {
    if (xp >= l.xpNeeded) current = l;
    else break;
  }
  return current;
}

function getNextLevel(xp: number) {
  for (const l of levels) {
    if (xp < l.xpNeeded) return l;
  }
  return null;
}

const ProgressPage = () => {
  const { activeChild } = useAuth();
  const { data: progress, isLoading } = useQuery({
    queryKey: ["progress", activeChild?.id],
    queryFn: () => api.getProgress(activeChild!.id),
    enabled: !!activeChild,
  });

  if (isLoading || !progress) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  const xp = progress.xp_total;
  const currentLevel = getCurrentLevel(xp);
  const nextLevel = getNextLevel(xp);
  const xpForNext = nextLevel ? nextLevel.xpNeeded - currentLevel.xpNeeded : 0;
  const xpProgress = nextLevel ? xp - currentLevel.xpNeeded : xpForNext;
  const progressPercent = xpForNext > 0 ? (xpProgress / xpForNext) * 100 : 100;
  const xpRemaining = nextLevel ? nextLevel.xpNeeded - xp : 0;

  const stats = [
    { icon: Flame, label: "Day Streak", value: progress.streak_days, bg: "bg-peach/40" },
    { icon: BookOpen, label: "Lessons Done", value: progress.lessons_completed, bg: "bg-mint/40" },
    { icon: MessageCircle, label: "Chats", value: progress.conversations_count, bg: "bg-lavender/40" },
    { icon: Zap, label: "Total XP", value: xp, bg: "bg-lemon/40" },
  ];

  const nextLevelTips = [
    { icon: BookOpen, text: "Complete more lessons", xp: "+10 XP each", bg: "bg-mint/30" },
    { icon: MessageCircle, text: "Chat with Mitra", xp: "+5 XP/min", bg: "bg-lavender/30" },
    { icon: Target, text: "Get a perfect quiz score", xp: "Bonus XP", bg: "bg-peach/30" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="container mx-auto max-w-2xl px-4 py-8 space-y-6">
        <div className="text-center mb-2">
          <div className="inline-flex items-center gap-2 bg-lemon/40 text-foreground px-4 py-2 rounded-full text-sm font-display font-bold mb-3 animate-bounce-gentle">
            <Sparkles className="w-4 h-4 text-primary" />
            Look how far you've come!
          </div>
        </div>

        {/* Level Card */}
        <Card className="gradient-card overflow-hidden rounded-3xl border-2 border-border/50 fun-shadow animate-pop">
          <CardContent className="p-6">
            <div className="flex items-center gap-4 mb-5">
              <div className="h-[72px] w-[72px] rounded-2xl bg-lemon/40 flex items-center justify-center">
                <Trophy className="h-10 w-10 text-primary animate-bounce-gentle" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground font-display font-bold">Your Level</p>
                <h1 className="font-display text-2xl md:text-3xl font-bold text-foreground">
                  Level {currentLevel.level} — {currentLevel.name}
                </h1>
                <p className="text-sm text-primary font-display font-bold mt-0.5">
                  {xp} XP earned!
                </p>
              </div>
            </div>

            {nextLevel ? (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground font-display font-bold">
                    Next: Level {nextLevel.level}
                  </span>
                  <span className="font-display font-bold text-primary">
                    {xpRemaining} XP to go!
                  </span>
                </div>
                <ProgressBar value={progressPercent} className="h-4 rounded-full" />
                <div className="flex justify-between text-xs text-muted-foreground font-display font-bold">
                  <span>{currentLevel.name}</span>
                  <span>{nextLevel.name}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-2">
                <p className="font-display font-bold text-primary text-lg">
                  Max level reached! You're amazing!
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          {stats.map((stat, i) => (
            <Card
              key={stat.label}
              className="gradient-card rounded-3xl border-2 border-border/50 hover:fun-shadow-hover hover:-translate-y-1 transition-all duration-300 animate-pop"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <CardContent className="p-5 flex items-center gap-3">
                <div className={`h-12 w-12 rounded-2xl ${stat.bg} flex items-center justify-center shrink-0`}>
                  <stat.icon className="h-6 w-6 text-foreground" />
                </div>
                <div>
                  <p className="font-display text-2xl font-bold text-foreground leading-tight">
                    {stat.value}
                  </p>
                  <p className="text-xs text-muted-foreground font-display font-bold">
                    {stat.label}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Next Level Tips */}
        {nextLevel && (
          <Card className="gradient-card rounded-3xl border-2 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="font-display text-lg flex items-center gap-2">
                <Rocket className="h-5 w-5 text-primary" />
                Power Up to {nextLevel.name}!
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              {nextLevelTips.map((tip, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-3 p-4 rounded-2xl ${tip.bg} hover:-translate-y-0.5 transition-all`}
                >
                  <div className="w-10 h-10 rounded-xl bg-card/60 flex items-center justify-center shrink-0">
                    <tip.icon className="h-5 w-5 text-foreground" />
                  </div>
                  <span className="text-sm text-foreground flex-1 font-display font-bold">{tip.text}</span>
                  <span className="text-xs font-display font-bold text-primary bg-primary/10 px-3 py-1 rounded-full">
                    {tip.xp}
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Level Roadmap */}
        <Card className="gradient-card rounded-3xl border-2 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-lg flex items-center gap-2">
              <Award className="h-5 w-5 text-primary" />
              Your Journey
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-3">
              {levels.map((l) => {
                const isActive = l.level === currentLevel.level;
                const isCompleted = xp >= l.xpNeeded && l.level < currentLevel.level;
                const isLocked = l.level > currentLevel.level;

                return (
                  <div
                    key={l.level}
                    className={`flex items-center gap-3 p-4 rounded-2xl transition-all ${
                      isActive
                        ? "bg-primary/10 border-2 border-primary/25 fun-shadow"
                        : "bg-muted/30"
                    }`}
                  >
                    <div
                      className={`h-10 w-10 rounded-xl flex items-center justify-center text-base font-display font-bold ${
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : isCompleted || !isLocked
                            ? "bg-primary/20 text-primary"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {l.level}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm font-display font-bold ${isLocked ? "text-muted-foreground" : "text-foreground"}`}>
                        {l.name}
                      </p>
                      <p className="text-xs text-muted-foreground font-display">
                        {l.xpNeeded} XP needed
                      </p>
                    </div>
                    {isActive && (
                      <span className="text-xs font-bold text-primary bg-primary/10 px-3 py-1 rounded-full font-display animate-bounce-gentle">
                        You're here!
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ProgressPage;
