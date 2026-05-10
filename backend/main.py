import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.gateway.api import all_routers

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

for router in all_routers:
    app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
