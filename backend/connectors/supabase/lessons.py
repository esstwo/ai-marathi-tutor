"""Lesson connectors — fetch and complete lessons."""

from datetime import datetime, timezone

from backend.db.supabase_client import supabase_admin


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


def record_lesson_completion(child_id: str, lesson_id: str, score: int) -> dict:
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
    return {"ok": True}
