# MarathiMitra (मराठीमित्र)

Your child's friendly AI companion for learning spoken Marathi.

## What is this?

MarathiMitra helps diaspora kids (ages 5-12) who understand Marathi but respond in English
to build confidence in spoken Marathi through AI-powered conversations, structured lessons,
and game-based missions — interactive, scenario-based challenges where the child speaks Marathi
to progress through culturally familiar situations (visiting grandma, shopping at a market,
celebrating Ganpati).

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend:** Python + FastAPI (thin gateway) + portable Markdown skill files
- **Database:** Supabase (PostgreSQL + Auth)
- **AI:** Groq API (Llama 3.3 70B) — conversations, missions, weekly digest
- **TTS:** Google Cloud Text-to-Speech (Marathi) — vocabulary, quiz, chat
- **STT:** Groq Whisper large-v3 — Marathi speech-to-text input
- **Email:** Resend — weekly AI-written parent digest
- **MCP:** MCP App server (Node/TypeScript) with OAuth 2.1 for Claude Desktop + claude.ai
- **Deployment:** Vercel (frontend) + Render (backend + MCP App + digest cron)

## Project Structure

```
backend/
  main.py                          # FastAPI app — loads gateway routers
  core/
    skill_loader.py                # Discovers and loads .md skill files
    connector_registry.py          # Maps connector names → callable functions
    llm.py                         # Generic agentic loop + LLM error hierarchy
  skills/                          # Portable skill definitions (Markdown + YAML frontmatter)
    conversation.md                # Mitra tutor — personality, safety, response format
    lessons.md                     # Lesson delivery — retrieve and present vocabulary
    progress.md                    # Progress tracker — XP rules, streak logic
    mission_generator.md           # Generate mission scenarios from level vocabulary
    mission_guide.md               # Play scenario character, guide child through steps
    parent_digest.md               # Weekly parent email — tone rules + 3 few-shot examples
  connectors/                      # Minimal code bridging skills to external systems
    supabase/
      auth.py                      # signup, login, refresh, parent records
      children.py                  # child profiles, ownership checks
      conversations.py             # start/end conversations, save/get messages
      lessons.py                   # list/get/complete lessons
      progress.py                  # counts and aggregations for reporting
      missions.py                  # CRUD for missions + child mission progress
      digest.py                    # date-filtered queries for weekly digest
    tts/
      google_tts.py                # speak_marathi (base64 MP3)
  gateway/                         # Thin HTTP layer
    api.py                         # All REST endpoints (single file)
    auth.py                        # Token validation + child ownership
    guardrails.py                  # Input/output validation, session limits, cost protection
    progress_utils.py              # Deterministic XP/streak calculations
  services/
    tts.py                         # Google Cloud TTS wrapper with caching
    digest.py                      # Weekly parent digest: stats gathering, LLM call, email send
  db/
    supabase_client.py             # Supabase client init
    migrations.sql                 # Database schema
  tests/
    test_guardrails.py             # 112 eval tests for all guardrail categories
mcp_server.py                      # Standalone MCP server for Claude Desktop (stdio)
mcp-app/
  server.ts                        # MCP App server — interactive UIs inside Claude
  api-client.ts                    # API client proxying to FastAPI (Bearer or service key)
  auth.ts                          # OAuth 2.1 + PKCE server: discovery, login page, token exchange
  types.ts                         # Shared TypeScript types
  src/                             # App logic (TypeScript)
    conversation-app.ts            # Chat logic (message feed, TTS, end-chat)
    lessons-app.ts                 # Lesson flow (browse → learn → quiz → results + TTS on Marathi)
    progress-app.ts                # Dashboard rendering
  styles/shared.css                # Kid-friendly design system
frontend-react/
  src/
    components/                    # Navbar, LessonCard, DynamicIcon, LessonView, ProtectedRoute, shadcn/ui
    contexts/                      # AuthContext (token + refresh token management)
    services/                      # Axios API client with Bearer token + 401 refresh interceptor
    types/                         # TypeScript interfaces matching backend schemas
    pages/
      Index.tsx                    # Landing page
      Login.tsx                    # Sign in / sign up
      ChildSetup.tsx               # Child profile creation + selection
      Home.tsx                     # Dashboard with stats + quick actions
      Lessons.tsx                  # Lesson browser with level selector
      Chats.tsx                    # AI conversation with Mitra
      Missions.tsx                 # Mission list + play view with step progress
      Progress.tsx                 # Child progress + level roadmap
      ParentProgress.tsx           # Parent aggregated dashboard
content/
  level1_lessons.json              # Level 1: Foundations (20 lessons)
  level2_lessons.json              # Level 2: Home Life (20 lessons)
  level3_lessons.json              # Level 3: Out & About (20 lessons)
  level4_lessons.json              # Level 4: Conversations (20 lessons)
scripts/
  seed_content.py                  # Seed lessons into Supabase (--reseed to replace all)
```

