# Plan: Plugin Architecture for MarathiMitra (Section 4)

## Context
The capstone review (Section 4) recommends converting MarathiMitra from a full-stack monolith into a plugin architecture: Skills (portable intelligence) + MCP Connectors (standardized data/service access). The current app has ~1,150 lines of Python backend where the actual intelligence is a 42-line prompt and a 185-line service — the rest is plumbing. This plan is an architecture document for future implementation.

---

## Current Architecture
```
React (Vercel) → FastAPI monolith (Render) → Groq LLM / Supabase / Google TTS
```
The FastAPI backend handles: auth, HTTP routing, DB queries, LLM calls, TTS, response parsing, XP/streak logic — all in one process.

## Target Architecture
```
React (Vercel) → Thin API Gateway (auth + routing) → LLM Orchestrator
                                                        ↕
                                              MCP Servers (tools)
                                            ┌─────────────────────┐
                                            │ supabase-mcp        │
                                            │ tts-mcp             │
                                            └─────────────────────┘
```
The LLM becomes the orchestrator. It calls MCP tools to fetch data, manage conversations, and generate responses. The gateway handles auth and forwards requests.

---

## Deployment Strategy

**Recommended approach: Start in-process (Phase 1), split later if needed.**

- **Phase 1:** Everything stays deployed as a single FastAPI app on Render. The MCP "servers" are just Python modules called in-process — no separate deployment, no network overhead, no extra cost. You get 90% of the architectural benefit with zero deployment complexity.
- **Phase 2+:** If you need independent scaling or want other LLM apps to connect to the same MCP servers, split them into separate Render services communicating via SSE transport.
- **The gateway always stays on Render** — it's the only publicly accessible endpoint.

---

## MCP Servers

### Server 1: `supabase-mcp` (Data Layer)

Replaces all scattered `supabase_admin.table(...)` calls across services and routers.

**Tools:**

| Tool | Input | Output |
|------|-------|--------|
| `get_child_profile` | `{child_id}` | `{name, age, current_level, xp_total, streak_days}` |
| `get_current_lesson_context` | `{child_id}` | `{title, theme, vocabulary[]}` or null |
| `list_lessons` | `{level}` | Array of lesson objects |
| `get_lesson` | `{lesson_id}` | Full lesson (vocab + quiz) |
| `record_lesson_completion` | `{child_id, lesson_id, score}` | `{xp_earned, xp_total, streak_days}` |
| `start_conversation` | `{child_id}` | `{conversation_id}` |
| `save_message` | `{conversation_id, role, content}` | `{message_id}` |
| `get_conversation_history` | `{conversation_id, limit?}` | Array of `{role, content}` |
| `end_conversation` | `{conversation_id}` | `{xp_earned, duration_minutes, marathi_ratio}` |
| `get_child_progress` | `{child_id}` | Stats object |
| `get_parent_progress` | `{parent_id}` | Aggregated stats |
| `create_child` | `{parent_id, name, age, avatar}` | Child object |

**Key decision:** XP/streak logic (`_update_streak`, `award_*_xp` from `progress.py`) lives inside this server as composite tools — not split between gateway and MCP. These are deterministic math, not LLM skills.

**Auth:** This server trusts its caller. Token validation stays in the gateway.

### Server 2: `tts-mcp` (Text-to-Speech)

Wraps `backend/services/tts.py` (Google Cloud TTS).

| Tool | Input | Output |
|------|-------|--------|
| `speak_marathi` | `{text}` | `{audio_base64, format: "mp3"}` |

Returns base64 since MCP communicates via JSON. In-memory cache moves here.

### Server 3: `content-mcp` (deferred)

Optional. Only needed when lesson content comes from somewhere other than Supabase (e.g., Google Sheets, a CMS). Skip for v1.

---

## Skill Extraction

### Skill: Marathi Conversation Partner

The core intelligence, currently split across `mitra_system.py` (prompt template) and `mitra.py` (prompt construction, LLM call, response parsing).

Becomes a portable artifact with 3 parts:

**Part A — System Instructions** (`skills/mitra-conversation/system-instructions.md`)
The existing `MITRA_BASE_PROMPT` content (personality, rules, safety, format) plus new sections:
- Romanized Marathi handling
- Few-shot examples (3-5 ideal exchanges)
- Conversation flow control
- Tool-calling protocol: "Call `get_child_profile` first to learn who you're talking to. Call `get_current_lesson_context` to know what vocabulary to weave in."

**Part B — Tool Manifest** (`skills/mitra-conversation/tool-manifest.json`)
Declares which MCP tools this skill needs access to:
- `supabase-mcp/get_child_profile`
- `supabase-mcp/get_current_lesson_context`
- `supabase-mcp/get_conversation_history`
- `supabase-mcp/save_message`
- `tts-mcp/speak_marathi`

