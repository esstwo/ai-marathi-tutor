# MarathiMitra (मराठीमित्र)

Your child's friendly AI companion for learning spoken Marathi.

## What is this?

MarathiMitra helps diaspora kids (ages 5-12) who understand Marathi but respond in English
to build confidence in spoken Marathi through AI-powered conversations, structured lessons,
and game-based missions.

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python + FastAPI
- **Database:** Supabase (PostgreSQL + Auth)
- **AI:** Groq API
- **Deployment:** Streamlit Cloud (frontend) + Render (backend)

## Project Structure

```
backend/
  main.py                  # FastAPI app with CORS
  db/
    supabase_client.py     # Supabase client init
    migrations.sql         # Full database schema (run in Supabase SQL Editor)
  models/
    schemas.py             # Pydantic request models
  routers/
    auth.py                # POST /auth/signup
    children.py            # POST /children
frontend/
  app.py                   # Streamlit app (signup + child setup flow)
content/
  level1_lessons.json      # Level 1 lesson data (vocabulary + quizzes)
scripts/
  seed_content.py          # Seed lessons into Supabase
```

## API Endpoints

| Method | Path           | Description                        | Auth     |
|--------|----------------|------------------------------------|----------|
| GET    | /health        | Health check                       | None     |
| POST   | /auth/signup   | Create account (email, password, name) | None |
| POST   | /children      | Add a child profile (name, age, avatar) | Bearer token |

## Setup

1. Clone this repo
2. Copy `.env.example` to `.env` and fill in your API keys
3. Install dependencies: `pip install -r requirements.txt`
4. Run the database migration: apply `backend/db/migrations.sql` in Supabase SQL Editor
5. Seed lesson content: `python -m scripts.seed_content`
6. Start backend: `uvicorn backend.main:app --reload`
7. Start frontend: `streamlit run frontend/app.py`

## Deployment

- **Frontend:** Deploy to [Streamlit Cloud](https://share.streamlit.io) — point main file to `frontend/app.py`
- **Backend:** Deploy to [Render](https://render.com) — start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Set `API_BASE_URL` in Streamlit secrets to point the frontend at the Render backend

## Project Status

MVP — validating core hypothesis with 5 beta families.
