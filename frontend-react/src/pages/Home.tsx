import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Flame, Zap, Trophy, BookOpen, MessageCircle, BarChart3, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";

const Home = () => {
  const { activeChild } = useAuth();
  const { data: progress } = useQuery({
    queryKey: ["progress", activeChild?.id],
    queryFn: () => api.getProgress(activeChild!.id),
    enabled: !!activeChild,
  });

  const stats = [
    { icon: Flame, label: "Day Streak", value: progress?.streak_days ?? 0, bg: "bg-peach/40" },
    { icon: Zap, label: "Total XP", value: progress?.xp_total ?? 0, bg: "bg-lemon/40" },
    { icon: Trophy, label: "Level", value: progress?.current_level ?? 1, bg: "bg-mint/40" },
    { icon: BookOpen, label: "Lessons", value: progress?.lessons_completed ?? 0, bg: "bg-lavender/40" },
  ];

  const quickActions = [
    { icon: BookOpen, label: "Start a Lesson", description: "Learn new Marathi words", path: "/lessons", bg: "bg-mint/30" },
    { icon: MessageCircle, label: "Chat with Mitra", description: "Practice with your AI buddy", path: "/chats", bg: "bg-lavender/30" },
    { icon: BarChart3, label: "View Progress", description: "See how far you've come", path: "/progress", bg: "bg-peach/30" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="container mx-auto max-w-2xl px-4 py-8 space-y-8">
        {/* Greeting */}
        <div className="text-center animate-pop">
          <p className="text-5xl mb-3 animate-bounce-gentle">{activeChild?.avatar}</p>
          <h1 className="font-display text-3xl md:text-4xl font-bold text-foreground">
            Hi {activeChild?.name}!
          </h1>
          <p className="text-muted-foreground mt-2 font-display font-medium">
            Ready to learn some Marathi today?
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          {stats.map((stat, i) => (
            <Card
              key={stat.label}
              className="gradient-card rounded-3xl border-2 border-border/50 hover:fun-shadow-hover hover:-translate-y-1 transition-all duration-300 animate-pop"
              style={{ animationDelay: `${i * 80}ms` }}
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

        {/* Quick actions */}
        <div className="space-y-3">
          <h2 className="font-display text-lg font-bold text-foreground flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            What would you like to do?
          </h2>
          {quickActions.map((action, i) => (
            <Link key={action.path} to={action.path}>
              <Card
                className="gradient-card rounded-2xl border-2 border-border/50 hover:fun-shadow-hover hover:-translate-y-1 transition-all duration-300 animate-pop cursor-pointer mb-3"
                style={{ animationDelay: `${(i + 4) * 80}ms` }}
              >
                <CardContent className="p-4 flex items-center gap-4">
                  <div className={`h-12 w-12 rounded-2xl ${action.bg} flex items-center justify-center shrink-0`}>
                    <action.icon className="h-6 w-6 text-foreground" />
                  </div>
                  <div className="flex-1">
                    <p className="font-display font-bold text-foreground">{action.label}</p>
                    <p className="text-sm text-muted-foreground">{action.description}</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;
