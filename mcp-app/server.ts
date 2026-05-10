/**
 * MCP App server — exposes MarathiMitra as interactive HTML UIs inside Claude.
 *
 * 3 primary tools (each opens an HTML app in Claude):
 *   - start-marathi-practice → conversation UI
 *   - browse-lessons → lesson browser UI
 *   - show-progress → progress dashboard UI
 *
 * 7 inner tools (called by apps via postMessage):
 *   - chat-send-message, chat-end, speak-marathi
 *   - list-lessons, get-lesson, complete-lesson, get-progress
 *
 * 3 resources serving bundled HTML from dist/apps/.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { z } from "zod";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { randomUUID } from "crypto";

import { MarathiApiClient } from "./api-client.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ── Config ───────────────────────────────────────────────────────────

const API_BASE_URL = process.env.MARATHI_API_URL || "http://localhost:8000";
const SERVICE_KEY = process.env.MARATHI_SERVICE_KEY || "";
const PORT = parseInt(process.env.PORT || process.env.MCP_APP_PORT || "3001", 10);

const api = new MarathiApiClient(API_BASE_URL, SERVICE_KEY);

// ── Helper: load bundled HTML ────────────────────────────────────────

function loadAppHtml(name: string): string {
  // Works whether running from source (tsx server.ts) or compiled (node dist/server.js)
  const fromSource = resolve(__dirname, "dist", "apps", `${name}.html`);
  const fromDist = resolve(__dirname, "apps", `${name}.html`);
  for (const p of [fromSource, fromDist]) {
    try {
      return readFileSync(p, "utf-8");
    } catch {
      continue;
    }
  }
  return `<html><body><p>App "${name}" not built yet. Run: npm run build:apps</p></body></html>`;
}

// ── MCP Server factory ───────────────────────────────────────────────
// Each session gets its own McpServer instance since McpServer only
// supports a single transport connection at a time.

function createServer(): McpServer {
const server = new McpServer({
  name: "MarathiMitra",
  version: "1.0.0",
});

// ── Resources: bundled HTML apps ─────────────────────────────────────

server.resource(
  "Conversation App",
  "ui://marathi-mitra/conversation",
  { mimeType: "text/html;profile=mcp-app" },
  async () => ({
    contents: [
      {
        uri: "ui://marathi-mitra/conversation",
        mimeType: "text/html;profile=mcp-app",
        text: loadAppHtml("conversation"),
      },
    ],
  })
);

server.resource(
  "Lessons App",
  "ui://marathi-mitra/lessons",
  { mimeType: "text/html;profile=mcp-app" },
  async () => ({
    contents: [
      {
        uri: "ui://marathi-mitra/lessons",
        mimeType: "text/html;profile=mcp-app",
        text: loadAppHtml("lessons"),
      },
    ],
  })
);

server.resource(
  "Progress App",
  "ui://marathi-mitra/progress",
  { mimeType: "text/html;profile=mcp-app" },
  async () => ({
    contents: [
      {
        uri: "ui://marathi-mitra/progress",
        mimeType: "text/html;profile=mcp-app",
        text: loadAppHtml("progress"),
      },
    ],
  })
);

// ── Primary tools (open HTML apps) ───────────────────────────────────

server.registerTool("start-marathi-practice", {
  title: "Practice Marathi",
  description:
    "Start a Marathi conversation with Mitra, the AI tutor. Opens an interactive chat UI.",
  inputSchema: {
    child_id: z.string().describe("The child's UUID"),
  },
  _meta: {
    ui: { resourceUri: "ui://marathi-mitra/conversation" },
  },
}, async ({ child_id }) => {
  try {
    const result = await api.startConversation(child_id);
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(result),
        },
      ],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("browse-lessons", {
  title: "Browse Lessons",
  description:
    "Browse Marathi vocabulary lessons by level. Opens a lesson browser with flashcards and quizzes.",
  inputSchema: {
    child_id: z.string().describe("The child's UUID"),
    level: z.number().min(1).max(5).optional().describe("Lesson level (1-5). Defaults to child's current level."),
  },
  _meta: {
    ui: { resourceUri: "ui://marathi-mitra/lessons" },
  },
}, async ({ child_id, level }) => {
  try {
    const targetLevel = level || 1;
    const lessons = await api.listLessons(targetLevel);
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({ child_id, level: targetLevel, lessons }),
        },
      ],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("show-progress", {
  title: "Show Progress",
  description:
    "Show a child's Marathi learning progress — XP, streak, level, lessons completed.",
  inputSchema: {
    child_id: z.string().describe("The child's UUID"),
  },
  _meta: {
    ui: { resourceUri: "ui://marathi-mitra/progress" },
  },
}, async ({ child_id }) => {
  try {
    const progress = await api.getProgress(child_id);
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(progress),
        },
      ],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

// ── Inner tools (called by apps via postMessage) ─────────────────────

server.registerTool("chat-send-message", {
  title: "Send Chat Message",
  description: "Send a message in an active Marathi conversation.",
  inputSchema: {
    conversation_id: z.string().describe("Active conversation UUID"),
    message: z.string().describe("The child's message"),
  },
}, async ({ conversation_id, message }) => {
  try {
    const result = await api.sendMessage(conversation_id, message);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(result) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("chat-end", {
  title: "End Chat",
  description: "End an active Marathi conversation and get XP summary.",
  inputSchema: {
    conversation_id: z.string().describe("Active conversation UUID"),
  },
}, async ({ conversation_id }) => {
  try {
    const result = await api.endConversation(conversation_id);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(result) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("speak-marathi", {
  title: "Speak Marathi",
  description: "Convert Marathi text to speech. Returns base64-encoded MP3 audio.",
  inputSchema: {
    text: z.string().max(200).describe("Marathi text to speak (max 200 chars)"),
  },
}, async ({ text }) => {
  try {
    const base64Audio = await api.speakMarathi(text);
    return {
      content: [{ type: "text" as const, text: JSON.stringify({ audio_base64: base64Audio }) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("list-lessons", {
  title: "List Lessons",
  description: "List Marathi lessons for a given level.",
  inputSchema: {
    level: z.number().min(1).max(5).describe("Lesson level (1-5)"),
  },
}, async ({ level }) => {
  try {
    const lessons = await api.listLessons(level);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(lessons) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("get-lesson", {
  title: "Get Lesson",
  description: "Get a specific lesson with vocabulary and quiz questions.",
  inputSchema: {
    lesson_id: z.string().describe("Lesson UUID"),
  },
}, async ({ lesson_id }) => {
  try {
    const lesson = await api.getLesson(lesson_id);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(lesson) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("complete-lesson", {
  title: "Complete Lesson",
  description: "Record lesson completion and award XP.",
  inputSchema: {
    lesson_id: z.string().describe("Lesson UUID"),
    child_id: z.string().describe("Child UUID"),
    score: z.number().min(0).max(100).describe("Quiz score (0-100)"),
  },
}, async ({ lesson_id, child_id, score }) => {
  try {
    const result = await api.completeLesson(lesson_id, child_id, score);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(result) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

server.registerTool("get-progress", {
  title: "Get Progress",
  description: "Get a child's learning progress stats.",
  inputSchema: {
    child_id: z.string().describe("Child UUID"),
  },
}, async ({ child_id }) => {
  try {
    const progress = await api.getProgress(child_id);
    return {
      content: [{ type: "text" as const, text: JSON.stringify(progress) }],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      content: [{ type: "text" as const, text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

return server;
}

// ── Transport ────────────────────────────────────────────────────────
// Use --stdio flag for Claude Desktop (stdio transport).
// Default: HTTP transport for remote access / claude.ai.

const useStdio = process.argv.includes("--stdio");

if (useStdio) {
  // Stdio mode — single session, launched by Claude Desktop
  const mcpServer = createServer();
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error(`MarathiMitra MCP App running (stdio). Backend: ${API_BASE_URL}`);
} else {
  // HTTP mode — multi-session, for remote access
  const expressApp = createMcpExpressApp({ host: "0.0.0.0" });

  const sessions = new Map<string, { transport: StreamableHTTPServerTransport; server: McpServer }>();

  expressApp.post("/mcp", async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;

    if (sessionId && sessions.has(sessionId)) {
      const { transport } = sessions.get(sessionId)!;
      await transport.handleRequest(req, res, req.body);
      return;
    }

    const mcpServer = createServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
    });

    transport.onclose = () => {
      const sid = (transport as unknown as { sessionId?: string }).sessionId;
      if (sid) sessions.delete(sid);
    };

    await mcpServer.connect(transport);
    await transport.handleRequest(req, res, req.body);

    const newSessionId = res.getHeader("mcp-session-id") as string | undefined;
    if (newSessionId) {
      sessions.set(newSessionId, { transport, server: mcpServer });
    }
  });

  expressApp.get("/mcp", async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    if (sessionId && sessions.has(sessionId)) {
      const { transport } = sessions.get(sessionId)!;
      await transport.handleRequest(req, res);
      return;
    }
    res.status(400).json({ error: "No session. Send POST to /mcp first." });
  });

  expressApp.delete("/mcp", async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    if (sessionId && sessions.has(sessionId)) {
      const { transport } = sessions.get(sessionId)!;
      await transport.handleRequest(req, res);
      sessions.delete(sessionId);
      return;
    }
    res.status(400).json({ error: "No session." });
  });

  expressApp.listen(PORT, () => {
    console.log(`MarathiMitra MCP App server running on http://localhost:${PORT}/mcp`);
    console.log(`Backend API: ${API_BASE_URL}`);
  });
}
