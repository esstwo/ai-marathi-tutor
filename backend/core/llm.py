"""Generic agentic loop — runs any skill by combining its prompt with connectors.

Extracts the Groq-specific agentic loop from mitra_conversation.py into a
reusable function: run_skill(skill, messages) → parsed output.
"""

import inspect
import json
import logging
import os
import time
from typing import Callable

from groq import (
    Groq,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    APIConnectionError,
)
from dotenv import load_dotenv

from backend.core.skill_loader import Skill

load_dotenv()

logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 300
MAX_TOOL_ROUNDS = 3


# ── LLM error hierarchy ─────────────────────────────────────────────────

class LLMServiceError(Exception):
    """Base exception for all LLM service errors."""

class LLMRateLimitError(LLMServiceError):
    """Raised when the LLM API returns a rate limit (429) error after retries."""

class LLMTimeoutError(LLMServiceError):
    """Raised when the LLM API times out after retries."""

class LLMAuthError(LLMServiceError):
    """Raised when the LLM API key is invalid or expired."""

class LLMContentFilterError(LLMServiceError):
    """Raised when the LLM refuses to respond due to content filtering."""

class LLMConnectionError(LLMServiceError):
    """Raised when the LLM API is unreachable after retries."""


# ── Tool schema generation ──────────────────────────────────────────────

# Python type → JSON Schema type
_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _fn_to_tool_schema(name: str, fn: Callable) -> dict:
    """Convert a connector function into an OpenAI-style tool definition.

    Uses the function's signature for parameters and docstring for description.
    """
    sig = inspect.signature(fn)
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        annotation = param.annotation
        # Resolve Optional / union types
        json_type = _TYPE_MAP.get(annotation, "string")
        properties[param_name] = {
            "type": json_type,
            "description": param_name,
        }
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": fn.__doc__ or name,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def connectors_to_tools(connectors: dict[str, Callable]) -> list[dict]:
    """Convert a dict of connector functions into OpenAI-style tool definitions."""
    return [_fn_to_tool_schema(name, fn) for name, fn in connectors.items()]


# ── Groq API call with retries ──────────────────────────────────────────

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
                raise LLMRateLimitError("LLM is rate limited — please try again shortly.") from e
        except APITimeoutError as e:
            if attempt < max_retries:
                logger.warning("Groq timeout, retrying (attempt %d/%d)", attempt + 1, max_retries)
            else:
                raise LLMTimeoutError("LLM took too long to respond — please try again.") from e
        except AuthenticationError as e:
            raise LLMAuthError("Service temporarily unavailable.") from e
        except BadRequestError as e:
            raise LLMContentFilterError("Could not generate a response for this input.") from e
        except APIConnectionError as e:
            if attempt < max_retries:
                logger.warning("Groq connection error, retrying (attempt %d/%d)", attempt + 1, max_retries)
            else:
                raise LLMConnectionError("Could not reach the language service.") from e


# ── Tool execution ──────────────────────────────────────────────────────

def _execute_tool_calls(tool_calls, connectors: dict[str, Callable]) -> list[dict]:
    """Execute tool calls against connector functions and return result messages."""
    results = []
    for tool_call in tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        fn = connectors.get(name)
        if fn:
            try:
                result = fn(**args)
                content = json.dumps(result, default=str)
            except Exception as e:
                logger.warning("Connector %s failed: %s", name, e)
                content = json.dumps({"error": str(e)})
        else:
            content = json.dumps({"error": f"Unknown connector: {name}"})

        results.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": name,
            "content": content,
        })
    return results


# ── Generic agentic loop ────────────────────────────────────────────────

def run_skill_raw(messages: list[dict], connectors: dict[str, Callable]) -> str:
    """Run the agentic tool-calling loop with given messages and connectors.

    If the LLM requests tool calls, execute them against connectors and feed
    results back. Loops until the LLM produces a final text response or max
    rounds exceeded. Returns the final text content.
    """
    tools = connectors_to_tools(connectors) if connectors else None

    for round_num in range(MAX_TOOL_ROUNDS + 1):
        response_format = None
        current_tools = tools
        if round_num == MAX_TOOL_ROUNDS:
            current_tools = None
            response_format = {"type": "json_object"}

        response = _call_groq(messages, tools=current_tools, response_format=response_format)
        message = response.choices[0].message

        if message.tool_calls and round_num < MAX_TOOL_ROUNDS:
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
            tool_results = _execute_tool_calls(message.tool_calls, connectors)
            messages.extend(tool_results)
            logger.info("Tool round %d: called %s", round_num + 1,
                        [tc.function.name for tc in message.tool_calls])
        else:
            return message.content or ""

    return ""


def parse_json_response(raw_text: str) -> dict:
    """Parse LLM's JSON response. Falls back gracefully for plain text."""
    text = raw_text.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
        return data
    except (json.JSONDecodeError, TypeError):
        return {"marathi_text": text, "english_hint": None}


def run_skill(skill: Skill, messages: list[dict],
              connectors: dict[str, Callable]) -> dict:
    """Run a skill end-to-end: inject system prompt, run agentic loop, parse output.

    Args:
        skill: The loaded Skill definition.
        messages: User/assistant messages (system prompt is prepended automatically).
        connectors: Dict of connector_name → callable for this skill.

    Returns:
        Parsed dict from the LLM's JSON response.
    """
    full_messages = [
        {"role": "system", "content": skill.system_prompt},
        *messages,
    ]

    raw_text = run_skill_raw(full_messages, connectors)
    parsed = parse_json_response(raw_text)
    parsed["raw"] = raw_text
    return parsed
