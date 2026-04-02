"""Conversation router — start conversations and chat with Mitra."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.models.schemas import (
    StartConversationRequest,
    StartConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from backend.skills.mitra_conversation import chat, greet
from backend.services.progress import award_conversation_xp
from backend.services.llm_errors import (
    LLMRateLimitError, LLMTimeoutError, LLMAuthError,
    LLMContentFilterError, LLMServiceError,
)
from backend.dependencies.auth import get_current_parent, verify_child_ownership
from backend.mcp.supabase_tools import (
    start_conversation_record,
    save_message,
    get_conversation_messages,
    get_conversation,
    update_conversation_message_count,
    end_conversation_record,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/start", response_model=StartConversationResponse)
def start_conversation(req: StartConversationRequest, parent_id: str = Depends(get_current_parent)):
    """Create a new conversation and return Mitra's opening greeting."""
    try:
        verify_child_ownership(req.child_id, parent_id)

        conv = start_conversation_record(req.child_id)
        if not conv:
            raise HTTPException(status_code=500, detail="Failed to create conversation")

        conversation_id = conv["id"]

        result = greet(req.child_id)

        save_message(conversation_id, "mitra", result["marathi_text"])

        update_conversation_message_count(conversation_id, 1)

        return StartConversationResponse(
            conversation_id=conversation_id,
            marathi_text=result["marathi_text"],
            english_hint=result["english_hint"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except LLMAuthError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMContentFilterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error starting conversation")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {e}")


@router.post("/{conversation_id}/message", response_model=SendMessageResponse)
def send_message(conversation_id: str, req: SendMessageRequest, parent_id: str = Depends(get_current_parent)):
    """Send a child message and get Mitra's response."""
    try:
        conv = get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        child_id = conv["child_id"]
        verify_child_ownership(child_id, parent_id)
        current_count = conv["message_count"] or 0

        save_message(conversation_id, "child", req.message)

        history_rows = get_conversation_messages(conversation_id)
        conversation_history = [
            {"role": row["role"], "content": row["content"]}
            for row in history_rows
        ]

        result = chat(
            child_id=child_id,
            message=req.message,
            conversation_history=conversation_history[:-1],
        )

        save_message(conversation_id, "mitra", result["marathi_text"])

        update_conversation_message_count(conversation_id, current_count + 2)

        return SendMessageResponse(
            marathi_text=result["marathi_text"],
            english_hint=result["english_hint"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except LLMAuthError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMContentFilterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in send_message")
        raise HTTPException(status_code=500, detail=f"Mitra service error: {e}")


@router.post("/{conversation_id}/end")
def end_conversation(conversation_id: str, parent_id: str = Depends(get_current_parent)):
    """End a conversation, set ended_at, and award XP based on duration."""
    try:
        conv = get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        verify_child_ownership(conv["child_id"], parent_id)

        if conv.get("ended_at"):
            return {"message": "Conversation already ended"}

        now = datetime.now(timezone.utc).isoformat()
        end_conversation_record(conversation_id, now)

        xp_result = award_conversation_xp(conv["child_id"], conversation_id)

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
        logger.exception("Unexpected error ending conversation")
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {e}")
