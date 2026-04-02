"""Mitra Conversation Skill — LLM-as-orchestrator with tool calling.

The LLM decides which tools to call (get_child_profile, get_lesson_context)
and generates structured JSON responses. The gateway just runs the agentic loop.
"""

import json
import os
import time
import logging

from groq import Groq, RateLimitError, APITimeoutError, AuthenticationError, BadRequestError, APIConnectionError
from dotenv import load_dotenv

from backend.services.llm_errors import (
    LLMRateLimitError, LLMTimeoutError, LLMAuthError,
    LLMContentFilterError, LLMConnectionError,
)
from backend.mcp.client import call_supabase_tool
from backend.prompts.mitra_system import MITRA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 10
MAX_TOKENS = 300
MAX_TOOL_ROUNDS = 3

# Tools the LLM can call (data-fetching only, not persistence)
MITRA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_child_profile",
            "description": "Fetch the child's profile including name, age, current_level, xp_total, streak_days",
            "parameters": {
                "type": "object",
                "properties": {
                    "child_id": {"type": "string", "description": "UUID of the child"}
                },
                "required": ["child_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_lesson_context",
            "description": "Fetch the child's current lesson vocabulary and theme to weave into conversation. Returns title, theme, and vocabulary list, or null if no lesson in progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "child_id": {"type": "string", "description": "UUID of the child"}
                },
                "required": ["child_id"]
            }
        }
    },
]

TOOL_EXECUTORS = {
    "get_child_profile": lambda args: call_supabase_tool("get_child_profile", args),
    "get_lesson_context": lambda args: call_supabase_tool("get_lesson_context", args),
}


def _call_groq(messages: list[dict], tools: list[dict] | None = None,
               response_format: dict | None = None, max_retries: int = 2):
    """Single Groq API call with retry logic. Returns the raw response."""
    kwargs = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
    if response_format:
        kwargs["response_format"] = response_format

    for attempt in range(max_retries + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning("Groq rate limited, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
                time.sleep(wait)
            else:
                raise LLMRateLimitError("Mitra is taking a break — please try again shortly.") from e
        except APITimeoutError as e:
            if attempt < max_retries:
                logger.warning("Groq timeout, retrying (attempt %d/%d)", attempt + 1, max_retries)
            else:
                raise LLMTimeoutError("Mitra took too long to respond — please try again.") from e
        except AuthenticationError as e:
            raise LLMAuthError("Service temporarily unavailable.") from e
        except BadRequestError as e:
            raise LLMContentFilterError("Could not generate a response for this input.") from e
        except APIConnectionError as e:
            if attempt < max_retries:
                logger.warning("Groq connection error, retrying (attempt %d/%d)", attempt + 1, max_retries)
            else:
                raise LLMConnectionError("Could not reach the language service.") from e


async def _execute_tool_calls(tool_calls) -> list[dict]:
    """Execute tool calls and return tool result messages."""
    results = []
    for tool_call in tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        executor = TOOL_EXECUTORS.get(name)
        if executor:
            try:
                result = await executor(args)
                content = json.dumps(result)
            except Exception as e:
                logger.warning("Tool %s failed: %s", name, e)
                content = json.dumps({"error": str(e)})
        else:
            content = json.dumps({"error": f"Unknown tool: {name}"})

        results.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": name,
            "content": content,
        })
    return results


async def call_llm(messages: list[dict], tools: list[dict] | None = None) -> str:
    """Call Groq with an agentic tool-calling loop.

    If the LLM requests tool calls, execute them and feed results back.
    Loops until the LLM produces a final text response or max rounds exceeded.
    Returns the final text content.
    """
    for round_num in range(MAX_TOOL_ROUNDS + 1):
        # On the final round (no more tool calls allowed), request JSON output
        response_format = None
        current_tools = tools
        if round_num == MAX_TOOL_ROUNDS:
            current_tools = None  # Force text-only response
            response_format = {"type": "json_object"}

        response = _call_groq(messages, tools=current_tools, response_format=response_format)
        message = response.choices[0].message

        if message.tool_calls and round_num < MAX_TOOL_ROUNDS:
            # LLM wants to call tools — execute and loop
            messages.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in message.tool_calls
                ],
            })
            tool_results = await _execute_tool_calls(message.tool_calls)
            messages.extend(tool_results)
            logger.info("Tool round %d: called %s", round_num + 1,
                        [tc.function.name for tc in message.tool_calls])
        else:
            # Final text response
            return message.content or ""

    return ""


def parse_json_response(raw_text: str) -> dict:
    """Parse LLM's JSON response into marathi_text and english_hint.

    Falls back gracefully if the LLM returns plain text.
    """
    try:
        data = json.loads(raw_text)
        return {
            "marathi_text": data.get("marathi_text", raw_text),
            "english_hint": data.get("english_hint"),
        }
    except (json.JSONDecodeError, TypeError):
        # Fallback: treat entire response as Marathi text
        return {"marathi_text": raw_text.strip(), "english_hint": None}


async def greet(child_id: str) -> dict:
    """Generate Mitra's opening greeting for a new conversation.

    The LLM calls get_child_profile and get_lesson_context itself
    via the tool-calling loop.

    Returns:
        {"marathi_text": str, "english_hint": str | None, "raw": str}
    """
    messages = [
        {"role": "system", "content": MITRA_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"[SYSTEM: The child (child_id: {child_id}) just opened the chat. "
                "First use your tools to learn about them, then "
                "greet them warmly by name in Marathi and invite them to start talking. "
                "Keep it to 1-2 short sentences. Respond as JSON.]"
            ),
        },
    ]

    raw_text = await call_llm(messages, tools=MITRA_TOOLS)
    parsed = parse_json_response(raw_text)
    parsed["raw"] = raw_text
    return parsed


async def chat(child_id: str, message: str, conversation_history: list[dict]) -> dict:
    """Main conversation entry point. The LLM orchestrates tool calls as needed.

    Args:
        child_id: UUID of the child.
        message: The child's latest message.
        conversation_history: List of prior messages as
            [{"role": "child"|"mitra", "content": "..."}]

    Returns:
        {"marathi_text": str, "english_hint": str | None, "raw": str}
    """
    messages = [
        {"role": "system", "content": MITRA_SYSTEM_PROMPT + f"\n\nThe child's ID is: {child_id}"},
    ]

    for msg in conversation_history[-MAX_HISTORY:]:
        role = "assistant" if msg["role"] == "mitra" else "user"
        messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    raw_text = await call_llm(messages, tools=MITRA_TOOLS)
    parsed = parse_json_response(raw_text)
    parsed["raw"] = raw_text

    return parsed
