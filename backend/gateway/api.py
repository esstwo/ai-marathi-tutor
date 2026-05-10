"""Thin HTTP gateway — maps REST endpoints to skills and connectors.

Auth and CRUD endpoints call connectors directly.
Conversation endpoints use run_skill() for LLM orchestration.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr

from backend.gateway.auth import get_current_parent, verify_child_ownership
from backend.core.skill_loader import load_skills
from backend.core.llm import run_skill, LLMRateLimitError, LLMTimeoutError, LLMAuthError, LLMContentFilterError, LLMServiceError
from backend.core.connector_registry import get_for_skill

# Connectors (direct calls for CRUD)
from backend.connectors.supabase.auth import signup_user, create_parent_record, login_user, refresh_session
from backend.connectors.supabase.children import get_children_by_parent, create_child
from backend.connectors.supabase.lessons import list_lessons, get_lesson_by_id, record_lesson_completion
from backend.connectors.supabase.conversations import (
    start_conversation_record, save_message, get_conversation_messages,
    get_conversation, update_conversation_message_count, end_conversation_record,
)
from backend.services.tts import synthesize_marathi
from backend.gateway.progress_utils import (
    award_lesson_xp, award_conversation_xp, get_child_progress, get_parent_progress,
)

from supabase_auth.errors import AuthApiError

logger = logging.getLogger(__name__)

# Load skills once at import time
_skills = load_skills()
conversation_skill = _skills["marathi_conversation_partner"]

MAX_HISTORY = 10


# ── Request/Response schemas ────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChildCreateRequest(BaseModel):
    name: str
    age: int
    avatar: str = "\U0001f418"

class RefreshRequest(BaseModel):
    refresh_token: str

class StartConversationRequest(BaseModel):
    child_id: str

class SendMessageRequest(BaseModel):
    message: str

class TTSRequest(BaseModel):
    text: str

class LessonCompleteRequest(BaseModel):
    child_id: str
    score: int


# ── Auth routes ─────────────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup")
def signup(req: SignupRequest):
    try:
        auth_response = signup_user(req.email, req.password)
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if auth_response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_response.user.id
    parent = create_parent_record(user_id, req.email, req.name)

    if not parent:
        raise HTTPException(status_code=500, detail="Failed to create parent record")

    access_token = None
    refresh_token = None
    if auth_response.session:
        access_token = auth_response.session.access_token
        refresh_token = auth_response.session.refresh_token

    return {
        "message": "Signup successful",
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "parent": parent,
    }


@auth_router.post("/login")
def login(req: LoginRequest):
    try:
        auth_response = login_user(req.email, req.password)
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if auth_response.user is None or auth_response.session is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = auth_response.user.id
    children = get_children_by_parent(user_id)

    return {
        "message": "Login successful",
        "user_id": user_id,
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
        "children": children,
    }


@auth_router.post("/children")
def create_child_endpoint(req: ChildCreateRequest, parent_id: str = Depends(get_current_parent)):
    if not 5 <= req.age <= 12:
        raise HTTPException(status_code=400, detail="Age must be between 5 and 12")

    child = create_child(parent_id, req.name, req.age, req.avatar)
    if not child:
        raise HTTPException(status_code=500, detail="Failed to create child")

    return {"message": "Child created", "child": child}


@auth_router.post("/refresh")
def refresh(req: RefreshRequest):
    try:
        auth_response = refresh_session(req.refresh_token)
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if auth_response.session is None:
        raise HTTPException(status_code=401, detail="Failed to refresh session")

    return {
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
    }


# ── Lesson routes ───────────────────────────────────────────────────────

lessons_router = APIRouter(prefix="/lessons", tags=["lessons"])


@lessons_router.get("/by-level/{level}")
def list_lessons_by_level(level: int):
    return list_lessons(level)


@lessons_router.get("/{lesson_id}")
def get_lesson(lesson_id: str):
    result = get_lesson_by_id(lesson_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return result


@lessons_router.post("/{lesson_id}/complete")
def complete_lesson(lesson_id: str, req: LessonCompleteRequest, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(req.child_id, parent_id)
    record_lesson_completion(req.child_id, lesson_id, req.score)
    xp_result = award_lesson_xp(req.child_id)

    return {
        "message": "Lesson completed",
        "score": req.score,
        "xp_earned": xp_result["xp_earned"],
        "xp_total": xp_result["xp_total"],
        "streak_days": xp_result["streak_days"],
    }


# ── Conversation routes (LLM-driven via run_skill) ─────────────────────

conversations_router = APIRouter(prefix="/conversations", tags=["conversations"])


def _handle_llm_errors(fn):
    """Decorator to map LLM errors to HTTP status codes."""
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except LLMRateLimitError as e:
            raise HTTPException(status_code=429, detail=str(e))
        except LLMTimeoutError as e:
            raise HTTPException(status_code=504, detail=str(e))
        except LLMAuthError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except LLMContentFilterError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except LLMServiceError as e:
            raise HTTPException(status_code=502, detail=str(e))
    wrapper.__name__ = fn.__name__
    return wrapper


@conversations_router.post("/start")
@_handle_llm_errors
async def start_conversation(req: StartConversationRequest, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(req.child_id, parent_id)

    conv = start_conversation_record(req.child_id)
    if not conv:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    conversation_id = conv["id"]
    connectors = get_for_skill(conversation_skill.connector_names)

    # Run the conversation skill for greeting
    messages = [
        {
            "role": "user",
            "content": (
                f"[SYSTEM: The child (child_id: {req.child_id}) just opened the chat. "
                "First use your tools to learn about them, then "
                "greet them warmly by name in Marathi and invite them to start talking. "
                "Keep it to 1-2 short sentences. Respond as JSON.]"
            ),
        },
    ]
    result = run_skill(conversation_skill, messages, connectors)

    save_message(conversation_id, "mitra", result["marathi_text"])
    update_conversation_message_count(conversation_id, 1)

    return {
        "conversation_id": conversation_id,
        "marathi_text": result["marathi_text"],
        "english_hint": result.get("english_hint"),
    }


@conversations_router.post("/{conversation_id}/message")
@_handle_llm_errors
async def send_message(conversation_id: str, req: SendMessageRequest, parent_id: str = Depends(get_current_parent)):
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    child_id = conv["child_id"]
    verify_child_ownership(child_id, parent_id)
    current_count = conv["message_count"] or 0

    save_message(conversation_id, "child", req.message)

    history_rows = get_conversation_messages(conversation_id)
    connectors = get_for_skill(conversation_skill.connector_names)

    # Build messages from conversation history
    messages = []
    for msg in history_rows[-MAX_HISTORY:]:
        role = "assistant" if msg["role"] == "mitra" else "user"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    # Append child_id to system prompt so tools can use it
    skill_with_context = conversation_skill
    original_prompt = conversation_skill.system_prompt
    conversation_skill.system_prompt = original_prompt + f"\n\nThe child's ID is: {child_id}"

    result = run_skill(conversation_skill, messages, connectors)

    # Restore original prompt
    conversation_skill.system_prompt = original_prompt

    save_message(conversation_id, "mitra", result["marathi_text"])
    update_conversation_message_count(conversation_id, current_count + 2)

    return {
        "marathi_text": result["marathi_text"],
        "english_hint": result.get("english_hint"),
    }


@conversations_router.post("/{conversation_id}/end")
async def end_conversation(conversation_id: str, parent_id: str = Depends(get_current_parent)):
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    verify_child_ownership(conv["child_id"], parent_id)

    if conv.get("ended_at"):
        return {"message": "Conversation already ended"}

    now = datetime.now(timezone.utc).isoformat()
    end_conversation_record(conversation_id, now)
    xp_result = award_conversation_xp(conv["child_id"], conversation_id)

    return {
        "message": "Conversation ended",
        "xp_earned": xp_result["xp_earned"],
        "xp_total": xp_result["xp_total"],
        "streak_days": xp_result["streak_days"],
        "duration_minutes": xp_result["duration_minutes"],
    }


# ── Progress routes ─────────────────────────────────────────────────────

progress_router = APIRouter(tags=["progress"])


@progress_router.get("/progress/{child_id}")
def child_progress(child_id: str, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(child_id, parent_id)
    return get_child_progress(child_id)


@progress_router.get("/parents/{parent_id}/progress")
def parent_progress(parent_id: str, current_parent_id: str = Depends(get_current_parent)):
    if parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return get_parent_progress(parent_id)


# ── TTS route ───────────────────────────────────────────────────────────

tts_router = APIRouter(prefix="/tts", tags=["tts"])


@tts_router.post("/speak")
def speak(req: TTSRequest, _parent_id: str = Depends(get_current_parent)):
    if not req.text or len(req.text) > 200:
        raise HTTPException(400, "Text must be 1-200 characters")
    audio_bytes = synthesize_marathi(req.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")


# ── Collect all routers ─────────────────────────────────────────────────

all_routers = [auth_router, lessons_router, conversations_router, progress_router, tts_router]
