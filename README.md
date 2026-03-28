# MarathiMitra (मराठीमित्र)

Your child's friendly AI companion for learning spoken Marathi.

## What is this?

MarathiMitra helps diaspora kids (ages 5-12) who understand Marathi but respond in English
to build confidence in spoken Marathi through AI-powered conversations, structured lessons,
and game-based missions.

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend:** Python + FastAPI
- **Database:** Supabase (PostgreSQL + Auth)
- **AI:** Groq API (Llama 3.3 70B)
- **Deployment:** Vercel/Netlify (frontend) + Render (backend)

## Project Structure

```
backend/
  main.py                  # FastAPI app with CORS
  db/
    supabase_client.py     # Supabase client init
    migrations.sql         # Full database schema (run in Supabase SQL Editor)
  models/
    schemas.py             # Pydantic request/response models
  routers/
    auth.py                # Signup, login, child creation
    lessons.py             # Lesson retrieval and completion
    conversations.py       # AI chat management
    progress.py            # Progress tracking
  services/
    mitra.py               # Groq LLM conversation service
    progress.py            # XP/streak calculations
  prompts/
    mitra_system.py        # Mitra personality prompt template
frontend-react/
  src/
    components/            # Navbar, LessonCard, LessonView, ProtectedRoute, shadcn/ui
    contexts/              # AuthContext (token, user, children, activeChild)
    services/              # Axios API client with Bearer token interceptor
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
frontend/                  # Legacy Streamlit frontend (deprecated)
content/
  level1_lessons.json      # Level 1 lesson data (vocabulary + quizzes)
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
| GET    | /lessons/by-level/{level}           | List lessons for a level             | None         |
| GET    | /lessons/{lesson_id}                | Get lesson with vocabulary + quiz    | None         |
| POST   | /lessons/{lesson_id}/complete       | Record completion, award XP          | None         |
| POST   | /conversations/start                | Start AI conversation                | None         |
| POST   | /conversations/{id}/message         | Send message, get AI response        | None         |
| POST   | /conversations/{id}/end             | End chat, calculate XP               | None         |
| GET    | /progress/{child_id}                | Get child progress stats             | None         |
| GET    | /parents/{parent_id}/progress       | Aggregated stats across children     | None         |

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

## Project Status

MVP — validating core hypothesis with 5 beta families.
