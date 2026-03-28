import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import LessonCard from "@/components/LessonCard";
import LessonView from "@/components/LessonView";
import { BookOpen, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";
import type { Lesson } from "@/types";

const Lessons = () => {
  const { activeChild } = useAuth();
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [level, setLevel] = useState(activeChild?.current_level ?? 1);

  const { data: lessons, isLoading } = useQuery({
    queryKey: ["lessons", level],
    queryFn: () => api.listLessons(level),
  });

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {activeLesson ? (
        <LessonView lesson={activeLesson} onBack={() => setActiveLesson(null)} />
      ) : (
        <section className="container mx-auto px-4 py-10 md:py-16">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-mint/30 text-foreground px-4 py-2 rounded-full text-sm font-display font-bold mb-4 animate-bounce-gentle">
              <BookOpen className="w-4 h-4 text-primary" />
              Time to learn!
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-foreground">
              Pick Your Adventure!
            </h1>
            <p className="text-muted-foreground mt-3 max-w-md mx-auto text-lg">
              Choose a topic and start learning awesome Marathi words!
            </p>
          </div>

          {/* Level selector */}
          <div className="flex justify-center gap-2 mb-10">
            {[1, 2, 3, 4].map((l) => (
              <Button
                key={l}
                variant={level === l ? "default" : "outline"}
                size="sm"
                className="rounded-xl font-display font-bold"
                onClick={() => setLevel(l)}
              >
                Level {l}
              </Button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : lessons && lessons.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 max-w-4xl mx-auto">
              {lessons.map((lesson, i) => (
                <div key={lesson.id} className="animate-pop" style={{ animationDelay: `${i * 120}ms` }}>
                  <LessonCard
                    lesson={lesson}
                    index={i}
                    onSelect={() => setActiveLesson(lesson)}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground font-display font-bold py-20">
              No lessons available for this level yet.
            </p>
          )}
        </section>
      )}
    </div>
  );
};

export default Lessons;
