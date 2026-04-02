# MarathiMitra (मराठीमित्र)

Your child's friendly AI companion for learning spoken Marathi.

## What is this?

MarathiMitra helps diaspora kids (ages 5-12) who understand Marathi but respond in English
to build confidence in spoken Marathi through AI-powered conversations, structured lessons,
and game-based missions.

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend:** Python + FastAPI + FastMCP (Model Context Protocol)
- **Database:** Supabase (PostgreSQL + Auth)
- **AI:** Groq API (Llama 3.3 70B)
- **TTS:** Google Cloud Text-to-Speech (Marathi)
- **Deployment:** Vercel (frontend) + Render (backend)

## Project Structure

```
backend/
  main.py                  # FastAPI app with CORS
  db/
    supabase_client.py     # Supabase client init
    migrations.sql         # Full database schema (run in Supabase SQL Editor)
  mcp/                     # MCP (Model Context Protocol) layer
    supabase_tools.py      # All Supabase operations as standalone functions
    supabase_server.py     # FastMCP server (19 tools registered)
    tts_tools.py           # TTS tool with base64 encoding
    tts_server.py          # FastMCP server (1 tool registered)
    client.py              # Async MCP client helper for in-process calls
  skills/
    mitra_conversation.py  # Mitra conversation skill (prompt building, LLM calls, response parsing)
  models/
    schemas.py             # Pydantic request/response models
  routers/
    auth.py                # Signup, login, child creation, token refresh
    lessons.py             # Lesson retrieval and completion
    conversations.py       # AI chat management
    progress.py            # Progress tracking
    tts.py                 # Text-to-speech endpoint
  services/
    mitra.py               # Re-exports from skills/mitra_conversation.py
    progress.py            # XP/streak calculations (async, calls MCP tools)
    tts.py                 # Google Cloud TTS wrapper with caching
    llm_errors.py          # LLM exception hierarchy
  dependencies/
    auth.py                # Token validation + child ownership checks
  prompts/
    mitra_system.py        # Mitra personality prompt template
frontend-react/
  src/
    components/            # Navbar, LessonCard, LessonView, ProtectedRoute, shadcn/ui
    contexts/              # AuthContext (token + refresh token management)
    services/              # Axios API client with Bearer token + 401 refresh interceptor
    types/                 # TypeScript interfaces matching backend schemas
    pages/
      Index.tsx            # Landing page
      Login.tsx            # Sign in / sign up
      ChildSetup.tsx       # Child profile creation + selection
      Home.tsx             # Dashboard with stats + quick actions
      Lessons.tsx          # Lesson browser with level selector
      Chats.tsx            # AI conversation with Mitra
      Progress.tsx         # Child progress + level roadmap
      ParentProgress.tsx   # Parent aggregated dashboard
content/
  level1_lessons.json      # Level 1 lesson data (vocabulary + quizzes)
  level2_lessons.json      # Level 2 lesson data
scripts/
  seed_content.py          # Seed lessons into Supabase
```

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

## Deployment

- **Frontend:** Deploy `frontend-react/` to Vercel or Netlify — set `VITE_API_BASE_URL` env var to the backend URL
- **Backend:** Deploy to [Render](https://render.com) — start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Architecture

The backend uses a **plugin architecture** based on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io):

- **MCP Servers** (`backend/mcp/`) — all database operations and TTS are registered as MCP tools via FastMCP, callable by any MCP client
- **Skills** (`backend/skills/`) — portable intelligence (prompt building, LLM interaction, response parsing) separated from plumbing
- **Gateway** (routers) — thin HTTP layer that calls MCP tools via an async in-process client

This separation means the same tools can later be called by Claude Desktop, other LLM apps, or deployed as standalone MCP services.

## Project Status

MVP — validating core hypothesis with 5 beta families.
