"""Reusable auth dependencies for FastAPI routers."""

from fastapi import Header, HTTPException

from backend.db.supabase_client import supabase, supabase_admin


def get_current_parent(authorization: str = Header()) -> str:
    """Validate Bearer token and return the parent's user ID."""
    token = authorization.replace("Bearer ", "")
    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user_response is None or user_response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_response.user.id


def verify_child_ownership(child_id: str, parent_id: str) -> None:
    """Check that a child belongs to the authenticated parent. Raises 403 if not."""
    result = (
        supabase_admin.table("children")
        .select("id")
        .eq("id", child_id)
        .eq("parent_id", parent_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=403, detail="Access denied")
