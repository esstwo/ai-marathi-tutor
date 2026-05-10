"""Guardrails for child safety, input/output validation, session limits, and cost protection.

All guardrail functions are pure — they raise HTTPException or return validated data.
Wire them into api.py endpoints.
"""

import logging
import os
import re
import time
from datetime import datetime, timezone

from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Configuration ──────────────────────────────────────────────────────

MAX_MESSAGE_LENGTH = 500
MAX_MESSAGES_PER_CONVERSATION = 50
MAX_CONVERSATION_MINUTES = 30
MAX_CONCURRENT_CONVERSATIONS = 3
DAILY_LLM_CALL_LIMIT = int(os.environ.get("DAILY_LLM_CALL_LIMIT", "500"))

# ── Input guardrails ──────────────────────────────────────────────────

# Prompt injection patterns — phrases that attempt to override system instructions
_INJECTION_PATTERNS = [
    r"ignore\s+(your|all|previous|above|the)\s+(?:\w+\s+)?(instructions|rules|prompt|guidelines)",
    r"ignore\s+all\s+previous\s+\w+",
    r"forget\s+(your|all|previous|above|the)\s+(?:\w+\s+)?(instructions|rules|prompt|guidelines)",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"act\s+as\s+(?:a|an)\s+",
    r"pretend\s+(?:you(?:'re|\s+are)\s+|to\s+be\s+)",
    r"disregard\s+(?:your|all|previous|above)",
    r"override\s+(?:your|all|previous|above)",
    r"jailbreak",
    r"\bDAN\b",
    r"do\s+anything\s+now",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# Profanity / inappropriate content — basic blocklist for kids' app
# Covers English profanity; Marathi/Hindi slurs would need a separate list
_PROFANITY_WORDS = {
    "fuck", "shit", "damn", "ass", "bitch", "bastard", "crap",
    "dick", "cock", "pussy", "slut", "whore", "nigger", "faggot",
    "kill", "murder", "suicide", "rape", "porn", "sex", "drug",
    "alcohol", "beer", "wine", "vodka", "whiskey", "cigarette",
    "gun", "bomb", "bombs", "weapon", "terrorist",
    "drugs", "guns", "weapons",
}
# Build regex that matches whole words only
_PROFANITY_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in _PROFANITY_WORDS) + r")\b",
    re.IGNORECASE,
)


def validate_message_input(message: str) -> str:
    """Validate and sanitize a child's chat message. Returns cleaned message or raises."""
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    message = message.strip()

    if len(message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Message too long — please keep it under {MAX_MESSAGE_LENGTH} characters.",
        )

    # Check for prompt injection attempts
    if _INJECTION_RE.search(message):
        logger.warning("Prompt injection attempt detected: %s", message[:100])
        raise HTTPException(
            status_code=400,
            detail="Hmm, that message didn't look quite right. Try saying something in Marathi or English!",
        )

    # Check for profanity / inappropriate content
    match = _PROFANITY_RE.search(message)
    if match:
        logger.warning("Profanity detected in child message: %s", match.group())
        raise HTTPException(
            status_code=400,
            detail="Let's keep our words kind and friendly! Try again with different words.",
        )

    return message


# ── Output guardrails ─────────────────────────────────────────────────

# Patterns that should never appear in LLM responses to children
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

SAFE_FALLBACK = {
    "marathi_text": "चला, आपण मराठी शिकूया!",
    "english_hint": "Let's learn Marathi!",
}


