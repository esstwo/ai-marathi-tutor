import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Lesson } from "@/types";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  ArrowLeft, ArrowRight, Check, X, Star, ThumbsUp, Dumbbell,
  Target, Sparkles, Rocket, BookOpen, Zap, Volume2,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import * as api from "@/services/api";

interface LessonViewProps {
  lesson: Lesson;
  onBack: () => void;
}

type Phase = "words" | "quiz" | "results";

const ConfettiBurst = () => (
  <div className="absolute inset-0 pointer-events-none overflow-hidden">
    {Array.from({ length: 12 }).map((_, i) => (
      <div
        key={i}
        className="absolute animate-confetti-fall"
        style={{
          left: `${10 + Math.random() * 80}%`,
          top: "-10px",
          animationDelay: `${Math.random() * 0.5}s`,
          animationDuration: `${1 + Math.random() * 0.5}s`,
        }}
      >
        <div
          className="w-3 h-3 rounded-sm"
          style={{
            backgroundColor: [
              "hsl(var(--peach))", "hsl(var(--mint))", "hsl(var(--lavender))",
              "hsl(var(--sky))", "hsl(var(--lemon))", "hsl(var(--coral))",
            ][i % 6],
          }}
        />
      </div>
    ))}
  </div>
);

const speakMarathi = async (text: string) => {
  try {
    const blob = await api.speakMarathiTTS(text);
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => URL.revokeObjectURL(url);
    audio.play();
  } catch {
    console.warn("TTS backend unavailable, falling back to browser speech");
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "hi-IN";
    utterance.rate = 0.85;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }
};