**Part C — Structured Output**
Replace the brittle MARATHI/HINT regex parsing (`_parse_response`) with JSON structured output:
```json
{"marathi_text": "...", "english_hint": "..." or null}
```
The LLM's structured output mode enforces the schema. The `_parse_response` function and its regex are eliminated.

### What does NOT become a skill
- **Progress/Gamification** — XP and streaks are deterministic math. They stay as logic inside `supabase-mcp` composite tools.
- **Lesson Delivery** — Currently just CRUD. Stays as MCP tool calls unless you later want the LLM to dynamically generate lessons.

---

## Migration Path (4 phases, each independently deployable)

### Phase 1: Internal Refactor (zero risk)
Reorganize code into MCP-shaped modules without changing deployment.

- Create `backend/mcp/supabase_tools.py` — move all Supabase operations from routers/services into standalone functions matching MCP tool signatures
- Create `backend/mcp/tts_tools.py` — move `synthesize_marathi` with base64 encoding
- Create `backend/skills/mitra_conversation.py` — extract system instructions + response parsing
- Update routers to call these new modules
- Frontend sees zero change. Build passes. Behavior identical.

### Phase 2: Standalone MCP Servers
Deploy MCP servers as separate processes.

- Create `mcp-servers/supabase-server/` with Python MCP SDK, move Phase 1 functions into tool handlers
- Create `mcp-servers/tts-server/` similarly
- Gateway becomes an MCP client, calls tools via stdio/SSE transport
- Deploy on Render as separate services
- Frontend still talks to same REST API. No frontend changes.

### Phase 3: LLM-as-Orchestrator
The LLM directly calls MCP tools instead of the gateway orchestrating.

- Pass MCP tool definitions to the LLM as function/tool schemas (Groq supports this with Llama 3.3)
- Gateway's `/conversations/{id}/message` simplifies to: send message + tools to LLM → execute tool calls → return response
- Remove `_build_lesson_context`, `_build_system_prompt`, `_get_child` from mitra.py — the LLM calls these tools itself
- System instructions tell the LLM the tool-calling protocol

**Risk:** Medium. LLM may not always call tools correctly. Mitigate with strong system instructions + validation layer + fallback to Phase 2 behavior.

### Phase 4: Thin Gateway (optional, deferred)
Replace FastAPI with a minimal auth proxy. Frontend uses MCP client directly for CRUD. Conversations still go through server-side LLM orchestrator (keys must not be in browser). High complexity, marginal benefit — defer.

---

## What Stays vs Goes

| Stays | Role in new architecture |
|-------|--------------------------|
| `backend/main.py` | Slimmed gateway (CORS, auth, health) |
| `backend/dependencies/auth.py` | Token validation stays in gateway |
| `backend/models/schemas.py` | REST API contract with frontend |
| `backend/services/llm_errors.py` | LLM failure → HTTP status mapping |
| `content/*.json` | Seed data |

| Goes | Where it moves |
|------|----------------|
| `backend/db/supabase_client.py` | Into `supabase-mcp` |
| `backend/services/mitra.py` | Split: `_call_llm` stays in gateway, prompt building becomes LLM self-orchestration, `_parse_response` eliminated by structured output |
| `backend/services/progress.py` | Into `supabase-mcp` as composite tools |
| `backend/services/tts.py` | Into `tts-mcp` |
| `backend/routers/*.py` | Dramatically simplified thin pass-throughs |

| New | Purpose |
|-----|---------|
| `mcp-servers/supabase-server/` | Supabase MCP server |
| `mcp-servers/tts-server/` | TTS MCP server |
| `skills/mitra-conversation/` | Portable skill artifact (instructions + examples + tool manifest) |

---

## Frontend Impact

- **Phases 1–3:** Zero frontend changes. The gateway exposes the same 11 REST endpoints. The axios interceptor, auth flow, and TypeScript types all remain valid.
- **Future (streaming):** Once the LLM orchestrates, SSE streaming for conversation responses becomes possible. Would need a new `sendMessageStream` in `api.ts` using EventSource.
- **Phase 4 only:** Frontend would use an MCP client library instead of REST. Deferred.

---

## Key Architectural Decisions

1. **XP/streaks are math, not AI** — they stay as deterministic logic in `supabase-mcp`, not LLM skills
2. **Auth stays in the gateway** — MCP servers trust their caller
3. **Structured JSON output replaces regex parsing** — eliminates the brittle `_parse_response`
4. **Frontend is shielded** — REST contract unchanged through Phases 1–3
5. **Phase 1 is the critical path** — zero risk, validates tool boundaries, delivers immediate code quality
6. **content-mcp is deferred** — over-engineering with only 2 JSON files
