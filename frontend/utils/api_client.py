"""FastAPI client wrapper — centralizes all backend API calls."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _headers(token: str | None = None) -> dict:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def signup(name: str, email: str, password: str) -> dict:
    res = requests.post(
        f"{API_BASE_URL}/auth/signup",
        json={"name": name, "email": email, "password": password},
    )
    res.raise_for_status()
    return res.json()


def login(email: str, password: str) -> dict:
    res = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password},
    )
    res.raise_for_status()
    return res.json()


def create_child(name: str, age: int, avatar: str, token: str) -> dict:
    res = requests.post(
        f"{API_BASE_URL}/auth/children",
        json={"name": name, "age": age, "avatar": avatar},
        headers=_headers(token),
    )
    res.raise_for_status()
    return res.json()


def list_lessons(level: int) -> list[dict]:
    res = requests.get(f"{API_BASE_URL}/lessons/by-level/{level}")
    res.raise_for_status()
    return res.json()


def get_lesson(lesson_id: str) -> dict:
    res = requests.get(f"{API_BASE_URL}/lessons/{lesson_id}")
    res.raise_for_status()
    return res.json()


def complete_lesson(lesson_id: str, child_id: str, score: int) -> dict:
    res = requests.post(
        f"{API_BASE_URL}/lessons/{lesson_id}/complete",
        json={"child_id": child_id, "score": score},
    )
    res.raise_for_status()
    return res.json()


def start_conversation(child_id: str) -> dict:
    res = requests.post(
        f"{API_BASE_URL}/conversations/start",
        json={"child_id": child_id},
    )
    res.raise_for_status()
    return res.json()


def send_message(conversation_id: str, message: str) -> dict:
    res = requests.post(
        f"{API_BASE_URL}/conversations/{conversation_id}/message",
        json={"message": message},
    )
    res.raise_for_status()
    return res.json()


def end_conversation(conversation_id: str) -> dict:
    res = requests.post(f"{API_BASE_URL}/conversations/{conversation_id}/end")
    res.raise_for_status()
    return res.json()


def get_progress(child_id: str) -> dict:
    res = requests.get(f"{API_BASE_URL}/progress/{child_id}")
    res.raise_for_status()
    return res.json()