const LessonView = ({ lesson, onBack }: LessonViewProps) => {
  const { activeChild } = useAuth();
  const queryClient = useQueryClient();

  const [phase, setPhase] = useState<Phase>("words");
  const [wordIndex, setWordIndex] = useState(0);
  const [quizIndex, setQuizIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [showCorrectAnim, setShowCorrectAnim] = useState(false);
  const [xpEarned, setXpEarned] = useState<number | null>(null);

  const completeMutation = useMutation({
    mutationFn: () =>
      api.completeLesson(lesson.id, activeChild!.id, score),
    onSuccess: (data) => {
      setXpEarned(data.xp_earned);
      queryClient.invalidateQueries({ queryKey: ["progress", activeChild?.id] });
    },
  });

  const words = lesson.vocabulary;
  const questions = lesson.quiz_questions;
  const totalSteps = words.length + questions.length;
  const currentStep =
    phase === "words"
      ? wordIndex + 1
      : phase === "quiz"
        ? words.length + quizIndex + 1
        : totalSteps;

  const progressValue = (currentStep / totalSteps) * 100;

  const handleNextWord = () => {
    if (wordIndex < words.length - 1) {
      setWordIndex((i) => i + 1);
    } else {
      setPhase("quiz");
    }
  };

  const handlePrevWord = () => {
    if (wordIndex > 0) setWordIndex((i) => i - 1);
  };

  const handleAnswer = (index: number) => {
    if (answered) return;
    setSelectedAnswer(index);
    setAnswered(true);
    const newScore = index === questions[quizIndex].correct_index ? score + 1 : score;
    if (index === questions[quizIndex].correct_index) {
      setScore(newScore);
      setShowCorrectAnim(true);
      setTimeout(() => setShowCorrectAnim(false), 800);
    }
  };

  const handleNextQuiz = () => {
    if (quizIndex < questions.length - 1) {
      setQuizIndex((i) => i + 1);
      setSelectedAnswer(null);
      setAnswered(false);
    } else {
      setPhase("results");
      completeMutation.mutate();
    }
  };

  const word = words[wordIndex];
  const question = questions[quizIndex];

  const isPerfect = score === questions.length;
  const isGood = score >= questions.length / 2;
  const ResultIcon = isPerfect ? Star : isGood ? ThumbsUp : Dumbbell;

  return (
    <div className="container mx-auto px-4 py-8 max-w-xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={onBack} className="shrink-0 rounded-xl">
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary" />
          <h2 className="font-display text-lg font-bold text-foreground">
            {lesson.title}
          </h2>
        </div>
        <span className="text-sm font-display font-bold text-primary bg-primary/10 px-3 py-1 rounded-full">
          {currentStep}/{totalSteps}
        </span>
      </div>

      <Progress value={progressValue} className="h-3 mb-8 rounded-full" />

      {/* Word Phase */}
      {phase === "words" && (
        <div className="animate-pop" key={`word-${wordIndex}`}>
          <div className="bg-mint/20 rounded-4xl p-10 text-center mb-8 relative overflow-hidden">
            <div className="absolute top-3 right-3 opacity-10">
              <Sparkles className="w-20 h-20 text-primary" />
            </div>
            <div className="flex justify-center mb-5">
              <div className="w-20 h-20 rounded-2xl bg-card/60 flex items-center justify-center fun-shadow">
                <BookOpen className="w-12 h-12 text-primary" />
              </div>
            </div>
            <div className="flex items-center justify-center gap-3 mb-3">
              <p className="font-display text-5xl md:text-6xl font-bold text-foreground">
                {word.marathi}
              </p>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full h-10 w-10 hover:bg-primary/10"
                onClick={() => speakMarathi(word.marathi)}
              >
                <Volume2 className="w-6 h-6 text-primary" />
              </Button>
            </div>
            <p className="text-muted-foreground text-lg italic mb-2">
              {word.pronunciation}
            </p>
            <p className="font-display text-2xl font-bold text-primary">
              {word.english}
            </p>
          </div>

          <div className="flex justify-between gap-3">
            <Button
              variant="outline"
              onClick={handlePrevWord}
              disabled={wordIndex === 0}
              className="rounded-2xl h-12 text-base font-bold px-6"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Back
            </Button>
            <Button variant="hero" onClick={handleNextWord} className="rounded-2xl h-12 text-base font-bold px-6 fun-shadow">
              {wordIndex === words.length - 1 ? (
                <>Quiz Time! <Target className="w-5 h-5 ml-1" /></>
              ) : (
                <>Next Word <ArrowRight className="w-4 h-4 ml-1" /></>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Quiz Phase */}
      {phase === "quiz" && (
        <div className="animate-pop relative" key={`quiz-${quizIndex}`}>
          {showCorrectAnim && <ConfettiBurst />}
          <div className="text-center mb-8">
            <span className="inline-flex items-center gap-2 bg-primary/10 text-primary text-sm font-bold px-4 py-2 rounded-full mb-4">
              <Target className="w-4 h-4" /> Quiz Time!
            </span>
            <p className="font-display text-2xl md:text-3xl font-bold text-foreground">
              {question.question}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 mb-8">
            {question.options.map((option, i) => {
              let variant: "outline" | "default" | "destructive" = "outline";
              let icon = null;
              let extraClass = "rounded-2xl h-14 text-base font-bold border-2";

              if (answered) {
                if (i === question.correct_index) {
                  variant = "default";
                  icon = <Check className="w-5 h-5" />;
                  extraClass += " animate-tada";
                } else if (i === selectedAnswer) {
                  variant = "destructive";
                  icon = <X className="w-5 h-5" />;
                }
              } else {
                extraClass += " hover:-translate-y-0.5 hover:fun-shadow transition-all";
              }

              return (
                <Button
                  key={i}
                  variant={variant}
                  className={`${extraClass} justify-start gap-3`}
                  onClick={() => handleAnswer(i)}
                >
                  <span className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center text-sm font-bold shrink-0">
                    {String.fromCharCode(65 + i)}
                  </span>
                  {icon}
                  {option}
                </Button>
              );
            })}
          </div>

          {answered && (
            <div className="text-center animate-pop">
              <p className="text-sm font-display font-bold mb-3 text-muted-foreground">
                {selectedAnswer === question.correct_index
                  ? "Awesome! You got it right!"
                  : "Oops! The right answer is highlighted above."}
              </p>
              <Button variant="hero" onClick={handleNextQuiz} className="rounded-2xl h-12 text-base font-bold px-8 fun-shadow">
                {quizIndex === questions.length - 1 ? (
                  <>See My Score <Star className="w-5 h-5 ml-1" /></>
                ) : (
                  <>Next Question <ArrowRight className="w-4 h-4 ml-1" /></>
                )}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Results Phase */}
      {phase === "results" && (
        <div className="animate-pop text-center relative">
          {isPerfect && <ConfettiBurst />}
          <div className="bg-muted/40 rounded-4xl p-10 mb-8 relative overflow-hidden">
            <div className="flex justify-center mb-5">
              <div className={`w-20 h-20 rounded-3xl flex items-center justify-center ${isPerfect ? "bg-lemon/50" : isGood ? "bg-mint/50" : "bg-peach/50"}`}>
                <ResultIcon className="w-12 h-12 text-primary animate-tada" />
              </div>
            </div>
            <p className="font-display text-4xl md:text-5xl font-bold text-foreground mb-2">
              {score}/{questions.length}
            </p>
            <p className="font-display text-lg font-bold text-primary mb-1">
              {isPerfect ? "PERFECT SCORE!" : isGood ? "Great Job!" : "Keep Trying!"}
            </p>
            <p className="text-muted-foreground">
              {isPerfect
                ? "You're a Marathi superstar!"
                : isGood
                  ? "You're doing amazing! Keep it up!"
                  : "Practice makes perfect! Try again!"}
            </p>
            {xpEarned != null && (
              <div className="mt-4 inline-flex items-center gap-2 bg-lemon/40 px-4 py-2 rounded-full font-display font-bold text-foreground">
                <Zap className="w-4 h-4 text-primary" />
                +{xpEarned} XP earned!
              </div>
            )}
          </div>
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={onBack} className="rounded-2xl h-12 text-base font-bold px-6">
              All Lessons
            </Button>
            <Button
              variant="hero"
              className="rounded-2xl h-12 text-base font-bold px-6 fun-shadow"
              onClick={() => {
                setPhase("words");
                setWordIndex(0);
                setQuizIndex(0);
                setScore(0);
                setSelectedAnswer(null);
                setAnswered(false);
                setXpEarned(null);
              }}
            >
              <Rocket className="w-5 h-5 mr-1" />
              Try Again
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LessonView;
