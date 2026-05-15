/**
 * Conversation app — chat with Mitra inside MCP App iframe.
 *
 * States: loading → chatting → ended
 * Communicates with MCP server via postMessage / callServerTool.
 */

// ── Types ────────────────────────────────────────────────────────────

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  hint?: string;
}

interface StartData {
  conversation_id: string;
  marathi_text: string;
  english_hint?: string;
}

interface SendResult {
  marathi_text: string;
  english_hint?: string;
}

interface EndResult {
  xp_earned: number;
  xp_total: number;
  streak_days: number;
  duration_minutes: number;
}

// ── State ────────────────────────────────────────────────────────────

let conversationId: string | null = null;
let messages: Message[] = [];
let isTyping = false;
let chatEnded = false;
let ttsPlaying = false;

// ── Tool call helper ─────────────────────────────────────────────────

// In MCP App iframes, tools are called via postMessage to the host.
// We use a request/response pattern with unique IDs.
let callId = 0;
const pendingCalls = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

function callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const id = ++callId;
    pendingCalls.set(id, { resolve, reject });
    window.parent.postMessage(
      { type: "tool-call", id, tool: name, arguments: args },
      "*"
    );
    // Timeout after 30s
    setTimeout(() => {
      if (pendingCalls.has(id)) {
        pendingCalls.delete(id);
        reject(new Error("Tool call timed out"));
      }
    }, 30000);
  });
}

// Listen for tool results from the host
window.addEventListener("message", (event: MessageEvent) => {
  try {
    const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;

    // Tool call response
    if (data?.type === "tool-result" && data.id != null) {
      const pending = pendingCalls.get(data.id);
      if (pending) {
        pendingCalls.delete(data.id);
        if (data.error) {
          pending.reject(new Error(data.error));
        } else {
          const content = typeof data.content === "string" ? JSON.parse(data.content) : data.content;
          pending.resolve(content);
        }
      }
      return;
    }

    // Initial data from the primary tool result
    if (data && typeof data.conversation_id === "string") {
      handleStart(data as StartData);
      return;
    }
  } catch {
    // Ignore
  }
});

// ── Handlers ─────────────────────────────────────────────────────────

function handleStart(data: StartData): void {
  conversationId = data.conversation_id;
  messages = [
    {
      id: Date.now(),
      role: "assistant",
      content: data.marathi_text,
      hint: data.english_hint,
    },
  ];
  chatEnded = false;
  render();
}

async function handleSend(): Promise<void> {
  const input = document.getElementById("chat-input") as HTMLInputElement;
  const msg = input.value.trim();
  if (!msg || !conversationId || isTyping || chatEnded) return;

  // Add user message
  messages.push({ id: Date.now(), role: "user", content: msg });
  input.value = "";
  isTyping = true;
  render();
  scrollToBottom();

  try {
    const result = (await callTool("chat-send-message", {
      conversation_id: conversationId,
      message: msg,
    })) as SendResult;

    messages.push({
      id: Date.now() + 1,
      role: "assistant",
      content: result.marathi_text,
      hint: result.english_hint,
    });
  } catch (e) {
    messages.push({
      id: Date.now() + 1,
      role: "assistant",
      content: "Oops, something went wrong. Try again!",
    });
  }

  isTyping = false;
  render();
  scrollToBottom();
}

async function handleEnd(): Promise<void> {
  if (!conversationId || chatEnded) return;

  try {
    const result = (await callTool("chat-end", {
      conversation_id: conversationId,
    })) as EndResult;

    chatEnded = true;
    render();
    renderEndBanner(result);
  } catch {
    // Show error inline
  }
}

async function handleTTS(text: string, button: HTMLElement): Promise<void> {
  if (ttsPlaying) return;
  ttsPlaying = true;
  button.classList.add("playing");

  try {
    const result = (await callTool("speak-marathi", { text })) as { audio_base64: string };
    const audio = new Audio(`data:audio/mpeg;base64,${result.audio_base64}`);
    audio.onended = () => {
      ttsPlaying = false;
      button.classList.remove("playing");
    };
    audio.onerror = () => {
      ttsPlaying = false;
      button.classList.remove("playing");
    };
    await audio.play();
  } catch {
    ttsPlaying = false;
    button.classList.remove("playing");
  }
}

// ── Render ───────────────────────────────────────────────────────────

function scrollToBottom(): void {
  const feed = document.getElementById("chat-feed");
  if (feed) {
    requestAnimationFrame(() => {
      feed.scrollTop = feed.scrollHeight;
    });
  }
}

