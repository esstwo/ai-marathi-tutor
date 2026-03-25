"""Lessons router — fetch lessons and record completion."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.db.supabase_client import supabase_admin
from backend.models.schemas import LessonResponse, LessonCompleteRequest
from backend.services.progress import award_lesson_xp

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/by-level/{level}", response_model=list[LessonResponse])
def list_lessons_by_level(level: int):
    """Return all lessons for a given level, ordered by sequence."""
    result = (
        supabase_admin.table("lessons")
        .select("*")
        .eq("level", level)
        .order("sequence")
        .execute()
    )
    return result.data or []


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: str):
    """Fetch a single lesson by ID."""
    result = (
        supabase_admin.table("lessons")
        .select("*")
        .eq("id", lesson_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return result.data


@router.post("/{lesson_id}/complete")
def complete_lesson(lesson_id: str, req: LessonCompleteRequest):
    """Record or update lesson completion for a child."""
    # Check if progress row already exists
    existing = (
        supabase_admin.table("child_lesson_progress")
        .select("id")
        .eq("child_id", req.child_id)
        .eq("lesson_id", lesson_id)
        .execute()
    )

    now = datetime.now(timezone.utc).isoformat()

    if existing.data:
        # Update existing progress
        supabase_admin.table("child_lesson_progress").update(
            {"status": "completed", "score": req.score, "completed_at": now}
        ).eq("id", existing.data[0]["id"]).execute()
    else:
        # Insert new progress
        supabase_admin.table("child_lesson_progress").insert(
            {
                "child_id": req.child_id,
                "lesson_id": lesson_id,
                "status": "completed",
                "score": req.score,
                "completed_at": now,
            }
        ).execute()

    # Award XP and update streak
    xp_result = award_lesson_xp(req.child_id)

    return {
        "message": "Lesson completed",
        "score": req.score,
        "xp_earned": xp_result["xp_earned"],
        "xp_total": xp_result["xp_total"],
        "streak_days": xp_result["streak_days"],
    }
