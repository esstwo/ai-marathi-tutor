"""Thin HTTP gateway — maps REST endpoints to skills and connectors.

Auth and CRUD endpoints call connectors directly.
Conversation endpoints use run_skill() for LLM orchestration.
"""

import logging
from datetime import datetime, timezone
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr

from backend.gateway.auth import get_current_parent, verify_child_ownership, SERVICE_MODE_PARENT
from backend.gateway.guardrails import (
    validate_message_input, validate_llm_output,
    check_message_limit, check_conversation_duration, check_concurrent_conversations,
    track_llm_call, track_child_llm_call, flag_conversation,
    check_signup_rate_limit, get_request_ip,
)
from backend.core.skill_loader import load_skills
from backend.core.llm import run_skill, LLMRateLimitError, LLMTimeoutError, LLMAuthError, LLMContentFilterError, LLMServiceError
from backend.core.connector_registry import get_for_skill

# Connectors (direct calls for CRUD)
from backend.connectors.supabase.auth import signup_user, create_parent_record, login_user, refresh_session
from backend.connectors.supabase.children import get_children_by_parent, create_child, get_child_profile
from backend.connectors.supabase.lessons import list_lessons, get_lesson_by_id, record_lesson_completion
from backend.connectors.supabase.conversations import (
    start_conversation_record, save_message, get_conversation_messages,
    get_conversation, update_conversation_message_count, end_conversation_record,
)
from backend.db.supabase_client import supabase_admin
from backend.services.tts import synthesize_marathi
from backend.gateway.progress_utils import (
    award_lesson_xp, award_conversation_xp, award_mission_xp,
    get_child_progress, get_parent_progress,
)
from backend.connectors.supabase.missions import (
    list_missions as list_missions_db, get_mission_by_id, create_mission,
    get_child_mission_progress, upsert_mission_progress,
)

from supabase_auth.errors import AuthApiError

logger = logging.getLogger(__name__)

# Load skills once at import time
_skills = load_skills()
conversation_skill = _skills["marathi_conversation_partner"]
mission_generator_skill = _skills["mission_generator"]
mission_guide_skill = _skills["marathi_mission_guide"]

MAX_HISTORY = 10


# ── Request/Response schemas ────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    captcha_token: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str | None = None

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

class GenerateMissionRequest(BaseModel):
    child_id: str
    level: int
    topic: str | None = None  # Optional theme the parent/child wants the mission to be about

class StartMissionRequest(BaseModel):
    child_id: str
    mission_id: str

class SendMissionMessageRequest(BaseModel):
    message: str


# ── Auth routes ─────────────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup")
def signup(req: SignupRequest, request: Request):
    check_signup_rate_limit(get_request_ip(request))

    try:
        auth_response = signup_user(req.email, req.password, captcha_token=req.captcha_token)
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if auth_response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_response.user.id
    parent = create_parent_record(user_id, req.email, req.name)

    if not parent:
        raise HTTPException(status_code=500, detail="Failed to create parent record")

    # When Supabase "Confirm email" is enabled, sign_up returns a user but no
    # session — the user must click the verification link before logging in.
    if auth_response.session is None:
        return {
            "message": "Please check your email to verify your account before signing in.",
            "user_id": user_id,
            "email_verification_required": True,
            "parent": parent,
        }

    return {
        "message": "Signup successful",
        "user_id": user_id,
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
        "email_verification_required": False,
        "parent": parent,
    }


@auth_router.post("/login")
def login(req: LoginRequest):
    try:
        auth_response = login_user(req.email, req.password, captcha_token=req.captcha_token)
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
    @wraps(fn)
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
    return wrapper


