/**
 * API client that proxies to the FastAPI backend.
 *
 * Supports two auth modes:
 *   - { userToken }  → Authorization: Bearer <jwt>   (OAuth sessions)
 *   - { serviceKey } → X-Service-Key: <key>           (stdio / CI)
 */

import type {
  StartConversationResponse,
  SendMessageResponse,
  EndConversationResponse,
  Lesson,
  LessonCompleteResponse,
  ChildProgress,
} from "./types.js";

type AuthOptions =
  | { userToken: string; serviceKey?: never }
  | { serviceKey: string; userToken?: never };

export class MarathiApiClient {
  private baseUrl: string;
  private auth: AuthOptions;

  constructor(baseUrl: string, auth: AuthOptions) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.auth = auth;
  }

  private authHeaders(): Record<string, string> {
    if (this.auth.userToken) return { Authorization: `Bearer ${this.auth.userToken}` };
    return { "X-Service-Key": this.auth.serviceKey ?? "" };
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      ...this.authHeaders(),
      ...(options.headers as Record<string, string> | undefined),
    };

    if (options.body && typeof options.body === "string") {
      headers["Content-Type"] = "application/json";
    }

    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`API ${res.status}: ${detail}`);
    }

    const contentType = res.headers.get("content-type") ?? "";
    if (contentType.includes("audio/")) {
      const buffer = await res.arrayBuffer();
      return Buffer.from(buffer).toString("base64") as unknown as T;
    }

    return res.json() as Promise<T>;
  }

  // ── Conversations ──────────────────────────────────────────────────

  async startConversation(childId: string): Promise<StartConversationResponse> {
    return this.request<StartConversationResponse>("/conversations/start", {
      method: "POST",
      body: JSON.stringify({ child_id: childId }),
    });
  }

  async sendMessage(conversationId: string, message: string): Promise<SendMessageResponse> {
    return this.request<SendMessageResponse>(`/conversations/${conversationId}/message`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  }

  async endConversation(conversationId: string): Promise<EndConversationResponse> {
    return this.request<EndConversationResponse>(`/conversations/${conversationId}/end`, {
      method: "POST",
    });
  }

  // ── Lessons ────────────────────────────────────────────────────────

  async listLessons(level: number): Promise<Lesson[]> {
    return this.request<Lesson[]>(`/lessons/by-level/${level}`);
  }

  async getLesson(lessonId: string): Promise<Lesson> {
    return this.request<Lesson>(`/lessons/${lessonId}`);
  }

  async completeLesson(lessonId: string, childId: string, score: number): Promise<LessonCompleteResponse> {
    return this.request<LessonCompleteResponse>(`/lessons/${lessonId}/complete`, {
      method: "POST",
      body: JSON.stringify({ child_id: childId, score }),
    });
  }

  // ── Progress ───────────────────────────────────────────────────────

  async getProgress(childId: string): Promise<ChildProgress> {
    return this.request<ChildProgress>(`/progress/${childId}`);
  }

  // ── TTS ────────────────────────────────────────────────────────────

  async speakMarathi(text: string): Promise<string> {
    return this.request<string>("/tts/speak", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }
}
