"""Supabase MCP tools — all database operations as standalone functions.

Each function takes simple inputs (IDs, strings) and returns dicts.
No HTTP concerns — callers handle error-to-status mapping.
"""

from datetime import datetime, timezone

from backend.db.supabase_client import supabase, supabase_admin


# ── Child operations ──────────────────────────────────────────────────

def get_child_profile(child_id: str) -> dict | None:
    """Fetch full child profile (merged columns for all callers)."""
    result = (
        supabase_admin.table("children")
        .select("name, age, current_level, xp_total, streak_days, streak_last_date")
        .eq("id", child_id)
        .single()
        .execute()
    )
    return result.data


def get_children_by_parent(parent_id: str) -> list[dict]:
    """Fetch all children belonging to a parent."""
    result = (
        supabase_admin.table("children")
        .select("id, name, age, avatar, current_level, xp_total, streak_days")
        .eq("parent_id", parent_id)
        .execute()
    )
    return result.data or []


def create_child(parent_id: str, name: str, age: int, avatar: str = "\U0001f418") -> dict | None:
    """Insert a new child record."""
    result = (
        supabase_admin.table("children")
        .insert({
            "parent_id": parent_id,
            "name": name,
            "age": age,
            "avatar": avatar,
        })
        .execute()
    )
    return result.data[0] if result.data else None


def update_child_stats(child_id: str, xp_total: int, streak_days: int, streak_last_date: str) -> None:
    """Update XP and streak fields on a child record."""
    supabase_admin.table("children").update(
        {
            "xp_total": xp_total,
            "streak_days": streak_days,
            "streak_last_date": streak_last_date,
        }
    ).eq("id", child_id).execute()


def verify_child_belongs_to_parent(child_id: str, parent_id: str) -> bool:
    """Check if a child belongs to a parent. Returns bool (no HTTP concern)."""
    result = (
        supabase_admin.table("children")
        .select("id")
        .eq("id", child_id)
        .eq("parent_id", parent_id)
        .execute()
    )
    return bool(result.data)


# ── Auth operations (use anon supabase client) ────────────────────────

def signup_user(email: str, password: str):
    """Sign up a new user via Supabase Auth. Lets AuthApiError propagate."""
    return supabase.auth.sign_up({"email": email, "password": password})


def create_parent_record(user_id: str, email: str, name: str) -> dict | None:
    """Insert a parent record."""
    result = (
        supabase_admin.table("parents")
        .insert({"id": user_id, "email": email, "name": name})
        .execute()
    )
    return result.data[0] if result.data else None


def login_user(email: str, password: str):
    """Authenticate a user via Supabase Auth. Lets AuthApiError propagate."""
    return supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )


def refresh_session(refresh_token: str):
    """Refresh a session using a refresh token. Lets AuthApiError propagate."""
    return supabase.auth.refresh_session(refresh_token)


# ── Lesson operations ────────────────────────────────────────────────

def list_lessons(level: int) -> list[dict]:
    """Fetch all lessons for a level, ordered by sequence."""
    result = (
        supabase_admin.table("lessons")
        .select("*")
        .eq("level", level)
        .order("sequence")
        .execute()
    )
    return result.data or []


def get_lesson_by_id(lesson_id: str) -> dict | None:
    """Fetch a single lesson by ID."""
    result = (
        supabase_admin.table("lessons")
        .select("*")
        .eq("id", lesson_id)
        .single()
        .execute()
    )
    return result.data


def get_lesson_context(child_id: str) -> dict | None:
    """Fetch the child's current/recent lesson for conversation context.

    Returns {"title": str, "theme": str, "vocabulary": list} or None.
    """
    progress = (
        supabase_admin.table("child_lesson_progress")
        .select("lesson_id, status")
        .eq("child_id", child_id)
        .in_("status", ["in_progress", "completed"])
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )

    if not progress.data:
        return None

    lesson_id = progress.data[0]["lesson_id"]
    lesson = (
        supabase_admin.table("lessons")
        .select("title, theme, vocabulary")
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    return lesson.data if lesson.data else None


def record_lesson_completion(child_id: str, lesson_id: str, score: int) -> None:
    """Upsert lesson completion into child_lesson_progress."""
    existing = (
        supabase_admin.table("child_lesson_progress")
        .select("id")
        .eq("child_id", child_id)
        .eq("lesson_id", lesson_id)
        .execute()
    )

    now = datetime.now(timezone.utc).isoformat()

    if existing.data:
        supabase_admin.table("child_lesson_progress").update(
            {"status": "completed", "score": score, "completed_at": now}
        ).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase_admin.table("child_lesson_progress").insert(
            {
                "child_id": child_id,
                "lesson_id": lesson_id,
                "status": "completed",
                "score": score,
                "completed_at": now,
            }
        ).execute()


# ── Conversation operations ───────────────────────────────────────────

def start_conversation_record(child_id: str) -> dict | None:
    """Insert a new conversation row. Returns the row dict (with 'id')."""
    result = (
        supabase_admin.table("conversations")
        .insert({"child_id": child_id})
        .execute()
    )
    return result.data[0] if result.data else None


def save_message(conversation_id: str, role: str, content: str) -> None:
    """Insert a message into conversation_messages."""
    supabase_admin.table("conversation_messages").insert(
        {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
    ).execute()


def get_conversation_messages(conversation_id: str) -> list[dict]:
    """Fetch all messages for a conversation, ordered by created_at."""
    result = (
        supabase_admin.table("conversation_messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def get_conversation(conversation_id: str) -> dict | None:
    """Fetch a conversation row (child_id, message_count, ended_at, started_at)."""
    result = (
        supabase_admin.table("conversations")
        .select("child_id, message_count, ended_at, started_at")
        .eq("id", conversation_id)
        .single()
        .execute()
    )
    return result.data


def update_conversation_message_count(conversation_id: str, count: int) -> None:
    """Set message_count on a conversation."""
    supabase_admin.table("conversations").update(
        {"message_count": count}
    ).eq("id", conversation_id).execute()


def end_conversation_record(conversation_id: str, ended_at: str) -> None:
    """Set ended_at on a conversation."""
    supabase_admin.table("conversations").update(
        {"ended_at": ended_at}
    ).eq("id", conversation_id).execute()


# ── Progress query operations ─────────────────────────────────────────

def count_completed_lessons(child_id: str | None = None, child_ids: list[str] | None = None) -> int:
    """Count completed lessons for one child or a list of children."""
    query = (
        supabase_admin.table("child_lesson_progress")
        .select("id", count="exact")
        .eq("status", "completed")
    )
    if child_id:
        query = query.eq("child_id", child_id)
    elif child_ids:
        query = query.in_("child_id", child_ids)
    return query.execute().count or 0


def count_conversations(child_id: str | None = None, child_ids: list[str] | None = None) -> int:
    """Count conversations for one child or a list of children."""
    query = supabase_admin.table("conversations").select("id", count="exact")
    if child_id:
        query = query.eq("child_id", child_id)
    elif child_ids:
        query = query.in_("child_id", child_ids)
    return query.execute().count or 0


def get_conversations_with_ratios(child_ids: list[str]) -> list[dict]:
    """Fetch conversations with marathi_ratio for parent dashboard."""
    result = (
        supabase_admin.table("conversations")
        .select("id, marathi_ratio")
        .in_("child_id", child_ids)
        .execute()
    )
    return result.data or []
