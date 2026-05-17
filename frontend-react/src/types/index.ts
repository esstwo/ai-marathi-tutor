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
  refresh_token: string;
  children: Child[];
}

export interface SignupResponse {
  user_id: string;
  access_token?: string | null;
  refresh_token?: string | null;
  email_verification_required: boolean;
  message: string;
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
  icon: string;
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
  missions_completed: number;
}

// ── Missions ──────────────────────────────────────────────────────────

export interface MissionStep {
  step: number;
  prompt: string;
  target_vocab: string[];
}

export interface Mission {
  id: string;
  level: number;
  title: string;
  title_english: string;
  scenario: string;
  steps: MissionStep[];
  required_vocab: string[];
  xp_reward: number;
}

export interface MissionProgress {
  mission_id: string;
  status: "not_started" | "in_progress" | "completed";
  score: number;
  completed_at?: string;
  missions?: Mission;
}

export interface StartMissionResponse {
  conversation_id: string;
  marathi_text: string;
  english_hint?: string;
  mission_step: number;
  total_steps: number;
}

export interface SendMissionMessageResponse {
  marathi_text: string;
  english_hint?: string;
  mission_step: number;
  mission_complete: boolean;
  step_score: number;
  total_steps: number;
  xp_earned?: number;
  xp_total?: number;
  score?: number;
}

export interface EndMissionResponse {
  message: string;
  xp_earned: number;
}

export interface ParentProgress {
  lessons_completed: number;
  total_lessons: number;
  xp_total: number;
  streak_days: number;
  conversations_count: number;
  avg_marathi_ratio: number;
}
