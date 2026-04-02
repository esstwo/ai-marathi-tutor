"""Lessons router — fetch lessons and record completion."""

from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import LessonResponse, LessonCompleteRequest
from backend.services.progress import award_lesson_xp
from backend.dependencies.auth import get_current_parent, verify_child_ownership
from backend.mcp.client import call_supabase_tool

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/by-level/{level}", response_model=list[LessonResponse])
async def list_lessons_by_level(level: int):
    """Return all lessons for a given level, ordered by sequence."""
    return await call_supabase_tool("list_lessons", {"level": level})


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str):
    """Fetch a single lesson by ID."""
    result = await call_supabase_tool("get_lesson_by_id", {"lesson_id": lesson_id})
    if not result:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return result


@router.post("/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, req: LessonCompleteRequest, parent_id: str = Depends(get_current_parent)):
    """Record or update lesson completion for a child."""
    verify_child_ownership(req.child_id, parent_id)

    await call_supabase_tool("record_lesson_completion", {
        "child_id": req.child_id,
        "lesson_id": lesson_id,
        "score": req.score,
    })

    xp_result = await award_lesson_xp(req.child_id)

    return {
        "message": "Lesson completed",
        "score": req.score,
        "xp_earned": xp_result["xp_earned"],
        "xp_total": xp_result["xp_total"],
        "streak_days": xp_result["streak_days"],
    }
