import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.routers import auth, lessons, conversations, progress, tts

load_dotenv()

app = FastAPI(title="MarathiMitra API")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://localhost:5173",  # Streamlit + React dev
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(lessons.router)
app.include_router(conversations.router)
app.include_router(progress.router)
app.include_router(tts.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
