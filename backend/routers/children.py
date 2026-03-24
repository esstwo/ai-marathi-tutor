from fastapi import APIRouter, HTTPException, Header
from backend.db.supabase_client import supabase, supabase_admin
from backend.models.schemas import ChildCreateRequest

router = APIRouter(tags=["children"])


@router.post("/children")
def create_child(req: ChildCreateRequest, authorization: str = Header()):
    # Extract token and get the authenticated user
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
