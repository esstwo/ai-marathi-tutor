import axios from "axios";
import type {
  LoginResponse,
  SignupResponse,
  Child,
  Lesson,
  LessonCompleteResponse,
  StartConversationResponse,
  SendMessageResponse,
  EndConversationResponse,
  ChildProgress,
  ParentProgress,
} from "@/types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function signup(
  name: string,
  email: string,
  password: string
): Promise<SignupResponse> {
  const { data } = await api.post("/auth/signup", { name, email, password });
  return data;
}

export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function createChild(
  name: string,
  age: number,
  avatar: string
): Promise<Child> {
  const { data } = await api.post("/auth/children", { name, age, avatar });
  return data;
}

export async function listLessons(level: number): Promise<Lesson[]> {
  const { data } = await api.get(`/lessons/by-level/${level}`);
  return data;
}

export async function getLesson(lessonId: string): Promise<Lesson> {
  const { data } = await api.get(`/lessons/${lessonId}`);
  return data;
}

export async function completeLesson(
  lessonId: string,
  childId: string,
  score: number
): Promise<LessonCompleteResponse> {
  const { data } = await api.post(`/lessons/${lessonId}/complete`, {
    child_id: childId,
    score,
  });
  return data;
}

export async function startConversation(
  childId: string
): Promise<StartConversationResponse> {
  const { data } = await api.post("/conversations/start", {
    child_id: childId,
  });
  return data;
}

export async function sendMessage(
  conversationId: string,
  message: string
): Promise<SendMessageResponse> {
  const { data } = await api.post(
    `/conversations/${conversationId}/message`,
    { message }
  );
  return data;
}

export async function endConversation(
  conversationId: string
): Promise<EndConversationResponse> {
  const { data } = await api.post(`/conversations/${conversationId}/end`);
  return data;
}

export async function getProgress(
  childId: string
): Promise<ChildProgress> {
  const { data } = await api.get(`/progress/${childId}`);
  return data;
}

export async function getParentProgress(
  parentId: string
): Promise<ParentProgress> {
  const { data } = await api.get(`/parents/${parentId}/progress`);
  return data;
}
