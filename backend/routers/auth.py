"""Auth router — signup, login, child creation."""

from fastapi import APIRouter, HTTPException, Header
from supabase_auth.errors import AuthApiError
from backend.db.supabase_client import supabase, supabase_admin
from backend.models.schemas import SignupRequest, LoginRequest, ChildCreateRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(req: SignupRequest):
    try:
        auth_response = supabase.auth.sign_up(
            {"email": req.email, "password": req.password}
        )
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if auth_response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_response.user.id

    parent_response = (
        supabase_admin.table("parents")
        .insert({"id": user_id, "email": req.email, "name": req.name})
        .execute()
    )

    if not parent_response.data:
        raise HTTPException(status_code=500, detail="Failed to create parent record")

    access_token = None
    if auth_response.session:
        access_token = auth_response.session.access_token

    return {
        "message": "Signup successful",
        "user_id": user_id,
        "access_token": access_token,
        "parent": parent_response.data[0],
    }


@router.post("/login")
def login(req: LoginRequest):
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": req.email, "password": req.password}
        )
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if auth_response.user is None or auth_response.session is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = auth_response.user.id

    children_response = (
        supabase_admin.table("children")
        .select("id, name, age, avatar, current_level")
        .eq("parent_id", user_id)
        .execute()
    )

    return {
        "message": "Login successful",
        "user_id": user_id,
        "access_token": auth_response.session.access_token,
        "children": children_response.data or [],
    }


@router.post("/children")
def create_child(req: ChildCreateRequest, authorization: str = Header()):
    token = authorization.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)

    if user_response is None or user_response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    parent_id = user_response.user.id

    if not 5 <= req.age <= 12:
        raise HTTPException(status_code=400, detail="Age must be between 5 and 12")

    child_response = (
        supabase_admin.table("children")
        .insert({
            "parent_id": parent_id,
            "name": req.name,
            "age": req.age,
            "avatar": req.avatar,
        })
        .execute()
    )

    if not child_response.data:
        raise HTTPException(status_code=500, detail="Failed to create child")

    return {"message": "Child created", "child": child_response.data[0]}
