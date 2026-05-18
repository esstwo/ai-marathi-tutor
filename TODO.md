# MarathiMitra — TODO

## Auth
- [ ] Switch from localStorage tokens to httpOnly cookies (more secure, simpler frontend — eliminates interceptor/refresh logic, but needs CORS `credentials: true` + cookie domain config for Vercel/Render cross-origin)

## Capstone Review Fixes (Remaining)
- [ ] Fix 4 (Section 3.2): Compute `marathi_ratio` — calculate Devanagari character ratio in child messages, write to `conversations` table in `end_conversation`
- [x] Fix 5 (Section 3.5): Prompt engineering — add few-shot examples, Romanized Marathi handling, conversation flow control to `skills/conversation.md`

## Plugin Architecture
- [x] Phase 1: Extract skill definitions as Markdown files with YAML frontmatter (`skills/conversation.md`, `lessons.md`, `progress.md`) + skill loader
- [x] Phase 2: Split MCP tools into domain-grouped connectors (`connectors/supabase/`, `connectors/tts/`) + connector registry
- [x] Phase 3: Generic agentic loop in `core/llm.py` — `run_skill(skill, messages, connectors)` works with any skill
- [x] Phase 4: Thin HTTP gateway (`gateway/api.py`) replacing 5 router files
- [x] Phase 5: MCP server (`mcp_server.py`) exposing skills + connectors for Claude Desktop
- [x] Phase 6: Cleanup — wired gateway into main.py, deleted old modules (routers/, mcp/, dependencies/, models/, prompts/)
- [ ] Optional: Deploy MCP server as separate Render service with SSE transport for external MCP clients

## MCP App (Interactive UI inside Claude)
- [x] Scaffold TypeScript MCP App server in `mcp-app/` with `@modelcontextprotocol/sdk`
- [x] Add service key auth bypass to FastAPI gateway for server-to-server calls
- [x] Create API client (`api-client.ts`) proxying to FastAPI with `X-Service-Key` header
- [x] Build MCP server (`server.ts`) with 3 primary tools + 7 inner tools + 3 HTML resources
- [x] Create shared CSS design system (`styles/shared.css`) with Devanagari fonts
- [x] Build progress app (`mcp-app/apps/progress.html`) — XP, streak, level dashboard with roadmap
- [x] Build conversation app (`mcp-app/apps/conversation.html`) — chat UI with Mitra, TTS playback, message history
- [x] Build lessons app (`mcp-app/apps/lessons.html`) — lesson browser, vocabulary cards, quiz interface
- [x] Bundle with Vite + vite-plugin-singlefile for sandboxed iframe delivery
- [x] Add stdio transport for Claude Desktop integration
- [x] Deploy as remote MCP server on Render with StreamableHTTP transport
- [x] Add OAuth 2.1 + PKCE authentication (`auth.ts`) for claude.ai remote access
- [x] Add TTS buttons to quiz questions and answer options (Devanagari detection)

## AI Features
- [x] Weekly AI parent digest — Llama 3.3 writes personalised email from weekly stats, sent via Resend
- [ ] AI pronunciation coach — STT + LLM feedback on Marathi pronunciation accuracy
- [ ] Adaptive lesson generation — LLM generates new vocabulary + quizzes based on weak areas
- [ ] Scenario-based conversation missions with specific roles (shopkeeper, grandparent, etc.)

## Game-Based Missions
- [x] DB migration: add `steps`, `title_english`, `created_at` to missions table
- [x] Mission connectors (`connectors/supabase/missions.py`): CRUD + progress tracking
- [x] Mission generator skill (`skills/mission_generator.md`): LLM generates scenarios from level vocab
- [x] Mission guide skill (`skills/mission_guide.md`): LLM plays scenario character, tracks steps, scores Marathi
- [x] Mission API routes: generate, start, message, end, list, progress
- [x] Mission XP: score-based XP awards, missions_completed in progress
- [x] Frontend: Missions page with list + play views, TTS, step progress bar, completion overlay
- [x] Navigation: Missions in navbar, Home quick action, Progress stat

## Content
- [x] Generate 80 Marathi lessons (20 per level × 4 levels) with vocabulary + quizzes
- [x] Add per-lesson icons (lucide icon names) for semantic lesson cards
- [x] Seed all lessons into Supabase with `--reseed` support

## Guardrails
- [x] Input validation: max message length (500), profanity filter, prompt injection detection
- [x] Output validation: JSON structure check, URL/email/phone stripping, profanity fallback
- [x] Session limits: 50 messages/conversation, 30 min duration, 3 concurrent conversations
- [x] Content flagging: `conversation_flags` table, auto-flag sanitized outputs, parent review endpoint
- [x] Cost protection: global daily LLM call limit (configurable via `DAILY_LLM_CALL_LIMIT`)
- [x] Eval tests: 123 pytest cases covering all guardrail categories

## Public Launch Hardening
- [x] Persisted per-child daily LLM cap (`usage_counters` table + atomic `increment_usage_counter` Postgres RPC; `DAILY_LLM_CALL_LIMIT_PER_CHILD`, default 100)
- [x] Email verification on signup (Supabase "Confirm email" + signup endpoint returns `email_verification_required` flag + frontend "check your email" toast)
- [x] Per-IP signup rate limit (`signup_attempts` table; `SIGNUP_ATTEMPTS_PER_HOUR`, default 5; X-Forwarded-For aware)
- [x] Cloudflare Turnstile on signup AND login (token forwarded to Supabase Auth, verified server-side; widget conditional on `VITE_TURNSTILE_SITE_KEY`)
- [x] CORS parsing tolerates whitespace + trailing slashes; logs the parsed allowlist at startup
- [x] Resend domain (marathimitra.site) verified — weekly digest sends end-to-end
- [x] Supabase auth emails routed through Resend SMTP (custom sender on your domain, no Supabase rate limit)
- [x] Branded HTML email templates (Confirm signup + Reset password) in Supabase
- [ ] Per-child cap on mission generation (currently shares the LLM call counter — heavy endpoint, worth its own limit ~5/day)
- [ ] Per-child cap on Whisper STT (`/tts/transcribe`) — currently ungated, charges Groq per audio second
- [ ] Per-child / per-day cap on Google TTS character spend (`/tts/speak`) — currently ungated apart from 200-char per-request limit
- [ ] Hard daily quota on Google Cloud TTS API characters/day (provider-side, set in GCP console)
- [ ] Spend alert on Groq + spend cap on Supabase plan + budget alerts on GCP billing
- [ ] Per-IP rate limit on `/auth/login` (currently only signup is throttled — login brute-force protection is Supabase's responsibility but a thin pre-check would help)
