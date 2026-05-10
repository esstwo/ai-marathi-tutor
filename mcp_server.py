"""MCP Server — expose MarathiMitra skills and connectors for Claude Desktop.

Run: python mcp_server.py
Connects via stdio transport (Claude Desktop / Claude Code).

Configure in claude_desktop_config.json:
{
  "mcpServers": {
    "marathi-tutor": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "GROQ_API_KEY": "...",
        "SUPABASE_URL": "...",
        "SUPABASE_KEY": "...",
        "SUPABASE_SERVICE_KEY": "...",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": "..."
      }
    }
  }
}
"""

from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP

from backend.core.skill_loader import load_skills

# Connectors — each becomes an MCP tool
from backend.connectors.supabase.children import (
    get_child_profile,
    get_children_by_parent,
    create_child,
    update_child_stats,
)
from backend.connectors.supabase.lessons import (
    list_lessons,
    get_lesson_by_id,
    get_lesson_context,
    record_lesson_completion,
)
from backend.connectors.supabase.conversations import (
    start_conversation_record,
    save_message,
    get_conversation_messages,
    get_conversation,
    update_conversation_message_count,
    end_conversation_record,
)
from backend.connectors.supabase.progress import (
    count_completed_lessons,
    count_conversations,
    get_conversations_with_ratios,
)
from backend.connectors.tts.google_tts import speak_marathi

from backend.gateway.progress_utils import (
    award_lesson_xp,
    award_conversation_xp,
    get_child_progress,
    get_parent_progress,
)


mcp = FastMCP(
    "MarathiMitra",
    description="AI Marathi tutor for diaspora kids — skills, lessons, progress, and TTS",
)

# ── Register connectors as tools ────────────────────────────────────────

# Children
mcp.tool()(get_child_profile)
mcp.tool()(get_children_by_parent)
mcp.tool()(create_child)
mcp.tool()(update_child_stats)

# Lessons
mcp.tool()(list_lessons)
mcp.tool()(get_lesson_by_id)
mcp.tool()(get_lesson_context)
mcp.tool()(record_lesson_completion)

# Conversations
mcp.tool()(start_conversation_record)
mcp.tool()(save_message)
mcp.tool()(get_conversation_messages)
mcp.tool()(get_conversation)
mcp.tool()(update_conversation_message_count)
mcp.tool()(end_conversation_record)

# Progress
mcp.tool()(count_completed_lessons)
mcp.tool()(count_conversations)
mcp.tool()(get_conversations_with_ratios)
mcp.tool()(award_lesson_xp)
mcp.tool()(award_conversation_xp)
mcp.tool()(get_child_progress)
mcp.tool()(get_parent_progress)

# TTS
mcp.tool()(speak_marathi)


# ── Register skills as resources (prompts Claude can read) ──────────────

_skills = load_skills()

for skill in _skills.values():
    # Use a factory to capture the skill variable correctly in the closure
    def _make_resource(s):
        @mcp.resource(f"skill://{s.name}", description=s.description)
        def _resource():
            return s.system_prompt
        return _resource
    _make_resource(skill)


# ── Register skill prompts as MCP prompts ───────────────────────────────

for skill in _skills.values():
    def _make_prompt(s):
        @mcp.prompt(name=s.name, description=s.description)
        def _prompt():
            return s.system_prompt
        return _prompt
    _make_prompt(skill)


if __name__ == "__main__":
    mcp.run()
