export interface Child {
  id: string;
  name: string;
  age: number;
  avatar: string;
  current_level: number;
}

export interface LoginResponse {
  user_id: string;
  access_token: string;
  children: Child[];
}

export interface SignupResponse {
  user_id: string;
  access_token: string;
}

export interface VocabWord {
  marathi: string;
  english: string;
  pronunciation: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
}

export interface Lesson {
  id: string;
  level: number;
  sequence: number;
  title: string;
  theme: string;
  vocabulary: VocabWord[];
  quiz_questions: QuizQuestion[];
}

export interface LessonCompleteResponse {
  score: number;
  xp_earned: number;
  xp_total: number;
  streak_days: number;
}

export interface StartConversationResponse {
  conversation_id: string;
  marathi_text: string;
  english_hint?: string;
}

export interface SendMessageResponse {
  marathi_text: string;
  english_hint?: string;
}

export interface EndConversationResponse {
  xp_earned: number;
  xp_total: number;
  streak_days: number;
  duration_minutes: number;
}

export interface ChildProgress {
  xp_total: number;
  streak_days: number;
  current_level: number;
  lessons_completed: number;
  conversations_count: number;
}

export interface ParentProgress {
  lessons_completed: number;
  total_lessons: number;
  xp_total: number;
  streak_days: number;
  conversations_count: number;
  avg_marathi_ratio: number;
}
