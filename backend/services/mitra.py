"""Mitra conversation service — builds prompts, calls Groq, parses response."""

import os
import re
from groq import Groq
from dotenv import load_dotenv

from backend.db.supabase_client import supabase_admin
from backend.prompts.mitra_system import MITRA_BASE_PROMPT, LEVEL_LABELS

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 10
MAX_TOKENS = 300


def _build_lesson_context(child_id: str) -> str:
    """Fetch the child's current/recent lesson to give Mitra topical context."""
    progress = (
        supabase_admin.table("child_lesson_progress")
        .select("lesson_id, status")
        .eq("child_id", child_id)
        .in_("status", ["in_progress", "completed"])
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )

    if not progress.data:
        return "No lesson in progress. Have a general Marathi conversation appropriate for the child's level."

    lesson_id = progress.data[0]["lesson_id"]
    lesson = (
        supabase_admin.table("lessons")
        .select("title, theme, vocabulary")
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    if not lesson.data:
        return "No lesson in progress. Have a general Marathi conversation appropriate for the child's level."

    l = lesson.data
    vocab_lines = []
    for word in l["vocabulary"]:
        vocab_lines.append(f"  • {word['marathi']} = {word['english']}")
    vocab_str = "\n".join(vocab_lines)

    return f"""## Today's Lesson Context
Topic: {l['title']}
Theme: {l['theme']}
Key vocabulary to weave into conversation:
{vocab_str}

Try to naturally use these words during the conversation. Don't drill them — weave them in."""


def _get_child(child_id: str) -> dict:
    """Fetch child profile from DB."""
    result = (
        supabase_admin.table("children")
        .select("name, age, current_level")
        .eq("id", child_id)
        .single()
        .execute()
    )
    return result.data


def _build_system_prompt(child: dict, child_id: str) -> str:
    """Assemble the full system prompt with child context."""
    level = child["current_level"]
    return MITRA_BASE_PROMPT.format(
        age=child["age"],
        child_name=child["name"],
        level=level,
        level_label=LEVEL_LABELS.get(level, LEVEL_LABELS[1]),
        lesson_context=_build_lesson_context(child_id),
    )


def _parse_response(raw_text: str) -> dict:
    """Parse Mitra's response into marathi_text and english_hint.

    Expected format:
        MARATHI: <text>
        HINT: <text or "none">

    Falls back gracefully if the model doesn't follow the format.
    """
    marathi_match = re.search(
        r"MARATHI:\s*(.+?)(?=\nHINT:|\Z)", raw_text, re.DOTALL
    )
    hint_match = re.search(r"HINT:\s*(.+)", raw_text, re.DOTALL)

    if marathi_match:
        marathi_text = marathi_match.group(1).strip()
        english_hint = hint_match.group(1).strip() if hint_match else None
        if english_hint and english_hint.lower() == "none":
            english_hint = None
    else:
        # Model didn't follow format — treat entire response as Marathi
        marathi_text = raw_text.strip()
        english_hint = None

    return {"marathi_text": marathi_text, "english_hint": english_hint}


def greet(child_id: str) -> dict:
    """Generate Mitra's opening greeting for a new conversation.

    Returns:
        {"marathi_text": str, "english_hint": str | None, "raw": str}
    """
    child = _get_child(child_id)
    if not child:
        raise ValueError(f"Child not found: {child_id}")

    system_prompt = _build_system_prompt(child, child_id)
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "[SYSTEM: The child just opened the chat. "
                "Greet them warmly by name in Marathi and invite them to start talking. "
                "Keep it to 1-2 short sentences.]"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
    )

    raw_text = response.choices[0].message.content
    parsed = _parse_response(raw_text)
    parsed["raw"] = raw_text
    return parsed


def chat(child_id: str, message: str, conversation_history: list[dict]) -> dict:
    """Main entry point for the Mitra conversation service.

    Args:
        child_id: UUID of the child.
        message: The child's latest message.
        conversation_history: List of prior messages as
            [{"role": "child"|"mitra", "content": "..."}]

    Returns:
        {"marathi_text": str, "english_hint": str | None, "raw": str}
    """
    child = _get_child(child_id)
    if not child:
        raise ValueError(f"Child not found: {child_id}")

    system_prompt = _build_system_prompt(child, child_id)

    # Map conversation_history roles to LLM roles and take last N messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-MAX_HISTORY:]:
        role = "assistant" if msg["role"] == "mitra" else "user"
        messages.append({"role": role, "content": msg["content"]})

    # Add the current message
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
    )

    raw_text = response.choices[0].message.content
    parsed = _parse_response(raw_text)
    parsed["raw"] = raw_text

    return parsed