## Architecture

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for detailed diagrams and request flows.

The backend uses a **skills + connectors** architecture:

- **Skills** (`backend/skills/*.md`) — Portable Markdown files that define *what* the AI does. Each skill has YAML frontmatter (input/output schema, connector dependencies) and a Markdown body that serves as the LLM system prompt. Skills can run in the web app, Claude Desktop, or any MCP client.
- **Connectors** (`backend/connectors/`) — Minimal Python functions that bridge skills to external systems (Supabase, Google TTS). No business logic — just glue.
- **Core** (`backend/core/`) — Generic infrastructure: skill loader, connector registry, and the agentic tool-calling loop that works with any skill.
- **Gateway** (`backend/gateway/`) — Thin HTTP layer that maps REST endpoints to skill invocations and connector calls.
- **Services** (`backend/services/`) — Shared utilities: Google Cloud TTS wrapper with caching, and the weekly parent digest service (stats gathering + LLM call + Resend email).
- **MCP App** (`mcp-app/`) — TypeScript MCP server with OAuth 2.1 authentication serving interactive HTML apps inside Claude.

## API Endpoints

| Method | Path                                | Description                              | Auth              |
|--------|-------------------------------------|------------------------------------------|-------------------|
| GET    | /health                             | Health check                             | None              |
| POST   | /auth/signup                        | Create account                           | None              |
| POST   | /auth/login                         | Authenticate user                        | None              |
| POST   | /auth/children                      | Add a child profile                      | Bearer token      |
| POST   | /auth/refresh                       | Refresh expired access token             | None              |
| GET    | /lessons/by-level/{level}           | List lessons for a level                 | None              |
| GET    | /lessons/{lesson_id}                | Get lesson with vocabulary + quiz        | None              |
| POST   | /lessons/{lesson_id}/complete       | Record completion, award XP              | Bearer token      |
| POST   | /conversations/start                | Start AI conversation                    | Bearer token      |
| POST   | /conversations/{id}/message         | Send message, get AI response            | Bearer token      |
| POST   | /conversations/{id}/end             | End chat, calculate XP                   | Bearer token      |
| GET    | /progress/{child_id}                | Get child progress stats                 | Bearer token      |
| GET    | /parents/{parent_id}/progress       | Aggregated stats across children         | Bearer token      |
| GET    | /missions/by-level/{level}          | List missions for a level                | Bearer token      |
| POST   | /missions/generate                  | LLM-generate a new mission               | Bearer token      |
| GET    | /missions/progress/{child_id}       | Get child's mission progress             | Bearer token      |
| POST   | /missions/start                     | Start a mission (creates conversation)   | Bearer token      |
| POST   | /missions/{id}/message              | Send message in active mission           | Bearer token      |
| POST   | /missions/{id}/end                  | Quit mission early                       | Bearer token      |
| POST   | /tts/speak                          | Synthesize Marathi text to audio         | Bearer token      |
| POST   | /tts/transcribe                     | Transcribe Marathi audio to text         | Bearer token      |
| POST   | /digest/send                        | Trigger weekly digests for all parents   | Service key only  |
| GET    | /digest/preview/{parent_id}         | Preview digest without sending           | Bearer / svc key  |

