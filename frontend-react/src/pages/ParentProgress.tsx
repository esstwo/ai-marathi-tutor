import { useQuery } from "@tanstack/react-query";
import { Users, BookOpen, Zap, Flame, MessageCircle, Languages, Loader2, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";

const ParentProgress = () => {
  const { userId } = useAuth();
  const { data: progress, isLoading } = useQuery({
    queryKey: ["parentProgress", userId],
    queryFn: () => api.getParentProgress(userId!),
    enabled: !!userId,
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

  const stats = [
    { icon: BookOpen, label: "Lessons Completed", value: `${progress.lessons_completed}/${progress.total_lessons}`, bg: "bg-mint/40" },
    { icon: Zap, label: "Total XP", value: progress.xp_total, bg: "bg-lemon/40" },
    { icon: Flame, label: "Day Streak", value: progress.streak_days, bg: "bg-peach/40" },
    { icon: MessageCircle, label: "Conversations", value: progress.conversations_count, bg: "bg-lavender/40" },
    { icon: Languages, label: "Marathi Usage", value: `${Math.round(progress.avg_marathi_ratio * 100)}%`, bg: "bg-sky/40" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="container mx-auto max-w-2xl px-4 py-8 space-y-6">
        <div className="text-center mb-4">
          <div className="inline-flex items-center gap-2 bg-sky/30 text-foreground px-4 py-2 rounded-full text-sm font-display font-bold mb-3 animate-bounce-gentle">
            <Sparkles className="w-4 h-4 text-primary" />
            Parent Dashboard
          </div>
          <h1 className="font-display text-3xl md:text-4xl font-bold text-foreground">
            Your Children's Progress
          </h1>
          <p className="text-muted-foreground mt-2 font-display font-medium">
            Aggregated stats across all learners
          </p>
        </div>

        <Card className="gradient-card rounded-3xl border-2 border-border/50 fun-shadow animate-pop">
          <CardContent className="p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-[72px] w-[72px] rounded-2xl bg-sky/40 flex items-center justify-center">
                <Users className="h-10 w-10 text-primary animate-bounce-gentle" />
              </div>
              <div>
                <h2 className="font-display text-2xl font-bold text-foreground">Overview</h2>
                <p className="text-sm text-muted-foreground font-display font-bold">
                  All children combined
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-2 gap-4">
          {stats.map((stat, i) => (
            <Card
              key={stat.label}
              className={`gradient-card rounded-3xl border-2 border-border/50 hover:fun-shadow-hover hover:-translate-y-1 transition-all duration-300 animate-pop ${
                i === stats.length - 1 ? "col-span-2 sm:col-span-1" : ""
              }`}
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
      </div>
    </div>
  );
};

export default ParentProgress;
