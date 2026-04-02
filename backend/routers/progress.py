"""Progress router — dashboard and XP stats."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from backend.services.progress import get_progress, get_parent_progress
from backend.dependencies.auth import get_current_parent, verify_child_ownership

logger = logging.getLogger(__name__)
router = APIRouter(tags=["progress"])


@router.get("/progress/{child_id}")
async def child_progress(child_id: str, parent_id: str = Depends(get_current_parent)):
    """Return progress stats for a child."""
    verify_child_ownership(child_id, parent_id)
    try:
        return await get_progress(child_id)
    except Exception as e:
        logger.exception("Failed to fetch child progress")
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress: {e}")


@router.get("/parents/{parent_id}/progress")
async def parent_progress(parent_id: str, current_parent_id: str = Depends(get_current_parent)):
    """Return aggregated progress across all children for a parent."""
    if parent_id != current_parent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        return await get_parent_progress(parent_id)
    except Exception as e:
        logger.exception("Failed to fetch parent progress")
        raise HTTPException(status_code=500, detail=f"Failed to fetch parent progress: {e}")