## Setup

1. Clone this repo
2. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   SUPABASE_URL=...
   SUPABASE_KEY=...
   SUPABASE_SERVICE_KEY=...
   GROQ_API_KEY=...
   RESEND_API_KEY=...
   RESEND_FROM_EMAIL=MarathiMitra <digest@yourdomain.com>
   ```
3. Install backend dependencies: `pip install -r requirements.txt`
4. Run the database migration: apply `backend/db/migrations.sql` in Supabase SQL Editor
5. Seed lesson content: `python -m scripts.seed_content`
6. Start backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
7. Start React frontend:
   ```bash
   cd frontend-react
   npm install
   npm run dev
   ```
8. Open `http://localhost:5173`

## Claude Desktop Integration (stdio)

MarathiMitra has two MCP integration paths. For Claude Desktop, use the stdio MCP App server — no OAuth needed, uses a service key directly:

```json
{
  "mcpServers": {
    "marathi-mitra": {
      "command": "node",
      "args": ["/path/to/mcp-app/dist/server.js", "--stdio"],
      "env": {
        "MARATHI_API_URL": "https://marathi-mitra-api.onrender.com",
        "MARATHI_SERVICE_KEY": "your-service-key"
      }
    }
  }
}
```

Build first: `cd mcp-app && npm run build`

## MCP App (Interactive UI inside Claude)

The MCP App server renders interactive HTML UIs (chat, lessons, progress dashboard) directly inside Claude Desktop or claude.ai.

**For claude.ai (remote HTTP + OAuth 2.1):**

1. Deploy `mcp-app/` to Render (see `render.yaml`)
2. Set env vars: `MARATHI_API_URL`, `MARATHI_SERVICE_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `MCP_BASE_URL`
3. Add `https://your-mcp-app.onrender.com/mcp` as a remote MCP server in claude.ai settings
4. Claude opens the OAuth login page — parents sign in with their existing MarathiMitra credentials
5. All subsequent `/mcp` requests carry a Supabase JWT — the backend validates ownership normally

**OAuth 2.1 endpoints exposed by the MCP App:**

| Endpoint | Purpose |
|---|---|
| `GET /.well-known/oauth-authorization-server` | OAuth discovery metadata |
| `GET /.well-known/oauth-protected-resource` | Protected resource metadata |
| `GET /authorize` | Start OAuth flow |
| `GET /login` | Login page (email + password form) |
| `POST /login` | Validate credentials, issue auth code |
| `POST /token` | PKCE code exchange → Supabase JWT |

**Tools registered:** `start-marathi-practice`, `browse-lessons`, `show-progress` (each opens an interactive HTML app), plus 7 inner tools for app-to-server communication.

## Weekly Parent Digest

Every Sunday at 9am UTC a Render cron job generates and emails personalised learning summaries to all parents. For each child the AI (Llama 3.3 70B) is given:

- Lessons completed this week with quiz scores
- Number of Mitra conversations
- Current streak and total XP

It writes a warm, specific, 3-4 paragraph email and sends it via Resend.

To preview without sending:
```bash
curl https://marathi-mitra-api.onrender.com/digest/preview/<parent_id> \
  -H "X-Service-Key: your-service-key"
```

## Deployment

A `render.yaml` Blueprint defines all backend services — connect the repo to Render and it auto-configures everything.

| Service | Type | Notes |
|---|---|---|
| `marathi-mitra-api` | Web | FastAPI backend |
| `marathi-mitra-mcp-app` | Web | MCP App with OAuth 2.1 |
| `marathi-weekly-digest` | Cron | Sundays 9am UTC |

- **Frontend:** Deploy `frontend-react/` to Vercel — set `VITE_API_BASE_URL` to the backend URL
- **Backend:** Render web service — `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **MCP App:** Render web service — `node dist/server.js` (no `--stdio` flag for HTTP mode)

## Project Status

MVP — validating core hypothesis with 5 beta families.
