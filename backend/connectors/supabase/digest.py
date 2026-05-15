"""Supabase queries for the weekly parent digest."""

from datetime import datetime, timedelta, timezone

from backend.db.supabase_client import supabase_admin


def get_all_parents() -> list[dict]:
    """Fetch all parent records that have an email address."""
    result = supabase_admin.table("parents").select("id, name, email").execute()
    return [p for p in (result.data or []) if p.get("email")]


def get_weekly_lesson_completions(child_id: str, since: datetime) -> list[dict]:
    """Lessons completed by a child in the past week, with title and score."""
    completions = (
        supabase_admin.table("child_lesson_progress")
        .select("lesson_id, score, completed_at")
        .eq("child_id", child_id)
        .eq("status", "completed")
        .gte("completed_at", since.isoformat())
        .execute()
    )
    if not completions.data:
        return []

    lesson_ids = [r["lesson_id"] for r in completions.data]
    lessons = (
        supabase_admin.table("lessons")
        .select("id, title")
        .in_("id", lesson_ids)
        .execute()
    )
    title_map = {l["id"]: l["title"] for l in (lessons.data or [])}

    return [
        {
            "title": title_map.get(r["lesson_id"], "Unknown lesson"),
            "score": r["score"],
            "completed_at": r["completed_at"],
        }
        for r in completions.data
    ]


def get_weekly_conversations(child_id: str, since: datetime) -> list[dict]:
    """Conversations started by a child in the past week."""
    result = (
        supabase_admin.table("conversations")
        .select("id, started_at, ended_at, marathi_ratio")
        .eq("child_id", child_id)
        .gte("started_at", since.isoformat())
        .execute()
    )
    return result.data or []
