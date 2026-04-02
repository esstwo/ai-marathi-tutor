"""Mitra Conversation Skill — prompt building, LLM calls, response parsing.

This is the intelligence layer: it owns the system prompt, Groq API interaction,
and response format. Data access goes through supabase_tools.
"""

import os
import re
import time
import logging

from groq import Groq, RateLimitError, APITimeoutError, AuthenticationError, BadRequestError, APIConnectionError
from dotenv import load_dotenv

from backend.services.llm_errors import (
    LLMRateLimitError, LLMTimeoutError, LLMAuthError,
    LLMContentFilterError, LLMConnectionError,
)
from backend.mcp.supabase_tools import get_child_profile, get_lesson_context
from backend.prompts.mitra_system import MITRA_BASE_PROMPT, LEVEL_LABELS

logger = logging.getLogger(__name__)

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 10
MAX_TOKENS = 300


def call_llm(messages: list[dict], max_retries: int = 2) -> str:
    """Call the Groq API with structured error handling and retry logic."""
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=messages,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning("Groq rate limited, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
                time.sleep(wait)
            else:
                logger.error("Groq rate limit exceeded after %d retries", max_retries)
                raise LLMRateLimitError("Mitra is taking a break — please try again shortly.") from e
        except APITimeoutError as e:
            if attempt < max_retries:
                logger.warning("Groq timeout, retrying (attempt %d/%d)", attempt + 1, max_retries)
            else:
                logger.error("Groq timeout after %d retries", max_retries)
                raise LLMTimeoutError("Mitra took too long to respond — please try again.") from e
        except AuthenticationError as e:
            logger.error("Groq authentication failed: %s", e)
            raise LLMAuthError("Service temporarily unavailable.") from e
        except BadRequestError as e:
            logger.error("Groq bad request (possible content filter): %s", e)
            raise LLMContentFilterError("Could not generate a response for this input.") from e
        except APIConnectionError as e:
            if attempt < max_retries:
                logger.warning("Groq connection error, retrying (attempt %d/%d)", attempt + 1, max_retries)
            else:
                logger.error("Groq connection failed after %d retries", max_retries)
                raise LLMConnectionError("Could not reach the language service.") from e


def build_lesson_context_text(child_id: str) -> str:
    """Format lesson context as text for the system prompt."""
    lesson = get_lesson_context(child_id)

    if not lesson:
        return "No lesson in progress. Have a general Marathi conversation appropriate for the child's level."

    vocab_lines = []
    for word in lesson["vocabulary"]:
        vocab_lines.append(f"  \u2022 {word['marathi']} = {word['english']}")
    vocab_str = "\n".join(vocab_lines)

    return f"""## Today's Lesson Context
Topic: {lesson['title']}
Theme: {lesson['theme']}
Key vocabulary to weave into conversation:
{vocab_str}

Try to naturally use these words during the conversation. Don't drill them \u2014 weave them in."""


def build_system_prompt(child: dict, child_id: str) -> str:
    """Assemble the full system prompt with child context."""
    level = child["current_level"]
    return MITRA_BASE_PROMPT.format(
        age=child["age"],
        child_name=child["name"],
        level=level,
        level_label=LEVEL_LABELS.get(level, LEVEL_LABELS[1]),
        lesson_context=build_lesson_context_text(child_id),
    )


def parse_response(raw_text: str) -> dict:
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
        marathi_text = raw_text.strip()
        english_hint = None

    return {"marathi_text": marathi_text, "english_hint": english_hint}


def greet(child_id: str) -> dict:
    """Generate Mitra's opening greeting for a new conversation.

    Returns:
        {"marathi_text": str, "english_hint": str | None, "raw": str}
    """
    child = get_child_profile(child_id)
    if not child:
        raise ValueError(f"Child not found: {child_id}")

    system_prompt = build_system_prompt(child, child_id)
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

    raw_text = call_llm(messages)
    parsed = parse_response(raw_text)
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
    child = get_child_profile(child_id)
    if not child:
        raise ValueError(f"Child not found: {child_id}")

    system_prompt = build_system_prompt(child, child_id)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-MAX_HISTORY:]:
        role = "assistant" if msg["role"] == "mitra" else "user"
        messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    raw_text = call_llm(messages)
    parsed = parse_response(raw_text)
    parsed["raw"] = raw_text

    return parsed
