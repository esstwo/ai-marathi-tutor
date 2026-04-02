"""Auth router — signup, login, child creation."""

from fastapi import APIRouter, Depends, HTTPException
from supabase_auth.errors import AuthApiError
from backend.models.schemas import SignupRequest, LoginRequest, ChildCreateRequest
from backend.dependencies.auth import get_current_parent
from pydantic import BaseModel
from backend.mcp.supabase_tools import (
    signup_user,
    create_parent_record,
    login_user,
    get_children_by_parent,
    create_child as db_create_child,
    refresh_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(req: SignupRequest):
    try:
        auth_response = signup_user(req.email, req.password)
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if auth_response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_response.user.id

    parent = create_parent_record(user_id, req.email, req.name)

    if not parent:
        raise HTTPException(status_code=500, detail="Failed to create parent record")

    access_token = None
    refresh_token = None
    if auth_response.session:
        access_token = auth_response.session.access_token
        refresh_token = auth_response.session.refresh_token

    return {
        "message": "Signup successful",
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "parent": parent,
    }


@router.post("/login")
def login(req: LoginRequest):
    try:
        auth_response = login_user(req.email, req.password)
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if auth_response.user is None or auth_response.session is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = auth_response.user.id
    children = get_children_by_parent(user_id)

    return {
        "message": "Login successful",
        "user_id": user_id,
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
        "children": children,
    }


@router.post("/children")
def create_child(req: ChildCreateRequest, parent_id: str = Depends(get_current_parent)):

    if not 5 <= req.age <= 12:
        raise HTTPException(status_code=400, detail="Age must be between 5 and 12")

    child = db_create_child(parent_id, req.name, req.age, req.avatar)

    if not child:
        raise HTTPException(status_code=500, detail="Failed to create child")

    return {"message": "Child created", "child": child}


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
def refresh(req: RefreshRequest):
    """Exchange a refresh token for a new access token."""
    try:
        auth_response = refresh_session(req.refresh_token)
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if auth_response.session is None:
        raise HTTPException(status_code=401, detail="Failed to refresh session")

    return {
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
    }
