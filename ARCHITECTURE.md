# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                   │
│                  React + TypeScript + Vite                           │
│                                                                     │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Pages    │  │  Auth     │  │  API     │  │  Components      │  │
│  │  (7 views)│  │  Context  │  │  Client  │  │  (shadcn/ui)     │  │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  └──────────────────┘  │
│        │              │              │                               │
│        └──────────────┴──────┬───────┘                               │
│                              │  Axios + Bearer token                 │
│                              │  401 → auto refresh → retry           │
└──────────────────────────────┼───────────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────┼───────────────────────────────────────┐
│                         BACKEND (FastAPI)                            │
│                              │                                       │
│  ┌───────────────────────────▼──────────────────────────────────┐   │
│  │                      Routers (Gateway)                       │   │
│  │  auth.py │ lessons.py │ conversations.py │ progress.py │ tts │   │
│  │                                                              │   │
│  │  Thin HTTP layer — validates auth, delegates to services     │   │
│  └──────┬────────────────────┬──────────────────────────────────┘   │
│         │                    │                                       │
│         │              ┌─────▼──────────────────────────────────┐   │
│         │              │         Skills Layer                    │   │
│         │              │    mitra_conversation.py                │   │
│         │              │                                        │   │
│         │              │  ┌──────────────────────────────────┐  │   │
│         │              │  │      Agentic Tool-Calling Loop   │  │   │
│         │              │  │                                  │  │   │
│         │              │  │  1. Send prompt + tool defs      │  │   │
│         │              │  │  2. LLM requests tool calls      │  │   │
│         │              │  │  3. Execute tools via MCP        │  │   │
│         │              │  │  4. Feed results back to LLM     │  │   │
│         │              │  │  5. LLM returns JSON response    │  │   │
│         │              │  └──────────────┬───────────────────┘  │   │
│         │              └────────────────┬┘                      │   │
│         │                               │                       │   │
│  ┌──────▼───────────────────────────────▼──────────────────────┐   │
│  │                     MCP Client (client.py)                   │   │
│  │              Async in-process tool invocation                │   │
│  └──────┬───────────────────────────────┬──────────────────────┘   │
│         │                               │                          │
│  ┌──────▼──────────────┐  ┌─────────────▼────────────────────┐    │
│  │  supabase-mcp       │  │  tts-mcp                         │    │
│  │  FastMCP Server     │  │  FastMCP Server                  │    │
│  │  (19 tools)         │  │  (1 tool)                        │    │
│  │                     │  │                                  │    │
│  │  get_child_profile  │  │  speak_marathi                   │    │
│  │  get_lesson_context │  │                                  │    │
│  │  save_message       │  └──────────────┬───────────────────┘    │
│  │  create_conversation│                 │                         │
│  │  update_xp          │                 │                         │
│  │  ... (14 more)      │                 │                         │
│  └──────┬──────────────┘                 │                         │
│         │                                │                         │
└─────────┼────────────────────────────────┼─────────────────────────┘
          │                                │
          ▼                                ▼
┌──────────────────┐            ┌─────────────────────┐
│    Supabase      │            │  Google Cloud TTS    │
│  (PostgreSQL +   │            │  (Marathi speech)    │
│   Auth)          │            │                      │
└──────────────────┘            └─────────────────────┘

          ▲
          │ Tool calls via Groq API
          │
┌─────────┴────────┐
│   Groq Cloud     │
│  Llama 3.3 70B   │
│  (LLM engine)    │
└──────────────────┘
```

## Request Flow: AI Conversation

```
User sends message
       │
       ▼
┌─────────────────┐
│  POST /conver-   │
│  sations/{id}/   │
│  message         │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐     ┌──────────────────┐
│  conversations  │────▶│  verify auth +   │
│  router         │     │  child ownership │
└───────┬─────────┘     └──────────────────┘
        │
        ▼
┌─────────────────┐
│  save_message   │──── MCP call ──▶ supabase-mcp
│  (child's msg)  │
└───────┬─────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  mitra_conversation.chat()               │
│                                          │
│  Build messages:                         │
│    [system prompt, history, user msg]    │
│                                          │
│  call_llm(messages, tools=MITRA_TOOLS)   │
│         │                                │
│         ▼                                │
│  ┌─── Agentic Loop (max 3 rounds) ───┐  │
│  │                                    │  │
│  │  Groq API ◀──────────────────────┐ │  │
│  │    │                             │ │  │
│  │    ▼                             │ │  │
│  │  tool_calls?                     │ │  │
│  │    │ yes          │ no           │ │  │
│  │    ▼              ▼              │ │  │
│  │  Execute via    Return JSON      │ │  │
│  │  MCP client     response         │ │  │
│  │    │                             │ │  │
│  │    ▼                             │ │  │
│  │  Append tool                     │ │  │
│  │  results to ─────────────────────┘ │  │
│  │  messages                          │  │
│  └────────────────────────────────────┘  │
│                                          │
│  parse_json_response(raw_text)           │
│    → {marathi_text, english_hint}        │
└───────┬──────────────────────────────────┘
        │
        ▼
┌─────────────────┐
│  save_message   │──── MCP call ──▶ supabase-mcp
│  (Mitra's reply)│
└───────┬─────────┘
        │
        ▼
  Return to client:
  {marathi_text, english_hint, audio_url}
```

## Layer Responsibilities

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **Gateway** | `backend/routers/` | HTTP endpoints, auth validation, request/response shaping. No business logic. |
| **Skills** | `backend/skills/` | LLM orchestration — prompt construction, agentic tool-calling loop, response parsing. |
| **Services** | `backend/services/` | Business logic (XP calculation, TTS caching). Bridges routers and MCP. |
| **MCP Servers** | `backend/mcp/` | Standardized tool interface. All DB and TTS operations exposed as MCP tools. |
| **Prompts** | `backend/prompts/` | System prompt definitions. Personality, safety rules, response format. |

## Key Design Decisions

**LLM-as-Orchestrator**: The LLM receives tool definitions and decides what context it needs. The gateway doesn't hardcode "fetch profile, then fetch lesson, then call LLM." Instead, the LLM calls `get_child_profile` and `get_lesson_context` itself via the agentic loop. This makes the system more flexible — the LLM can skip tools it doesn't need or call them in any order.

**MCP for Tool Interface**: All database operations are registered as MCP tools via FastMCP. Currently called in-process, but the same tools can be deployed as standalone services with SSE/HTTP transport, or called by external MCP clients (Claude Desktop, other LLM apps).

**Data-fetching vs Persistence Split**: The LLM can only call read-only tools (`get_child_profile`, `get_lesson_context`). Write operations (`save_message`, `update_xp`) are called by the gateway — the LLM should never decide when to persist data.

**Structured JSON Output**: The LLM returns `{"marathi_text": "...", "english_hint": "..."}` instead of a free-text format parsed with regex. Falls back gracefully if the LLM returns plain text.

**Token Refresh**: The frontend's Axios interceptor catches 401s, refreshes the JWT via `/auth/refresh`, and retries the original request. Concurrent requests queue behind the refresh.

## Database Schema (Supabase)

```
parents ──────< children ──────< conversations ──────< messages
                   │
                   ├──────< lesson_completions >────── lessons
                   │                                      │
                   │                                      ├──< vocabulary
                   │                                      └──< quiz_questions
                   │
                   └──────< child_progress (view)
```

Core tables: `parents`, `children`, `lessons`, `vocabulary`, `quiz_questions`, `lesson_completions`, `conversations`, `messages`. Row-level security ensures parents only access their own children's data.
