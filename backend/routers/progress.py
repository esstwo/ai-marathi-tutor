"""Progress router — dashboard and XP stats."""

from fastapi import APIRouter, HTTPException
from backend.services.progress import get_progress, get_parent_progress

router = APIRouter(tags=["progress"])


@router.get("/progress/{child_id}")
def child_progress(child_id: str):
    """Return progress stats for a child."""
    try:
        return get_progress(child_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress: {e}")


@router.get("/parents/{parent_id}/progress")
def parent_progress(parent_id: str):
    """Return aggregated progress across all children for a parent."""
    try:
        return get_parent_progress(parent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch parent progress: {e}")