@conversations_router.post("/start")
@_handle_llm_errors
async def start_conversation(req: StartConversationRequest, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(req.child_id, parent_id)
    check_concurrent_conversations(req.child_id, supabase_admin)
    track_llm_call()
    track_child_llm_call(req.child_id)

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
    result = validate_llm_output(result)

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

    # Session guardrails
    current_count = conv["message_count"] or 0
    check_message_limit(current_count)
    check_conversation_duration(conv["started_at"])

    # Input guardrails
    clean_message = validate_message_input(req.message)

    # Cost protection
    track_llm_call()
    track_child_llm_call(child_id)

    save_message(conversation_id, "child", clean_message)

    history_rows = get_conversation_messages(conversation_id)
    connectors = get_for_skill(conversation_skill.connector_names)

    # Build messages from conversation history
    messages = []
    for msg in history_rows[-MAX_HISTORY:]:
        role = "assistant" if msg["role"] == "mitra" else "user"
        messages.append({"role": role, "content": msg["content"]})
    # JSON reminder appended to the child's message (not saved) — saved assistant
    # history is plain marathi_text, so without this the model can drift into
    # plain-text replies that break the JSON contract.
    messages.append({
        "role": "user",
        "content": (
            f"{clean_message}\n\n"
            "[Reply as a single JSON object: "
            "{\"marathi_text\":\"...\",\"english_hint\":\"...\"}. No prose outside the JSON.]"
        ),
    })

    # Append child_id to system prompt so tools can use it
    original_prompt = conversation_skill.system_prompt
    conversation_skill.system_prompt = original_prompt + f"\n\nThe child's ID is: {child_id}"

    result = run_skill(conversation_skill, messages, connectors)

    # Restore original prompt
    conversation_skill.system_prompt = original_prompt

    # Output guardrails
    result = validate_llm_output(result)

    # Flag if output was sanitized
    if result.get("_flagged"):
        flag_conversation(conversation_id, "LLM output contained PII/URLs — sanitized", supabase_admin)

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
    if current_parent_id != SERVICE_MODE_PARENT and parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return get_parent_progress(parent_id)


@progress_router.get("/parents/{parent_id}/flags")
def parent_flags(parent_id: str, current_parent_id: str = Depends(get_current_parent)):
    """Get safety flags for all conversations belonging to this parent's children."""
    if current_parent_id != SERVICE_MODE_PARENT and parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    children = get_children_by_parent(parent_id)
    child_ids = [c["id"] for c in children]
    if not child_ids:
        return []
    conversations = (
        supabase_admin.table("conversations")
        .select("id")
        .in_("child_id", child_ids)
        .execute()
    )
    conv_ids = [c["id"] for c in (conversations.data or [])]
    if not conv_ids:
        return []
    flags = (
        supabase_admin.table("conversation_flags")
        .select("*")
        .in_("conversation_id", conv_ids)
        .order("flagged_at", desc=True)
        .execute()
    )
    return flags.data or []


# ── TTS route ───────────────────────────────────────────────────────────

tts_router = APIRouter(prefix="/tts", tags=["tts"])


@tts_router.post("/speak")
def speak(req: TTSRequest, _parent_id: str = Depends(get_current_parent)):
    if not req.text or len(req.text) > 200:
        raise HTTPException(400, "Text must be 1-200 characters")
    audio_bytes = synthesize_marathi(req.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@tts_router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), _parent_id: str = Depends(get_current_parent)):
    """Transcribe audio to Marathi text using Groq Whisper."""
    import os
    from groq import Groq

    audio_bytes = await audio.read()
    if len(audio_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(400, "Audio file too large (max 10MB)")

    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    try:
        transcription = groq_client.audio.transcriptions.create(
            file=(audio.filename or "audio.webm", audio_bytes),
            model="whisper-large-v3",
            language="mr",
            response_format="text",
        )
        return {"text": transcription.strip() if isinstance(transcription, str) else transcription.text.strip()}
    except Exception as e:
        logger.warning("Groq transcription failed: %s", e)
        raise HTTPException(500, "Transcription failed")


# ── Mission routes (LLM-generated, shared, scenario-based challenges) ──

missions_router = APIRouter(prefix="/missions", tags=["missions"])


def _build_mission_context(child: dict, mission: dict) -> str:
    """Render the child + mission data the mission_guide skill needs as a single
    block to append to the system prompt. Replaces tool calls — we already have
    this data in the gateway, so making the LLM fetch it again is pure overhead
    (and was the source of empty responses when Sarvam's tool loop didn't terminate)."""
    import json as _json
    steps = mission.get("steps") or []
    steps_lines = []
    for s in steps:
        if not isinstance(s, dict):
            continue
        step_num = s.get("step")
        prompt = s.get("prompt", "")
        target_vocab = s.get("target_vocab") or []
        steps_lines.append(
            f"  Step {step_num}: {prompt}"
            + (f" (target vocab: {', '.join(target_vocab)})" if target_vocab else "")
        )
    steps_block = "\n".join(steps_lines) if steps_lines else "  (no steps defined)"

    return (
        f"\n\n## Mission Context (already loaded — do NOT call tools)\n"
        f"Child: {child.get('name', '?')} (age {child.get('age', '?')}, level {child.get('current_level', '?')})\n"
        f"Mission title: {mission.get('title', '?')} ({mission.get('title_english', '')})\n"
        f"Scenario: {mission.get('scenario', '')}\n"
        f"Total steps: {len(steps)}\n"
        f"Steps:\n{steps_block}\n"
        f"Required vocab: {', '.join(mission.get('required_vocab') or [])}\n"
    )


@missions_router.get("/by-level/{level}")
def list_missions_by_level(level: int, _parent_id: str = Depends(get_current_parent)):
    return list_missions_db(level)


@missions_router.get("/progress/{child_id}")
def mission_progress(child_id: str, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(child_id, parent_id)
    return get_child_mission_progress(child_id)


@missions_router.post("/generate")
@_handle_llm_errors
async def generate_mission(req: GenerateMissionRequest, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(req.child_id, parent_id)
    if not 1 <= req.level <= 4:
        raise HTTPException(400, "Level must be between 1 and 4")

    track_llm_call()
    track_child_llm_call(req.child_id)

    # Gather vocabulary from all lessons at this level
    level_lessons = list_lessons(req.level)
    vocab_items = []
    for lesson in level_lessons:
        vocab = lesson.get("vocabulary") or []
        if isinstance(vocab, list):
            vocab_items.extend(vocab)

    import json
    vocab_context = json.dumps(vocab_items, ensure_ascii=False) if vocab_items else "[]"

    # Sandwich the topic between header and footer so it survives attention
    # drift through the (potentially huge) vocab list in the middle.
    if req.topic:
        header = (
            f"=== MISSION TOPIC: {req.topic} ===\n\n"
            f"Generate a Level {req.level} Marathi mission that is entirely about: {req.topic}\n"
            f"Every step must directly involve this exact scenario. Do not substitute a similar one."
        )
        footer = (
            f"REMINDER: This mission MUST be about \"{req.topic}\". "
            f"Only use vocabulary above that fits naturally with that scenario — "
            f"do not force unrelated words. If the vocabulary doesn't have a perfect "
            f"match for some words you need, use simple Marathi words a kid would know.\n\n"
            f"Respond as a JSON object."
        )
    else:
        header = (
            f"Generate a Level {req.level} Marathi mission.\n"
            f"Choose a creative, culturally relevant scenario from the variety suggestions in your instructions."
        )
        footer = "Respond as a JSON object."

    messages = [
        {
            "role": "user",
            "content": (
                f"{header}\n\n"
                f"Available vocabulary you may draw from:\n{vocab_context}\n\n"
                f"{footer}"
            ),
        },
    ]
    connectors = get_for_skill(mission_generator_skill.connector_names)
    result = run_skill(mission_generator_skill, messages, connectors)

    # Validate the LLM produced a real mission — without this, a parser
    # fallback (Sarvam doesn't enforce JSON) would silently persist an empty
    # mission with no scenario/steps that the mission_guide can't actually play.
    title = result.get("title")
    scenario = result.get("scenario")
    steps = result.get("steps")
    if not title or not scenario or not isinstance(steps, list) or len(steps) == 0:
        logger.warning(
            "Mission generation produced incomplete output — title=%r, scenario=%r, steps=%r. Raw LLM output: %s",
            title, scenario, steps, (result.get("raw") or "")[:500],
        )
        raise HTTPException(
            status_code=502,
            detail="Couldn't generate a mission this time — please try again with a different topic or in a moment.",
        )

    mission = create_mission(
        level=req.level,
        title=title,
        title_english=result.get("title_english", title),
        scenario=scenario,
        steps=steps,
        required_vocab=result.get("required_vocab", []),
        xp_reward=result.get("xp_reward", 25),
    )

    return mission


@missions_router.post("/start")
@_handle_llm_errors
async def start_mission(req: StartMissionRequest, parent_id: str = Depends(get_current_parent)):
    verify_child_ownership(req.child_id, parent_id)
    check_concurrent_conversations(req.child_id, supabase_admin)
    track_llm_call()
    track_child_llm_call(req.child_id)

    mission = get_mission_by_id(req.mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")

    # Create a conversation linked to this mission
    import json
    conv = start_conversation_record(req.child_id)
    if not conv:
        raise HTTPException(500, "Failed to create conversation")

    conversation_id = conv["id"]
    # Store mission_id in conversation context
    supabase_admin.table("conversations").update(
        {"context": json.dumps({"mission_id": req.mission_id})}
    ).eq("id", conversation_id).execute()

    # Mark mission as in_progress
    upsert_mission_progress(req.child_id, req.mission_id, "in_progress")

    child = get_child_profile(req.child_id) or {}
    total_steps = len(mission.get("steps") or [])

    # Inject mission + child context directly into the prompt so the LLM doesn't
    # need to make any tool calls just to know who/what it's playing.
    original_prompt = mission_guide_skill.system_prompt
    mission_guide_skill.system_prompt = original_prompt + _build_mission_context(child, mission)

    messages = [
        {
            "role": "user",
            "content": (
                "The child just opened this mission. "
                "Set the scene — introduce the scenario in character based on the Mission Context above, "
                "and prompt the child for Step 1. "
                "Respond as JSON with mission_step=1, mission_complete=false, step_score=0."
            ),
        },
    ]
    try:
        result = run_skill(mission_guide_skill, messages, connectors={})
    finally:
        mission_guide_skill.system_prompt = original_prompt
    result = validate_llm_output(result)

    save_message(conversation_id, "mitra", result["marathi_text"])
    update_conversation_message_count(conversation_id, 1)

    return {
        "conversation_id": conversation_id,
        "marathi_text": result["marathi_text"],
        "english_hint": result.get("english_hint"),
        "mission_step": result.get("mission_step", 1),
        "total_steps": total_steps,
    }


@missions_router.post("/{conversation_id}/message")
@_handle_llm_errors
async def send_mission_message(
    conversation_id: str, req: SendMissionMessageRequest, parent_id: str = Depends(get_current_parent)
):
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")

    child_id = conv["child_id"]
    verify_child_ownership(child_id, parent_id)

    # Extract mission_id from conversation context
    import json
    context = {}
    if conv.get("context"):
        try:
            context = json.loads(conv["context"]) if isinstance(conv["context"], str) else conv["context"]
        except (json.JSONDecodeError, TypeError):
            pass
    mission_id = context.get("mission_id")
    if not mission_id:
        raise HTTPException(400, "This conversation is not a mission")

    mission = get_mission_by_id(mission_id)
    total_steps = len(mission.get("steps") or []) if mission else 5

    # Session guardrails
    current_count = conv["message_count"] or 0
    check_message_limit(current_count)
    check_conversation_duration(conv["started_at"])

    # Input guardrails
    clean_message = validate_message_input(req.message)
    track_llm_call()
    track_child_llm_call(child_id)

    save_message(conversation_id, "child", clean_message)

    history_rows = get_conversation_messages(conversation_id)
    child = get_child_profile(child_id) or {}

    messages = []
    for msg in history_rows[-MAX_HISTORY:]:
        role = "assistant" if msg["role"] == "mitra" else "user"
        messages.append({"role": role, "content": msg["content"]})
    # Append a JSON reminder to the child's message before sending to the LLM —
    # the saved assistant history only contains marathi_text (not the JSON wrapper),
    # so without this nudge the model mirrors the plain-text pattern and skips JSON.
    # The reminder is NOT saved to the conversation history shown in the UI.
    messages.append({
        "role": "user",
        "content": (
            f"{clean_message}\n\n"
            "[Reply as a single JSON object: "
            "{\"marathi_text\":\"...\",\"english_hint\":\"...\",\"mission_step\":<int>,"
            "\"mission_complete\":<bool>,\"step_score\":<0-3>}. No prose outside the JSON.]"
        ),
    })

    # Inject mission + child context — same pattern as start_mission, no tool calls needed
    original_prompt = mission_guide_skill.system_prompt
    mission_guide_skill.system_prompt = original_prompt + _build_mission_context(child, mission)

    try:
        result = run_skill(mission_guide_skill, messages, connectors={})
    finally:
        mission_guide_skill.system_prompt = original_prompt

    # Output guardrails
    result = validate_llm_output(result)

    if result.get("_flagged"):
        flag_conversation(conversation_id, "LLM output contained PII/URLs — sanitized", supabase_admin)

    save_message(conversation_id, "mitra", result["marathi_text"])
    update_conversation_message_count(conversation_id, current_count + 2)

    mission_complete = result.get("mission_complete", False)
    step_score = result.get("step_score", 1)
    mission_step = result.get("mission_step", 1)

    # If mission is complete, calculate final score and award XP
    xp_result = None
    if mission_complete and mission_id:
        # Calculate aggregate score from step_scores in conversation history
        scores = []
        for msg in history_rows:
            if msg["role"] == "mitra":
                try:
                    parsed = json.loads(msg["content"])
                    if "step_score" in parsed:
                        scores.append(parsed["step_score"])
                except (json.JSONDecodeError, TypeError):
                    pass
        scores.append(step_score)  # Include current step
        avg_score = sum(scores) / len(scores) if scores else 1
        final_score = round(avg_score / 3 * 100)  # Scale 0-3 to 0-100

        upsert_mission_progress(child_id, mission_id, "completed", final_score)

        # End the conversation
        now = datetime.now(timezone.utc).isoformat()
        end_conversation_record(conversation_id, now)

        xp_result = award_mission_xp(child_id, mission_id, final_score)

    response = {
        "marathi_text": result["marathi_text"],
        "english_hint": result.get("english_hint"),
        "mission_step": mission_step,
        "mission_complete": mission_complete,
        "step_score": step_score,
        "total_steps": total_steps,
    }

    if xp_result:
        response["xp_earned"] = xp_result["xp_earned"]
        response["xp_total"] = xp_result["xp_total"]
        response["score"] = xp_result["score"]

    return response


@missions_router.post("/{conversation_id}/end")
async def end_mission(conversation_id: str, parent_id: str = Depends(get_current_parent)):
    """End a mission early (quit). No XP awarded."""
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")

    verify_child_ownership(conv["child_id"], parent_id)

    if conv.get("ended_at"):
        return {"message": "Mission already ended"}

    now = datetime.now(timezone.utc).isoformat()
    end_conversation_record(conversation_id, now)

    # Reset mission progress
    import json
    context = {}
    if conv.get("context"):
        try:
            context = json.loads(conv["context"]) if isinstance(conv["context"], str) else conv["context"]
        except (json.JSONDecodeError, TypeError):
            pass
    mission_id = context.get("mission_id")
    if mission_id:
        upsert_mission_progress(conv["child_id"], mission_id, "not_started", 0)

    return {"message": "Mission ended", "xp_earned": 0}


# ── Digest routes ──────────────────────────────────────────────────────

digest_router = APIRouter(prefix="/digest", tags=["digest"])

from backend.services.digest import build_parent_digest, generate_digest_text, send_all_digests


@digest_router.post("/send")
def send_digests(_parent_id: str = Depends(get_current_parent)):
    """Trigger weekly digests for all parents. Service-key only."""
    if _parent_id != SERVICE_MODE_PARENT:
        raise HTTPException(status_code=403, detail="Service key required")
    return send_all_digests()


@digest_router.get("/preview/{parent_id}")
def preview_digest(parent_id: str, current_parent_id: str = Depends(get_current_parent)):
    """Preview the digest for a parent without sending it. For testing."""
    if current_parent_id != SERVICE_MODE_PARENT and parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    data = build_parent_digest(parent_id)
    if not data:
        raise HTTPException(status_code=404, detail="No children found for this parent")

    # Fetch parent name for the preview
    parent_row = (
        supabase_admin.table("parents")
        .select("name, email")
        .eq("id", parent_id)
        .single()
        .execute()
    )
    parent = parent_row.data or {}

    digest_text = generate_digest_text(parent.get("name") or "there", data["children_stats"])
    return {
        "to": parent.get("email"),
        "children_stats": data["children_stats"],
        "digest_text": digest_text,
    }


# ── Collect all routers ─────────────────────────────────────────────────

all_routers = [auth_router, lessons_router, conversations_router, progress_router, tts_router, missions_router, digest_router]
