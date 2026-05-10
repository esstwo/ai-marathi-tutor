/**
 * API client that proxies to the FastAPI backend.
 * Uses X-Service-Key header for auth — no JWT, no login, no refresh.
 */

import type {
  StartConversationResponse,
  SendMessageResponse,
  EndConversationResponse,
  Lesson,
  LessonCompleteResponse,
  ChildProgress,
} from "./types.js";

export class MarathiApiClient {
  private baseUrl: string;
  private serviceKey: string;

  constructor(baseUrl: string, serviceKey: string) {
    // Strip trailing slash
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.serviceKey = serviceKey;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "X-Service-Key": this.serviceKey,
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

    // Handle binary responses (TTS audio)
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("audio/")) {
      const buffer = await res.arrayBuffer();
      return Buffer.from(buffer).toString("base64") as unknown as T;
    }

    return res.json() as Promise<T>;
  }

  // ── Conversations ──────────────────────────────────────────────────

  async startConversation(
    childId: string
  ): Promise<StartConversationResponse> {
    return this.request<StartConversationResponse>("/conversations/start", {
      method: "POST",
      body: JSON.stringify({ child_id: childId }),
    });
  }

  async sendMessage(
    conversationId: string,
    message: string
  ): Promise<SendMessageResponse> {
    return this.request<SendMessageResponse>(
      `/conversations/${conversationId}/message`,
      {
        method: "POST",
        body: JSON.stringify({ message }),
      }
    );
  }

  async endConversation(
    conversationId: string
  ): Promise<EndConversationResponse> {
    return this.request<EndConversationResponse>(
      `/conversations/${conversationId}/end`,
      { method: "POST" }
    );
  }

  // ── Lessons ────────────────────────────────────────────────────────

  async listLessons(level: number): Promise<Lesson[]> {
    return this.request<Lesson[]>(`/lessons/by-level/${level}`);
  }

  async getLesson(lessonId: string): Promise<Lesson> {
    return this.request<Lesson>(`/lessons/${lessonId}`);
  }

  async completeLesson(
    lessonId: string,
    childId: string,
    score: number
  ): Promise<LessonCompleteResponse> {
    return this.request<LessonCompleteResponse>(
      `/lessons/${lessonId}/complete`,
      {
        method: "POST",
        body: JSON.stringify({ child_id: childId, score }),
      }
    );
  }

  // ── Progress ───────────────────────────────────────────────────────

  async getProgress(childId: string): Promise<ChildProgress> {
    return this.request<ChildProgress>(`/progress/${childId}`);
  }

  // ── TTS ────────────────────────────────────────────────────────────

  async speakMarathi(text: string): Promise<string> {
    // Returns base64-encoded MP3 audio
    return this.request<string>("/tts/speak", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }
}
