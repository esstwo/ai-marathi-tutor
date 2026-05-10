# Plugin Architecture — Implementation Summary

## Context

The capstone review (Section 4) identified that MarathiMitra's ~1,150 lines of Python backend were mostly plumbing. The actual intelligence was a 42-line prompt and a 185-line service. The recommendation: make the intelligence portable by decomposing the app into **skills** (structured instructions), **connectors** (external system glue), and a **generic orchestration loop**.

This has been implemented. The old architecture (routers → services → MCP servers) has been replaced with skills + connectors.

---

## What Was Built

### Skills (Markdown files with YAML frontmatter)

Three portable skill definitions in `backend/skills/`:

| Skill | File | Purpose |
|-------|------|---------|
| Marathi Conversation Partner | `conversation.md` | System prompt for Mitra tutor — personality, safety rules, response format, tool-calling protocol |
| Lesson Delivery | `lessons.md` | Instructions for retrieving and presenting vocabulary lessons by level |
| Progress Tracker | `progress.md` | XP rules (10/lesson, 5/min conversation), streak logic, progress summary format |

Each file has YAML frontmatter declaring `name`, `description`, `input`/`output` schemas, and `connectors` (which tools the skill needs). The Markdown body is the system prompt, used directly by the LLM.

### Connectors (plain Python functions)

Domain-grouped in `backend/connectors/`:

| Module | Functions | External System |
|--------|-----------|-----------------|
| `supabase/children.py` | `get_child_profile`, `get_children_by_parent`, `create_child`, `update_child_stats`, `verify_child_belongs_to_parent` | Supabase |
| `supabase/auth.py` | `signup_user`, `create_parent_record`, `login_user`, `refresh_session` | Supabase Auth |
| `supabase/lessons.py` | `list_lessons`, `get_lesson_by_id`, `get_lesson_context`, `record_lesson_completion` | Supabase |
| `supabase/conversations.py` | `start_conversation_record`, `save_message`, `get_conversation_messages`, `get_conversation`, `update_conversation_message_count`, `end_conversation_record` | Supabase |
| `supabase/progress.py` | `count_completed_lessons`, `count_conversations`, `get_conversations_with_ratios` | Supabase |
| `tts/google_tts.py` | `speak_marathi` | Google Cloud TTS |

These are plain functions with no HTTP/MCP concerns — the same functions are called directly by the gateway and registered as MCP tools in `mcp_server.py`.

### Core Infrastructure

| Module | Purpose |
|--------|---------|
| `core/skill_loader.py` | Parses `.md` skill files using `python-frontmatter`, produces `Skill` dataclass objects |
| `core/connector_registry.py` | Auto-discovers all connector functions, maps names → callables so skills can reference them |
| `core/llm.py` | Generic agentic loop: `run_skill(skill, messages, connectors)`. Auto-generates tool schemas from function signatures. Handles retries, error mapping, JSON parsing. Works with any skill. |

### Gateway

`backend/gateway/api.py` — single file with all REST endpoints:
- Auth, lessons, TTS, progress → call connectors directly
- Conversations → use `run_skill()` with the conversation skill

### MCP Server

`mcp_server.py` at project root — standalone server exposing:
- 22 MCP tools (all connectors + progress utilities)
- 3 MCP resources (`skill://marathi_conversation_partner`, etc.)
- 3 MCP prompts (same skills as invokable prompts)
- Runs via stdio transport for Claude Desktop / Claude Code

---

## What Was Deleted

| Old module | Lines | Replaced by |
|---|---|---|
| `routers/auth.py`, `lessons.py`, `conversations.py`, `progress.py`, `tts.py` | ~400 | `gateway/api.py` (~250) |
| `mcp/supabase_tools.py` | 289 | `connectors/supabase/*.py` |
| `mcp/supabase_server.py`, `tts_server.py`, `client.py` | ~100 | Deleted (connectors called directly) |
| `skills/mitra_conversation.py` | 185 | `core/llm.py` (generic) + `skills/conversation.md` (prompt) |
| `services/progress.py` | 150 | `gateway/progress_utils.py` |
| `services/llm_errors.py` | 25 | Bundled in `core/llm.py` |
| `services/mitra.py` | 5 | Deleted |
| `models/schemas.py` | 85 | Inlined in `gateway/api.py` |
| `prompts/mitra_system.py` | 45 | `skills/conversation.md` |
| `dependencies/auth.py` | 30 | `gateway/auth.py` |

**Net result:** ~1,150 lines → ~400 lines of Python + 3 Markdown skill files.

---

## Key Decisions

1. **Skills are Markdown, not code** — portable across web app, Claude Desktop, CLI
2. **Connectors are plain functions** — no MCP client/server for in-process calls; MCP wraps them for external access
3. **Auto-generated tool schemas** — `core/llm.py` introspects connector function signatures instead of maintaining hand-written tool manifests
4. **XP/streak logic stays deterministic** — in `gateway/progress_utils.py`, not an LLM skill invocation
5. **Single gateway file** — all REST endpoints in one place, easy to audit
