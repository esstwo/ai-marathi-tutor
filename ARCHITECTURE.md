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
│  │                   Gateway (gateway/api.py)                   │   │
│  │                                                              │   │
│  │  Thin HTTP layer — validates auth, maps requests to skills   │   │
│  │  and connectors. CRUD calls connectors directly.             │   │
│  │  Conversations use run_skill() for LLM orchestration.        │   │
│  │                                                              │   │
│  │  ┌─────────────── Guardrails (guardrails.py) ─────────────┐ │   │
│  │  │ Input:  max length, profanity filter, injection detect │ │   │
│  │  │ Output: JSON validation, PII/URL strip, safe fallback  │ │   │
│  │  │ Session: msg cap (50), time cap (30m), concurrency (3) │ │   │
│  │  │ Cost:   daily LLM call limit, usage tracking           │ │   │
│  │  └────────────────────────────────────────────────────────┘ │   │
│  └──────┬────────────────────┬──────────────────────────────────┘   │
│         │                    │                                       │
│         │              ┌─────▼──────────────────────────────────┐   │
│         │              │         Core (core/llm.py)             │   │
│         │              │     Generic Agentic Loop               │   │
│         │              │                                        │   │
│         │              │  run_skill(skill, messages, connectors) │   │
│         │              │                                        │   │
│         │              │  1. Load skill's system prompt (.md)   │   │
│         │              │  2. Auto-generate tool schemas from    │   │
│         │              │     connector function signatures      │   │
│         │              │  3. Send to LLM with tool definitions  │   │
│         │              │  4. LLM requests tool calls            │   │
│         │              │  5. Execute against connectors          │   │
│         │              │  6. Feed results back, loop             │   │
│         │              │  7. Parse JSON response                │   │
│         │              └──────────────┬─────────────────────────┘   │
│         │                             │                              │
│  ┌──────▼─────────────────────────────▼────────────────────────┐    │
│  │                  Connectors (connectors/)                    │    │
│  │           Direct function calls to external systems          │    │
│  │                                                              │    │
│  │  supabase/          tts/                                     │    │
│  │    auth.py            google_tts.py                          │    │
│  │    children.py          speak_marathi()                      │    │
│  │    conversations.py                                          │    │
│  │    lessons.py                                                │    │
│  │    progress.py                                               │    │
│  └──────┬──────────────────────────────┬───────────────────────┘    │
│         │                              │                             │
│  ┌──────▼──────────┐   ┌──────────────▼──────────────┐              │
│  │  Skill Files    │   │  Connector Registry          │              │
│  │  (skills/*.md)  │   │  (core/connector_registry.py)│              │
│  │                 │   │                              │              │
│  │  conversation   │   │  Auto-discovers all          │              │
│  │  lessons        │   │  connector functions,        │              │
│  │  progress       │   │  maps names → callables      │              │
│  └─────────────────┘   └─────────────────────────────┘              │
│                                                                      │
└─────────┬────────────────────────────────┬───────────────────────────┘
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


                    ┌──────────────────────────────────┐
                    │     MCP Server (mcp_server.py)    │
                    │                                    │
                    │  Same connectors exposed as MCP    │
                    │  tools. Skills exposed as MCP      │
                    │  resources and prompts.             │
                    │                                    │
                    │  Claude Desktop connects via       │
                    │  stdio transport.                   │
                    └──────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │    MCP App (mcp-app/server.ts)    │
                    │                                    │
                    │  Interactive HTML UIs inside       │
                    │  Claude Desktop / claude.ai.       │
                    │  3 apps: conversation, lessons,    │
                    │  progress. Proxies to FastAPI      │
                    │  via service key auth.              │
                    │                                    │
                    │  stdio (Desktop) or HTTP (remote)  │
                    └──────────────────────────────────┘
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
│  gateway/api.py │────▶│  verify auth +   │
│                 │     │  child ownership │
└───────┬─────────┘     └──────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Guardrails (input)                      │
│  ✓ message length ≤ 500                  │
│  ✓ no profanity / inappropriate content  │
│  ✓ no prompt injection patterns          │
│  ✓ session: msg count < 50, time < 30m   │
│  ✓ cost: daily LLM calls within limit    │
└───────┬──────────────────────────────────┘
        │
        ▼
┌─────────────────┐
│  save_message   │──── connector call ──▶ supabase
│  (child's msg)  │
└───────┬─────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  run_skill(conversation_skill, ...)      │
│                                          │
│  1. Load system prompt from              │
│     skills/conversation.md               │
│                                          │
│  2. Build messages:                      │
│     [system prompt, history, user msg]   │
│                                          │
│  3. Auto-generate tool schemas from      │
│     connector functions                  │
│                                          │
│  4. Agentic loop (max 3 rounds):         │
│         │                                │
│  ┌─── Loop ──────────────────────────┐   │
│  │                                    │   │
│  │  Groq API ◀──────────────────────┐│   │
│  │    │                             ││   │
│  │    ▼                             ││   │
│  │  tool_calls?                     ││   │
│  │    │ yes          │ no           ││   │
│  │    ▼              ▼              ││   │
│  │  Execute via    Return JSON      ││   │
│  │  connectors     response         ││   │
│  │    │                             ││   │
│  │    ▼                             ││   │
│  │  Append tool                     ││   │
│  │  results to ─────────────────────┘│   │
│  │  messages                         │   │
│  └───────────────────────────────────┘   │
│                                          │
│  parse_json_response(raw_text)           │
│    → {marathi_text, english_hint}        │
└───────┬──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Guardrails (output)                     │
│  ✓ marathi_text exists (else fallback)   │
│  ✓ strip URLs, emails, phone numbers     │
│  ✓ no profanity (else safe fallback)     │
│  ✓ flag conversation if sanitized        │
└───────┬──────────────────────────────────┘
        │
        ▼
┌─────────────────┐
│  save_message   │──── connector call ──▶ supabase
│  (Mitra's reply)│
└───────┬─────────┘
        │
        ▼
  Return to client:
  {marathi_text, english_hint}
```

## Layer Responsibilities

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **Gateway** | `backend/gateway/` | HTTP endpoints, auth validation, request/response mapping. CRUD calls connectors directly. Conversations use `run_skill()`. |
| **Guardrails** | `backend/gateway/guardrails.py` | Child safety: input validation (length, profanity, prompt injection), output sanitization (PII/URL stripping, JSON validation), session limits (message/time/concurrency caps), cost protection (daily LLM call limit). |
| **Core** | `backend/core/` | Generic infrastructure: skill loader, connector registry, agentic tool-calling loop. Not MarathiMitra-specific. |
| **Skills** | `backend/skills/` | Portable Markdown files — system prompts with YAML frontmatter declaring inputs, outputs, and connector dependencies. The product's intelligence. |
| **Connectors** | `backend/connectors/` | Minimal glue code — plain Python functions that call external systems. No business logic. |
| **Services** | `backend/services/` | Shared utilities (Google Cloud TTS wrapper with caching). |
| **Tests** | `backend/tests/` | 112 eval tests covering all guardrail categories. Run: `pytest backend/tests/` |
| **MCP App** | `mcp-app/` | TypeScript MCP server serving interactive HTML UIs (chat, lessons, progress) inside Claude Desktop/claude.ai. Proxies to FastAPI via service key auth. |

## Skill File Format

Skills are Markdown files with YAML frontmatter — the same format as Claude skill files:

```markdown
---
name: marathi_conversation_partner
description: Friendly Marathi tutor for diaspora kids
input:
  child_id: string
  message: string
  history: list
output:
  format: json
  schema:
    marathi_text: string
    english_hint: string?
connectors:
  - get_child_profile
  - get_lesson_context
---

You are Mitra, a friendly Marathi tutor for kids.
... (the system prompt — this IS the intelligence)
```

The frontmatter declares structured metadata. The Markdown body is used directly as the LLM system prompt.

## Key Design Decisions

**Skills as Markdown, not code**: The intelligence lives in portable `.md` files — system prompts with input/output contracts. The same skill file works in the web app (via `run_skill()`), in Claude Desktop (via MCP resources), or in any future client. Adding a new capability means writing a new `.md` file, not Python code.

**LLM-as-Orchestrator**: The LLM receives connector tool definitions and decides what context it needs. The gateway doesn't hardcode "fetch profile, then fetch lesson, then call LLM." Instead, the LLM calls `get_child_profile` and `get_lesson_context` itself via the agentic loop.

**Connectors, not MCP in-process**: Connectors are plain Python functions called directly — no MCP client/server indirection for in-process calls. The MCP server (`mcp_server.py`) wraps the same connectors for external access.

**Deterministic logic stays in code**: XP/streak calculations are math, not AI. They live in `gateway/progress_utils.py` as plain functions, not LLM skill invocations.

**Auto-generated tool schemas**: `core/llm.py` generates OpenAI-style tool definitions from connector function signatures and docstrings — no hand-written tool manifests to keep in sync.

**Structured JSON Output**: The LLM returns `{"marathi_text": "...", "english_hint": "..."}` enforced via `response_format`. Falls back gracefully if the LLM returns plain text.

**Token Refresh**: The frontend's Axios interceptor catches 401s, refreshes the JWT via `/auth/refresh`, and retries the original request. Concurrent requests queue behind the refresh.

## Database Schema (Supabase)

```
parents ──────< children ──────< conversations ──────< messages
                   │                    │
                   │                    └──────< conversation_flags
                   │
                   ├──────< child_lesson_progress >────── lessons (icon, vocab, quiz)
                   │
                   └──────< child_mission_progress >───── missions
```

Core tables: `parents`, `children`, `lessons`, `child_lesson_progress`, `conversations`, `conversation_messages`, `conversation_flags`, `missions`. RLS on `parents` and `children`; all other access goes through the FastAPI gateway with auth checks.
