"""Progress router — dashboard and XP stats."""

from fastapi import APIRouter, HTTPException
from backend.services.progress import get_progress

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{child_id}")
def child_progress(child_id: str):
    """Return progress stats for a child."""
    try:
        return get_progress(child_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress: {e}")
