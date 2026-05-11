"""Conversation connectors — manage conversations and messages."""

from backend.db.supabase_client import supabase_admin


def start_conversation_record(child_id: str) -> dict | None:
    """Insert a new conversation row. Returns the row dict (with 'id')."""
    result = (
        supabase_admin.table("conversations")
        .insert({"child_id": child_id})
        .execute()
    )
    return result.data[0] if result.data else None


def save_message(conversation_id: str, role: str, content: str) -> dict:
    """Insert a message into conversation_messages."""
    supabase_admin.table("conversation_messages").insert(
        {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
    ).execute()
    return {"ok": True}


def get_conversation_messages(conversation_id: str) -> list[dict]:
    """Fetch all messages for a conversation, ordered by created_at."""
    result = (
        supabase_admin.table("conversation_messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def get_conversation(conversation_id: str) -> dict | None:
    """Fetch a conversation row (child_id, message_count, ended_at, started_at)."""
    result = (
        supabase_admin.table("conversations")
        .select("child_id, message_count, ended_at, started_at, context")
        .eq("id", conversation_id)
        .single()
        .execute()
    )
    return result.data


def update_conversation_message_count(conversation_id: str, count: int) -> dict:
    """Set message_count on a conversation."""
    supabase_admin.table("conversations").update(
        {"message_count": count}
    ).eq("id", conversation_id).execute()
    return {"ok": True}


def end_conversation_record(conversation_id: str, ended_at: str) -> dict:
    """Set ended_at on a conversation."""
    supabase_admin.table("conversations").update(
        {"ended_at": ended_at}
    ).eq("id", conversation_id).execute()
    return {"ok": True}
