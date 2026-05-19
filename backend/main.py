import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.gateway.api import all_routers

load_dotenv()

# Surface our INFO-level logs (LLM calls, guardrails, digest) through uvicorn's
# stderr. Without this, Python's default root level (WARNING) drops them silently.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="MarathiMitra API")

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://localhost:5173",  # Streamlit + React dev
)
# Strip whitespace and drop empties so the env var tolerates "a, b, c" formatting.
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in _raw_origins.split(",") if o.strip()]
print(f"[cors] allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
