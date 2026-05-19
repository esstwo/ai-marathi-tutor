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
│  │  │ Cost:   per-child daily LLM cap (persisted, atomic)    │ │   │
│  │  │         + global daily backstop (in-memory)            │ │   │
│  │  │ Abuse:  per-IP signup rate limit (persisted),          │ │   │
│  │  │         Cloudflare Turnstile token forwarded to        │ │   │
│  │  │         Supabase for server-side verification          │ │   │
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
│  │    missions.py                                               │    │
│  │    progress.py                                               │    │
│  │    digest.py          (weekly stats queries)                 │    │
│  │    usage.py           (per-child LLM call counter, atomic    │    │
│  │                        increment via Postgres RPC)           │    │
│  │    rate_limits.py     (per-IP signup attempt tracking)       │    │
│  └──────┬──────────────────────────────┬───────────────────────┘    │
│         │                              │                             │
│  ┌──────▼──────────┐   ┌──────────────▼──────────────┐              │
│  │  Skill Files    │   │  Connector Registry          │              │
│  │  (skills/*.md)  │   │  (core/connector_registry.py)│              │
│  │                 │   │                              │              │
│  │  conversation      │   │  Auto-discovers all          │              │
│  │  lessons           │   │  connector functions,        │              │
│  │  progress          │   │  maps names → callables      │              │
│  │  mission_generator │   │                              │              │
│  │  mission_guide     │   │                              │              │
│  │  parent_digest     │   │                              │              │
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
          │ Chat completions via OpenAI-compatible SDK
          │
┌─────────┴────────┐    ┌──────────────────┐
│   Sarvam AI      │    │   Groq Cloud     │
│  sarvam-105b     │    │  Whisper v3      │
│  (LLM engine,    │    │  (speech-to-text │
│  Indian-native)  │    │   for /tts/      │
│                  │    │   transcribe)    │
└──────────────────┘    └──────────────────┘


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
                    │  progress. TTS on all Marathi      │
                    │  text (vocab, quiz Q&A, chat).     │
                    │                                    │
                    │  stdio (Desktop): service key auth │
                    │  HTTP (claude.ai): OAuth 2.1+PKCE  │
                    │    auth.ts hosts login page,       │
                    │    /authorize, /token endpoints.   │
                    │    Per-session JWT forwarded to    │
                    │    FastAPI — owns child checks      │
                    └──────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │  Weekly Digest (services/digest)  │
                    │                                    │
                    │  Render cron: Sundays 9am UTC      │
                    │  For each parent:                  │
                    │   1. Query this week's lesson      │
                    │      completions + conversations   │
                    │   2. LLM writes personalised email │
                    │   3. Send via Resend               │
                    │                                    │
                    │  Preview: GET /digest/preview/:id  │
                    │  Trigger: POST /digest/send        │
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

## Request Flow: Mission Gameplay

```
Child starts a mission
       │
       ▼
┌─────────────────┐
│  POST /missions/ │
│  start           │
└───────┬─────────┘
        │
        ▼
  Create conversation with context = {"mission_id": "..."}
  Mark mission progress as "in_progress"
        │
        ▼
  run_skill(mission_guide_skill, opening prompt, connectors)
    │
    │  LLM calls get_child_profile + get_mission_by_id
    │  Sets the scene, prompts child for Step 1
    │
    ▼
  Return: {marathi_text, mission_step: 1, mission_complete: false}
        │
        ▼
  ┌── Message Loop ─────────────────────────────────┐
  │                                                   │
  │  Child sends message                              │
  │    │                                              │
  │    ▼                                              │
  │  POST /missions/{conv_id}/message                 │
  │    │                                              │
  │    ▼                                              │
  │  Guardrails (same as conversations)               │
  │    │                                              │
  │    ▼                                              │
  │  run_skill(mission_guide_skill, ...)              │
  │    │                                              │
  │    ▼                                              │
  │  LLM returns:                                     │
  │    mission_step (current step number)              │
  │    step_score (0-3: Marathi quality)               │
  │    mission_complete (bool)                         │
  │    │                                              │
  │    ├── Not complete → continue loop               │
  │    │                                              │
  │    └── Complete →                                 │
  │         Calculate final score (avg step_scores)    │
  │         XP = xp_reward × (score/100), min 10      │
  │         Award XP, end conversation                 │
  │         Return: {score, xp_earned, xp_total}       │
  └───────────────────────────────────────────────────┘
```

## Request Flow: Mission Generation

```
Child taps "Generate New Mission" for level 2
       │
       ▼
  POST /missions/generate  {child_id, level: 2}
       │
       ▼
  Fetch all lesson vocabulary for level 2
       │
       ▼
  run_skill(mission_generator_skill, vocab context)
       │
       ▼
  LLM returns:
    {title, title_english, scenario, steps[], required_vocab[], xp_reward}
       │
       ▼
  Save to shared `missions` table (available to all children)
       │
       ▼
  Return the new mission
```

## Layer Responsibilities

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **Gateway** | `backend/gateway/` | HTTP endpoints, auth validation, request/response mapping. CRUD calls connectors directly. Conversations and missions use `run_skill()`. Mission scoring and XP are deterministic (in `progress_utils.py`). |
| **Guardrails** | `backend/gateway/guardrails.py` | Child safety + abuse prevention: input validation (length, profanity, prompt injection), output sanitization (PII/URL stripping, JSON validation), session limits (message/time/concurrency caps), cost protection (per-child persisted daily LLM cap + global in-memory backstop), per-IP signup rate limit (persisted), X-Forwarded-For aware IP extraction. |
| **Core** | `backend/core/` | Generic infrastructure: skill loader, connector registry, agentic tool-calling loop. Not MarathiMitra-specific. |
| **Skills** | `backend/skills/` | Portable Markdown files — system prompts with YAML frontmatter declaring inputs, outputs, and connector dependencies. Five skills: conversation, lessons, progress, mission_generator, mission_guide. The product's intelligence. |
| **Connectors** | `backend/connectors/` | Minimal glue code — plain Python functions that call external systems. No business logic. |
| **Services** | `backend/services/` | Shared utilities: Google Cloud TTS wrapper with caching; weekly digest service (stats gathering, LLM call, Resend email). |
| **Tests** | `backend/tests/` | 123 eval tests covering all guardrail categories (input, output, session, per-child cost, signup rate limit). Run: `pytest backend/tests/` |
| **MCP App** | `mcp-app/` | TypeScript MCP server serving interactive HTML UIs (chat, lessons, progress) inside Claude Desktop/claude.ai. TTS buttons on all Marathi text (detected via Devanagari Unicode range). stdio mode uses service key; HTTP mode uses OAuth 2.1 + PKCE backed by Supabase email/password. |

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
  format: json        # or "text" for plain-text output (e.g. parent_digest)
  schema:
    marathi_text: string
    english_hint: string?
max_tokens: 300       # optional — override the global default (useful for longer outputs)
connectors:
  - get_child_profile
  - get_lesson_context
---

You are Mitra, a friendly Marathi tutor for kids.
... (the system prompt — this IS the intelligence)
```

The frontmatter declares structured metadata. The Markdown body is used directly as the LLM system prompt. Skills that produce longer output (e.g. `parent_digest` at 600 tokens) declare their own `max_tokens`; all others inherit the global default of 300.

## Key Design Decisions

**Skills as Markdown, not code**: The intelligence lives in portable `.md` files — system prompts with input/output contracts. The same skill file works in the web app (via `run_skill()`), in Claude Desktop (via MCP resources), or in any future client. Adding a new capability means writing a new `.md` file, not Python code.

**LLM-as-Orchestrator**: The LLM receives connector tool definitions and decides what context it needs. The gateway doesn't hardcode "fetch profile, then fetch lesson, then call LLM." Instead, the LLM calls `get_child_profile` and `get_lesson_context` itself via the agentic loop.

**Connectors, not MCP in-process**: Connectors are plain Python functions called directly — no MCP client/server indirection for in-process calls. The MCP server (`mcp_server.py`) wraps the same connectors for external access.

**Deterministic logic stays in code**: XP/streak calculations are math, not AI. They live in `gateway/progress_utils.py` as plain functions, not LLM skill invocations.

**Auto-generated tool schemas**: `core/llm.py` generates OpenAI-style tool definitions from connector function signatures and docstrings — no hand-written tool manifests to keep in sync.

**Shared, LLM-Generated Missions**: Missions are not static content — they're generated on-the-fly by the `mission_generator` skill using level vocabulary. Generated missions are saved to a shared `missions` table so all children can play them. Any child can request a new mission to grow the pool. The `mission_guide` skill plays the scenario character, tracks step progression, and scores Marathi usage (0-3 per step). The gateway aggregates step scores into a final 0-100 percentage and awards XP proportionally.

**Voice Input via Groq Whisper**: Kids can tap a mic button to speak instead of type. Audio is recorded in the browser (WebM), sent to Groq's Whisper large-v3 model with `language="mr"` (Marathi), and the transcribed text is inserted into the input field for review before sending. Whisper's multilingual model handles the mixed Marathi-English speech diaspora kids naturally produce. (Note: this is the only thing Groq is still used for — LLM moved to Sarvam.)

**Structured JSON Output**: The LLM returns `{"marathi_text": "...", "english_hint": "..."}`. Sarvam does not support OpenAI's `response_format={"type":"json_object"}` parameter, so JSON output is enforced via three layers instead: (1) each JSON-producing skill prompt has an explicit "Output format (strict)" section near the top, (2) the gateway appends a single-line JSON reminder to each user turn before sending to the LLM — the reminder is NOT saved to conversation history so the UI is unaffected, and (3) `parse_json_response` is defensive: tries `json.loads` after stripping markdown fences, then falls back to extracting the first `{...}` substring from prose-wrapped output, and only as a last resort treats the entire response as plain text.

**Token Refresh**: The frontend's Axios interceptor catches 401s, refreshes the JWT via `/auth/refresh`, and retries the original request. Concurrent requests queue behind the refresh.

**TTS on all Marathi text**: A `hasMarathi()` helper (Devanagari Unicode range `ऀ–ॿ`) detects Marathi in any string and conditionally renders a 🔊 button. Applied to vocabulary flashcards, quiz questions, and quiz answer options in both the React frontend (`LessonView.tsx`) and the MCP App lessons UI. Buttons outside interactive elements prevent click interference with answer selection.

**MCP OAuth 2.1 backed by Supabase**: The MCP App acts as its own OAuth authorization server — `auth.ts` hosts the discovery metadata, login page, and token endpoints. The login form calls Supabase `signInWithPassword` directly and issues an OAuth auth code wrapping the resulting Supabase JWT. On token exchange the JWT is returned as the `access_token`. All `/mcp` requests validate the JWT via `supabase.auth.getUser()`. The FastAPI backend sees ordinary Bearer tokens and runs the same ownership checks as the web app. stdio mode (Claude Desktop) bypasses this entirely with a service key.

**Weekly AI Parent Digest**: `services/digest.py` pre-fetches structured data (lesson titles, scores, conversation counts) from Supabase, then passes it to the LLM as a plain-text context block. The LLM writes the email body; it never calls tools or queries the DB itself. This keeps the digest fast, cheap, and fully auditable. A Render cron service fires weekly; `GET /digest/preview/:id` lets developers inspect output without sending.

**Few-shot prompting in skill files**: The `parent_digest` skill embeds three annotated input/output examples directly in the Markdown body — an active week, a quiet week, and two children with mixed activity. This constrains tone, structure, and the contextualised XP phrasing without extra code. Any skill can adopt this pattern; the examples live in the same `.md` file as the instructions, so they stay in sync as the prompt evolves.

**Per-child cost protection (persisted, not in-memory)**: The original `track_llm_call()` counter was a single global in-memory dict — it reset on every Render redeploy and didn't isolate users. `track_child_llm_call(child_id)` now writes through a Postgres `increment_usage_counter` RPC (atomic upsert with returning) backed by the `usage_counters` table. One abusive child cannot exhaust the global budget; the counter survives restarts and is consistent across workers. The DB call fails open on errors — a Supabase outage logs a warning rather than blocking learning. The original global limit remains as a cheap backstop.

**Signup hardening (defence in depth)**: Three layers gate account creation: (1) a persisted per-IP rate limit (`signup_attempts` table, 5/hr default) blocks burst signup attempts even before any external service is called; (2) Cloudflare Turnstile tokens are forwarded to Supabase Auth, which verifies them server-side using the configured secret and rejects forged/invalid tokens; (3) Supabase email confirmation requires clicking a verification link before the account becomes usable. Any single layer being bypassed still leaves the other two. The Turnstile widget is conditional on `VITE_TURNSTILE_SITE_KEY`, so local dev without a Cloudflare account still works — Supabase silently accepts a missing `captcha_token` when its own CAPTCHA setting is off. Login is gated by the same Turnstile token because Supabase's CAPTCHA toggle is project-wide.

**CORS that doesn't lie**: `ALLOWED_ORIGINS` is parsed defensively — whitespace and trailing slashes are stripped per entry so `"a, b, c"` and `"https://a/"` both work. The parsed list is logged at startup (`[cors] allowed origins: [...]`) so misconfigurations are immediately visible in Render logs instead of presenting as mysterious "Disallowed CORS origin" errors hours later.

**Sarvam over Groq, OpenAI SDK over Sarvam SDK**: LLM provider is Sarvam AI (`sarvam-105b`) — Marathi-native, ~10× cheaper than Groq paid (Groq free-tier rate limits were becoming a constraint). Sarvam exposes an OpenAI-compatible chat-completions endpoint at `https://api.sarvam.ai/v1`, so the integration uses the official `openai` Python SDK pointed at that base URL — no vendor lock-in to Sarvam-specific client code, and swapping providers in the future is a base-URL change. Tool calling format matches OpenAI exactly. Groq is retained only for Whisper STT (`/tts/transcribe`).

**Mission context injected, not tool-fetched**: The gateway already fetches the child profile and mission row before calling the mission_guide skill, so making the LLM call `get_child_profile` + `get_mission_by_id` as tools was pure overhead — extra round-trips, extra tokens, extra failure modes. `_build_mission_context()` renders the full mission (title, scenario, all steps with target vocab, required vocab) and child summary into a `## Mission Context` block appended to the system prompt. mission_guide ships with `connectors: []` and the system prompt explicitly says "do NOT call tools — all the data you need is right above." Result: 1 LLM round per mission turn instead of 3-4, and no possibility of an empty response from an exhausted tool loop. This same pattern is worth applying to the conversation skill next.

**JSON reminders are appended, not saved**: Saved assistant messages in `conversation_messages` contain only the rendered `marathi_text` — not the JSON wrapper. When the LLM sees that history on subsequent turns, it tends to mirror the plain-text format and skip JSON. The gateway sidesteps this by appending a short `[Reply as a single JSON object: {...}]` reminder to each child message immediately before sending to the LLM. The reminder is not persisted, so the chat UI shows the child's actual message and the conversation history stays clean — but the LLM sees a fresh JSON cue on every turn. Same fix applied to both `/conversations/.../message` and `/missions/.../message`.

## Database Schema (Supabase)

```
parents ──────< children ──────< conversations ──────< messages
                   │                    │
                   │                    └──────< conversation_flags
                   │
                   ├──────< child_lesson_progress >────── lessons (icon, vocab, quiz)
                   │
                   ├──────< child_mission_progress >───── missions
                   │
                   └──────< usage_counters    (per-child × per-day LLM call count)

signup_attempts                              (per-IP, attempted_at — not joined to anything)
```

Core tables: `parents`, `children`, `lessons`, `child_lesson_progress`, `conversations`, `conversation_messages`, `conversation_flags`, `missions`, `child_mission_progress`, `usage_counters`, `signup_attempts`. Missions store `steps` (jsonb) and `required_vocab` alongside the scenario. RLS on `parents` and `children`; all other access goes through the FastAPI gateway with auth checks.

The `usage_counters` table is incremented atomically via the `increment_usage_counter(child_id, date)` Postgres function — `insert ... on conflict do update returning` so two concurrent backend workers can't race. The `signup_attempts` table is pruned opportunistically on insert (rows older than 24h for that IP are deleted), avoiding a separate cleanup job.
