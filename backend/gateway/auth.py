"""Auth middleware — token validation and child ownership checks."""

import os
from typing import Optional

from fastapi import Header, HTTPException

from backend.db.supabase_client import supabase
from backend.connectors.supabase.children import verify_child_belongs_to_parent

# Service key for server-to-server calls (MCP App, scripts, etc.)
# When present, bypasses JWT validation and child ownership checks.
_SERVICE_KEY = os.environ.get("MARATHI_SERVICE_KEY")

# Sentinel parent_id returned for service-key requests
SERVICE_MODE_PARENT = "__service__"


def get_current_parent(
    authorization: Optional[str] = Header(default=None),
    x_service_key: Optional[str] = Header(default=None),
) -> str:
    """Validate Bearer token or service key. Return the parent's user ID."""
    # Service key bypass — trusted server-to-server calls
    if x_service_key and _SERVICE_KEY and x_service_key == _SERVICE_KEY:
        return SERVICE_MODE_PARENT

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user_response is None or user_response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_response.user.id


def verify_child_ownership(child_id: str, parent_id: str) -> None:
    """Check that a child belongs to the authenticated parent. Raises 403 if not.

    Skipped in service mode (trusted server-to-server calls).
    """
    if parent_id == SERVICE_MODE_PARENT:
        return
    if not verify_child_belongs_to_parent(child_id, parent_id):
        raise HTTPException(status_code=403, detail="Access denied")
