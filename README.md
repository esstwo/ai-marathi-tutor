# MarathiMitra (मराठीमित्र)

Your child's friendly AI companion for learning spoken Marathi.

## What is this?

MarathiMitra helps diaspora kids (ages 5-12) who understand Marathi but respond in English
to build confidence in spoken Marathi through AI-powered conversations, structured lessons,
and game-based missions.

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend:** Python + FastAPI (thin gateway) + portable Markdown skill files
- **Database:** Supabase (PostgreSQL + Auth)
- **AI:** Groq API (Llama 3.3 70B)
- **TTS:** Google Cloud Text-to-Speech (Marathi)
- **MCP:** FastMCP server for Claude Desktop integration
- **Deployment:** Vercel (frontend) + Render (backend)

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
  connectors/                      # Minimal code bridging skills to external systems
    supabase/
      auth.py                      # signup, login, refresh, parent records
      children.py                  # child profiles, ownership checks
      conversations.py             # start/end conversations, save/get messages
      lessons.py                   # list/get/complete lessons
      progress.py                  # counts and aggregations for reporting
    tts/
      google_tts.py                # speak_marathi (base64 MP3)
  gateway/                         # Thin HTTP layer
    api.py                         # All REST endpoints (single file)
    auth.py                        # Token validation + child ownership
    progress_utils.py              # Deterministic XP/streak calculations
  services/
    tts.py                         # Google Cloud TTS wrapper with caching
  db/
    supabase_client.py             # Supabase client init
    migrations.sql                 # Database schema
mcp_server.py                      # Standalone MCP server for Claude Desktop
mcp-app/
  server.ts                          # MCP App server — interactive UIs inside Claude
  api-client.ts                      # API client proxying to FastAPI with service key
  types.ts                           # Shared TypeScript types
  apps/                              # HTML entry points (bundled to single-file by Vite)
    conversation.html                # Chat with Mitra
    lessons.html                     # Lesson browser + quiz
    progress.html                    # XP dashboard + level roadmap
  src/                               # App logic (TypeScript)
  styles/shared.css                  # Kid-friendly design system
frontend-react/
  src/
    components/                    # Navbar, LessonCard, LessonView, ProtectedRoute, shadcn/ui
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
      Progress.tsx                 # Child progress + level roadmap
      ParentProgress.tsx           # Parent aggregated dashboard
content/
  level1_lessons.json              # Level 1 lesson data (vocabulary + quizzes)
  level2_lessons.json              # Level 2 lesson data
scripts/
  seed_content.py                  # Seed lessons into Supabase
```

## Architecture

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for detailed diagrams and request flows.

The backend uses a **skills + connectors** architecture:

- **Skills** (`backend/skills/*.md`) — Portable Markdown files that define *what* the AI does. Each skill has YAML frontmatter (input/output schema, connector dependencies) and a Markdown body that serves as the LLM system prompt. Skills can run in the web app, Claude Desktop, or any MCP client.
- **Connectors** (`backend/connectors/`) — Minimal Python functions that bridge skills to external systems (Supabase, Google TTS). No business logic — just glue.
- **Core** (`backend/core/`) — Generic infrastructure: skill loader, connector registry, and the agentic tool-calling loop that works with any skill.
- **Gateway** (`backend/gateway/`) — Thin HTTP layer that maps REST endpoints to skill invocations and connector calls.
- **MCP Server** (`mcp_server.py`) — Exposes all connectors as MCP tools and skills as MCP resources/prompts for Claude Desktop.

The LLM (Llama 3.3 70B via Groq) acts as the orchestrator — it receives connector tool definitions and autonomously calls `get_child_profile` and `get_lesson_context` to gather context before responding.

## API Endpoints

| Method | Path                                | Description                          | Auth         |
|--------|-------------------------------------|--------------------------------------|--------------|
| GET    | /health                             | Health check                         | None         |
| POST   | /auth/signup                        | Create account                       | None         |
| POST   | /auth/login                         | Authenticate user                    | None         |
| POST   | /auth/children                      | Add a child profile                  | Bearer token |
| POST   | /auth/refresh                       | Refresh expired access token         | None         |
| GET    | /lessons/by-level/{level}           | List lessons for a level             | None         |
| GET    | /lessons/{lesson_id}                | Get lesson with vocabulary + quiz    | None         |
| POST   | /lessons/{lesson_id}/complete       | Record completion, award XP          | Bearer token |
| POST   | /conversations/start                | Start AI conversation                | Bearer token |
| POST   | /conversations/{id}/message         | Send message, get AI response        | Bearer token |
| POST   | /conversations/{id}/end             | End chat, calculate XP               | Bearer token |
| GET    | /progress/{child_id}                | Get child progress stats             | Bearer token |
| GET    | /parents/{parent_id}/progress       | Aggregated stats across children     | Bearer token |
| POST   | /tts/speak                          | Synthesize Marathi text to audio     | Bearer token |

## Setup

1. Clone this repo
2. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   SUPABASE_URL=...
   SUPABASE_KEY=...
   SUPABASE_SERVICE_KEY=...
   GROQ_API_KEY=...
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

## Claude Desktop Integration

MarathiMitra can also run as an MCP server inside Claude Desktop:

1. Run `python mcp_server.py` or add to your Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "marathi-tutor": {
         "command": "python",
         "args": ["/path/to/mcp_server.py"],
         "env": {
           "GROQ_API_KEY": "...",
           "SUPABASE_URL": "...",
           "SUPABASE_KEY": "...",
           "SUPABASE_SERVICE_KEY": "..."
         }
       }
     }
   }
   ```
2. Claude gets access to 22 tools (child profiles, lessons, conversations, progress, TTS) and can read skill prompts to act as the Mitra tutor.

## Deployment

- **Frontend:** Deploy `frontend-react/` to Vercel or Netlify — set `VITE_API_BASE_URL` env var to the backend URL
- **Backend:** Deploy to [Render](https://render.com) — start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Project Status

MVP — validating core hypothesis with 5 beta families.
