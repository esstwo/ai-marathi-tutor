import type { Lesson } from "@/types";
import { BookOpen, Users, UtensilsCrossed, Hash, Palette, Music } from "lucide-react";
import { Sparkles } from "lucide-react";

const LESSON_STYLES = [
  { icon: BookOpen, color: "peach" },
  { icon: Users, color: "mint" },
  { icon: UtensilsCrossed, color: "lavender" },
  { icon: Hash, color: "sky" },
  { icon: Palette, color: "lemon" },
  { icon: Music, color: "coral" },
];

interface LessonCardProps {
  lesson: Lesson;
  index: number;
  onSelect: () => void;
}

const LessonCard = ({ lesson, index, onSelect }: LessonCardProps) => {
  const style = LESSON_STYLES[index % LESSON_STYLES.length];
  const Icon = style.icon;

  return (
    <button
      onClick={onSelect}
      className="group relative rounded-3xl border-2 border-border/50 bg-card p-8 text-left transition-all duration-300 hover:fun-shadow-hover hover:-translate-y-2 hover:border-primary/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div
        className={`bg-${style.color}/30 w-[72px] h-[72px] rounded-2xl flex items-center justify-center mb-5 group-hover:animate-wiggle transition-transform`}
      >
        <Icon className="w-9 h-9 text-foreground" />
      </div>
      <h3 className="font-display text-xl font-bold text-foreground mb-1">
        {lesson.title}
      </h3>
      <p className="font-display text-sm text-muted-foreground mb-1">
        {lesson.theme}
      </p>
      <p className="text-muted-foreground text-sm leading-relaxed mb-5">
        {lesson.vocabulary.length} words to learn
      </p>
      <span className="inline-flex items-center gap-2 text-sm font-bold text-primary group-hover:gap-3 transition-all bg-primary/10 px-4 py-2 rounded-full">
        <Sparkles className="w-4 h-4" />
        Let's Learn!
      </span>
    </button>
  );
};

export default LessonCard;
