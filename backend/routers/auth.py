from fastapi import APIRouter, HTTPException
from backend.db.supabase_client import supabase, supabase_admin
from backend.models.schemas import SignupRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(req: SignupRequest):
    # 1. Create auth user in Supabase
    auth_response = supabase.auth.sign_up(
        {"email": req.email, "password": req.password}
    )

    if auth_response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_response.user.id

    # 2. Insert row in parents table
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