function render(): void {
  const app = document.getElementById("app")!;

  app.innerHTML = `
    <!-- Header -->
    <div class="flex items-center gap-12" style="padding:12px 0;border-bottom:1px solid var(--border-light)">
      <div style="width:44px;height:44px;border-radius:var(--radius-sm);background:var(--primary-light);display:flex;align-items:center;justify-content:center;font-size:1.5rem">
        \u{1F33A}
      </div>
      <div style="flex:1">
        <h3 style="margin:0">Marathi Mitra</h3>
        <div class="text-small text-muted">\u2728 Your Marathi learning buddy</div>
      </div>
      ${
        conversationId && !chatEnded
          ? '<button class="btn btn-danger btn-sm" id="end-btn">\u25A0 End Chat</button>'
          : ""
      }
    </div>

    <!-- Messages -->
    <div class="chat-feed" id="chat-feed">
      ${messages
        .map(
          (msg) => `
        <div class="chat-bubble ${msg.role === "assistant" ? "chat-bubble-mitra" : "chat-bubble-child"}">
          ${
            msg.role === "assistant"
              ? `
                <div class="flex items-center gap-8">
                  <div class="marathi-text" style="flex:1">${escapeHtml(msg.content)}</div>
                  <button class="tts-btn" data-tts="${escapeAttr(msg.content)}" title="Listen">\u{1F50A}</button>
                </div>
                ${msg.hint ? `<div class="english-hint">${escapeHtml(msg.hint)}</div>` : ""}
              `
              : escapeHtml(msg.content)
          }
        </div>
      `
        )
        .join("")}
      ${
        isTyping
          ? `
        <div class="chat-bubble chat-bubble-mitra">
          <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
      `
          : ""
      }
    </div>

    <!-- Input -->
    ${
      chatEnded
        ? '<div id="end-banner"></div>'
        : `
      <div class="chat-input-bar">
        <input
          type="text"
          id="chat-input"
          class="input"
          placeholder="Type something fun..."
          ${!conversationId || isTyping ? "disabled" : ""}
          autocomplete="off"
        />
        <button
          class="btn btn-primary btn-icon"
          id="send-btn"
          ${!conversationId || isTyping ? "disabled" : ""}
          title="Send"
        >\u{27A4}</button>
      </div>
    `
    }
  `;

  // Bind events
  const endBtn = document.getElementById("end-btn");
  endBtn?.addEventListener("click", handleEnd);

  const sendBtn = document.getElementById("send-btn");
  sendBtn?.addEventListener("click", handleSend);

  const chatInput = document.getElementById("chat-input") as HTMLInputElement | null;
  chatInput?.addEventListener("keydown", (e: KeyboardEvent) => {
    if (e.key === "Enter") handleSend();
  });
  chatInput?.focus();

  // TTS buttons
  document.querySelectorAll<HTMLElement>("[data-tts]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-tts");
      if (text) handleTTS(text, btn);
    });
  });
}

function renderEndBanner(result: EndResult): void {
  const banner = document.getElementById("end-banner");
  if (!banner) return;

  banner.innerHTML = `
    <div class="chat-ended-banner">
      <div style="font-size:2rem;margin-bottom:8px">\u{1F389}</div>
      <div class="xp-earned">+${result.xp_earned} XP</div>
      <div class="text-muted" style="margin-top:4px">
        ${result.duration_minutes} min chat \u2022 ${result.streak_days} day streak
      </div>
      <div style="margin-top:4px;font-weight:600;color:var(--primary)">
        Total: ${result.xp_total} XP
      </div>
    </div>
  `;
}

// ── Utilities ────────────────────────────────────────────────────────

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function escapeAttr(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ── Init ─────────────────────────────────────────────────────────────

function init(): void {
  // Listen for initial data
  window.addEventListener("message", (event: MessageEvent) => {
    try {
      const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      if (data && typeof data.conversation_id === "string" && !conversationId) {
        handleStart(data as StartData);
      }
    } catch {
      // Ignore
    }
  });

  // Check URL hash for embedded data
  if (window.location.hash) {
    try {
      const data = JSON.parse(decodeURIComponent(window.location.hash.slice(1)));
      if (data.conversation_id) {
        handleStart(data as StartData);
        return;
      }
    } catch {
      // Ignore
    }
  }

  // Signal ready
  window.parent?.postMessage({ type: "ready", app: "conversation" }, "*");
}

init();
