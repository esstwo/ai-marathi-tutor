"""Conversation router — start conversations and chat with Mitra."""

from fastapi import APIRouter, HTTPException

from backend.db.supabase_client import supabase_admin
from backend.models.schemas import (
    StartConversationRequest,
    StartConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from backend.services.mitra import chat, greet
from backend.services.progress import award_conversation_xp

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/start", response_model=StartConversationResponse)
def start_conversation(req: StartConversationRequest):
    """Create a new conversation and return Mitra's opening greeting."""
    try:
        # Create conversation row
        conv = (
            supabase_admin.table("conversations")
            .insert({"child_id": req.child_id})
            .execute()
        )
        if not conv.data:
            raise HTTPException(status_code=500, detail="Failed to create conversation")

        conversation_id = conv.data[0]["id"]

        # Get Mitra's greeting
        result = greet(req.child_id)

        # Persist greeting message
        supabase_admin.table("conversation_messages").insert(
            {
                "conversation_id": conversation_id,
                "role": "mitra",
                "content": result["marathi_text"],
            }
        ).execute()

        # Update message count
        supabase_admin.table("conversations").update(
            {"message_count": 1}
        ).eq("id", conversation_id).execute()

        return StartConversationResponse(
            conversation_id=conversation_id,
            marathi_text=result["marathi_text"],
            english_hint=result["english_hint"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {e}")


@router.post("/{conversation_id}/message", response_model=SendMessageResponse)
def send_message(conversation_id: str, req: SendMessageRequest):
    """Send a child message and get Mitra's response."""
    try:
        # Fetch conversation to get child_id
        conv = (
            supabase_admin.table("conversations")
            .select("child_id, message_count")
            .eq("id", conversation_id)
            .single()
            .execute()
        )
        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        child_id = conv.data["child_id"]
        current_count = conv.data["message_count"] or 0

        # Persist child message
        supabase_admin.table("conversation_messages").insert(
            {
                "conversation_id": conversation_id,
                "role": "child",
                "content": req.message,
            }
        ).execute()

        # Load conversation history from DB (last 10 messages for LLM context)
        history_rows = (
            supabase_admin.table("conversation_messages")
            .select("role, content")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .execute()
        )
        conversation_history = [
            {"role": row["role"], "content": row["content"]}
            for row in (history_rows.data or [])
        ]

        # Call Mitra (history already includes the child message we just saved)
        result = chat(
            child_id=child_id,
            message=req.message,
            conversation_history=conversation_history[:-1],  # exclude current msg, chat() adds it
        )

        # Persist Mitra's response
        supabase_admin.table("conversation_messages").insert(
            {
                "conversation_id": conversation_id,
                "role": "mitra",
                "content": result["marathi_text"],
            }
        ).execute()

        # Update message count (+2 for child + mitra)
        supabase_admin.table("conversations").update(
            {"message_count": current_count + 2}
        ).eq("id", conversation_id).execute()

        return SendMessageResponse(
            marathi_text=result["marathi_text"],
            english_hint=result["english_hint"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mitra service error: {e}")


@router.post("/{conversation_id}/end")
def end_conversation(conversation_id: str):
    """End a conversation, set ended_at, and award XP based on duration."""
    from datetime import datetime, timezone

    try:
        conv = (
            supabase_admin.table("conversations")
            .select("child_id, ended_at")
            .eq("id", conversation_id)
            .single()
            .execute()
        )
        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conv.data.get("ended_at"):
            return {"message": "Conversation already ended"}

        now = datetime.now(timezone.utc).isoformat()
        supabase_admin.table("conversations").update(
            {"ended_at": now}
        ).eq("id", conversation_id).execute()

        xp_result = award_conversation_xp(conv.data["child_id"], conversation_id)

        return {
            "message": "Conversation ended",
            "xp_earned": xp_result["xp_earned"],
            "xp_total": xp_result["xp_total"],
            "streak_days": xp_result["streak_days"],
            "duration_minutes": xp_result["duration_minutes"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {e}")
