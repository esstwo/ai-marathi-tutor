"""Auth middleware — token validation and child ownership checks."""

from fastapi import Header, HTTPException

from backend.db.supabase_client import supabase
from backend.connectors.supabase.children import verify_child_belongs_to_parent


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
    if not verify_child_belongs_to_parent(child_id, parent_id):
        raise HTTPException(status_code=403, detail="Access denied")