def validate_llm_output(parsed: dict) -> dict:
    """Validate and sanitize the LLM's parsed response. Returns cleaned dict."""
    # Ensure required field exists
    if "marathi_text" not in parsed or not parsed["marathi_text"]:
        logger.warning("LLM output missing marathi_text, using fallback")
        return {**SAFE_FALLBACK, "raw": parsed.get("raw", "")}

    text = parsed["marathi_text"]
    hint = parsed.get("english_hint", "")
    flagged = False

    # Strip URLs from response
    for field_name, value in [("marathi_text", text), ("english_hint", hint)]:
        if value and _URL_RE.search(str(value)):
            logger.warning("LLM output contained URL in %s, stripping", field_name)
            parsed[field_name] = _URL_RE.sub("", str(value)).strip()
            flagged = True

    # Strip emails
    for field_name, value in [("marathi_text", parsed["marathi_text"]), ("english_hint", parsed.get("english_hint", ""))]:
        if value and _EMAIL_RE.search(str(value)):
            logger.warning("LLM output contained email in %s, stripping", field_name)
            parsed[field_name] = _EMAIL_RE.sub("", str(value)).strip()
            flagged = True

    # Strip phone numbers
    for field_name, value in [("marathi_text", parsed["marathi_text"]), ("english_hint", parsed.get("english_hint", ""))]:
        if value and _PHONE_RE.search(str(value)):
            logger.warning("LLM output contained phone number in %s, stripping", field_name)
            parsed[field_name] = _PHONE_RE.sub("", str(value)).strip()
            flagged = True

    # Check for profanity in LLM output
    for field_name in ["marathi_text", "english_hint"]:
        value = parsed.get(field_name, "")
        if value and _PROFANITY_RE.search(str(value)):
            logger.warning("LLM output contained profanity in %s, using fallback", field_name)
            return {**SAFE_FALLBACK, "raw": parsed.get("raw", "")}

    # If marathi_text got emptied after stripping, use fallback
    if not parsed["marathi_text"].strip():
        return {**SAFE_FALLBACK, "raw": parsed.get("raw", "")}

    if flagged:
        parsed["_flagged"] = True

    return parsed


# ── Session guardrails ────────────────────────────────────────────────

def check_message_limit(message_count: int):
    """Raise if conversation has exceeded the message limit."""
    if message_count >= MAX_MESSAGES_PER_CONVERSATION:
        raise HTTPException(
            status_code=400,
            detail="This conversation has reached its limit. Please end it and start a new one!",
        )


def check_conversation_duration(started_at: str):
    """Raise if conversation has been running too long."""
    if not started_at:
        return
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() / 60
        if elapsed > MAX_CONVERSATION_MINUTES:
            raise HTTPException(
                status_code=400,
                detail="This conversation has been going on for a while. Let's take a break and start fresh!",
            )
    except (ValueError, TypeError):
        pass  # If we can't parse the timestamp, skip this check


def check_concurrent_conversations(child_id: str, supabase_admin):
    """Raise if child has too many active (un-ended) conversations."""
    result = (
        supabase_admin.table("conversations")
        .select("id", count="exact")
        .eq("child_id", child_id)
        .is_("ended_at", "null")
        .execute()
    )
    active_count = result.count if result.count is not None else len(result.data)
    if active_count >= MAX_CONCURRENT_CONVERSATIONS:
        raise HTTPException(
            status_code=400,
            detail="You have too many open conversations. Please end one before starting a new one.",
        )


# ── Cost protection ───────────────────────────────────────────────────

# Simple in-memory daily counter (resets on server restart or date change)
_daily_calls = {"date": "", "count": 0}


def track_llm_call():
    """Increment daily LLM call counter. Raise if limit exceeded."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if _daily_calls["date"] != today:
        _daily_calls["date"] = today
        _daily_calls["count"] = 0

    _daily_calls["count"] += 1

    if _daily_calls["count"] > DAILY_LLM_CALL_LIMIT:
        logger.error("Daily LLM call limit exceeded: %d/%d", _daily_calls["count"], DAILY_LLM_CALL_LIMIT)
        raise HTTPException(
            status_code=503,
            detail="The learning service is very busy today. Please try again tomorrow!",
        )

    if _daily_calls["count"] % 100 == 0:
        logger.info("Daily LLM usage: %d/%d calls", _daily_calls["count"], DAILY_LLM_CALL_LIMIT)

    # Warn at 80% usage
    if _daily_calls["count"] == int(DAILY_LLM_CALL_LIMIT * 0.8):
        logger.warning("Daily LLM usage at 80%%: %d/%d calls", _daily_calls["count"], DAILY_LLM_CALL_LIMIT)


def get_daily_usage() -> dict:
    """Return current daily LLM usage stats."""
    return {
        "date": _daily_calls["date"],
        "calls": _daily_calls["count"],
        "limit": DAILY_LLM_CALL_LIMIT,
    }


# ── Content flagging ─────────────────────────────────────────────────

def flag_conversation(conversation_id: str, reason: str, supabase_admin):
    """Log a safety flag on a conversation for parent review."""
    try:
        supabase_admin.table("conversation_flags").insert({
            "conversation_id": conversation_id,
            "reason": reason,
            "flagged_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.info("Flagged conversation %s: %s", conversation_id, reason)
    except Exception as e:
        # Don't let flagging failures break the conversation flow
        logger.warning("Failed to flag conversation %s: %s", conversation_id, e)
