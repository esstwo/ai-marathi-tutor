# Plugin Architecture Plan

## Core Insight

Everything MarathiMitra does decomposes into **skills**, **system instructions**, and **connectors**. The current codebase is ~1,150 lines of Python backend and ~2,500 lines of React frontend. Most of that is plumbing: routing HTTP, managing state, rendering UI. The actual intelligence is a 42-line prompt (`mitra_system.py`) and a 185-line service (`mitra_conversation.py`). The rest is infrastructure.

**The shift:** Instead of building a full-stack app that happens to use an LLM, build a system where the LLM is the application and skills/connectors extend its capabilities. Skills are portable — they can run in Claude Desktop, a CLI, or a web app. Code only exists for things that need external system access.

---

## Current Architecture (what we're moving away from)

```
React Frontend (2,500 lines)
  → FastAPI Routers (HTTP gateway, lots of orchestration logic)
    → Skills (just mitra_conversation.py)
      → MCP Client (in-process)
        → MCP Servers (22 flat Supabase tools + 1 TTS tool)
          → External: Supabase, Google TTS, Groq
```

### Problems
- Routers contain orchestration logic that belongs in skills (save msg → fetch history → call LLM → save response → update count)
- 22 tools in one flat file, no grouping by capability
- Skills are code-heavy — the prompt is the intelligence, but it's buried under Python plumbing
- Not portable — the Mitra skill only works inside this FastAPI app
- Adding a new skill means touching routers, tools, MCP server, and services

---

## The Three Skills

The app has three core skills hiding inside it. A **skill** is a structured instruction that tells an AI how to convert a specific input into a specific output.

### Skill 1: Marathi Conversation Partner
- **Input:** Child's message (text, possibly transliterated), their age/level, recent lesson vocabulary
- **Output:** Marathi response in Devanagari with optional English hint (`{marathi_text, english_hint}`)
- **Current location:** `prompts/mitra_system.py` (42-line prompt) + `skills/mitra_conversation.py` (185-line service)
- **As a skill:** The system instructions, output format spec, and few-shot examples packaged as a self-contained definition. The agentic loop (call tools → feed back → get response) is generic infrastructure, not part of the skill.
- **Connectors needed:** `get_child_profile`, `get_lesson_context` (read-only data fetching)

### Skill 2: Lesson Delivery
- **Input:** Child's current level
- **Output:** Structured vocabulary lesson with words, pronunciations, quiz questions
- **Current location:** Static JSON in `content/` served via `routers/lessons.py` + `mcp/supabase_tools.py`
- **As a skill:** A prompt that retrieves lessons from a data source and formats them for conversation context. Could also generate lessons dynamically for topics not in the static set.
- **Connectors needed:** `list_lessons`, `get_lesson_by_id`, `record_lesson_completion`

### Skill 3: Progress Tracker
- **Input:** Child's activity history (lessons completed, conversations, XP)
- **Output:** Progress summary with streak, level, suggestions for parent
- **Current location:** `services/progress.py` (150 lines of XP/streak calculation)
- **As a skill:** A tool the LLM calls to read and update progress data. The XP/streak business logic (10 XP per lesson, 5 XP per conversation minute, consecutive-day streaks) becomes part of the skill definition so the LLM can explain and apply it.
- **Connectors needed:** `get_child_profile`, `update_child_stats`, `count_completed_lessons`, `count_conversations`

---

## Proposed Structure

```
backend/
├── main.py                         # Thin app factory — loads skills, exposes MCP server
│
├── core/                           # Generic infrastructure (not MarathiMitra-specific)
│   ├── llm.py                      # Agentic loop: send prompt → tool calls → execute → loop
│   ├── skill_loader.py             # Discovers and loads skill definitions from skills/
│   └── db.py                       # Supabase client
│
├── skills/                         # Each skill = a Markdown file with YAML frontmatter
│   ├── conversation.md             # Skill 1: system prompt, output spec, few-shot examples
│   ├── lessons.md                  # Skill 2: lesson delivery instructions
│   └── progress.md                 # Skill 3: progress tracking rules + XP logic
│
├── connectors/                     # Minimal code that bridges skills to external systems
│   ├── supabase/                   # All Supabase operations as MCP tools
│   │   ├── children.py             # get_child_profile, create_child, update_child_stats
│   │   ├── lessons.py              # list_lessons, get_lesson_by_id, get_lesson_context
│   │   ├── conversations.py        # start/end conversation, save/get messages
│   │   └── progress.py             # count_completed_lessons, count_conversations
│   └── tts/
│       └── google_tts.py           # speak_marathi
│
└── gateway/                        # Optional thin HTTP layer (only if serving a web frontend)
    └── api.py                      # Translates HTTP requests → skill invocations
```

---

## What a Skill Definition Looks Like

Skill files are Markdown with YAML frontmatter — the same format as Claude skill files. The frontmatter carries structured metadata (input/output schema, connectors). The Markdown body *is* the system prompt — no quoting, no escaping, no indentation issues.

````markdown
<!-- skills/conversation.md -->
---
name: marathi_conversation_partner
description: Friendly Marathi tutor for diaspora kids (ages 5-12)
input:
  child_id: string       # UUID — used to fetch profile and lesson context via tools
  message: string        # The child's latest message
  history: list          # Prior messages [{role, content}]
output:
  format: json
  schema:
    marathi_text: string  # Main response in Devanagari
    english_hint: string? # Optional English hint
connectors:
  - get_child_profile     # Read-only: name, age, level, XP, streak
  - get_lesson_context    # Read-only: current lesson vocabulary
---

You are Mitra, a friendly Marathi tutor for kids.

## Your Personality
- Patient and never judgmental — celebrate effort, not just correctness.
- Use simple, everyday Marathi — the kind spoken in homes, not textbooks.
- Gently correct mistakes by repeating the correct form naturally.
- Adapt language complexity to the child's demonstrated level.
- Code-switch strategically — English hints when stuck, then model the Marathi.

## Conversation Rules
- Always respond primarily in Marathi, using Devanagari script.
- If the child speaks English, acknowledge and model Marathi equivalent.
- Keep sentences short, vocabulary within demonstrated level.
- Introduce one new word per 3-4 exchanges, with context clues.

## Safety
- ONLY discuss age-appropriate topics about Marathi language and Indian culture.
- Redirect off-topic: "चला, आपण मराठी शिकूया!"
- Never share opinions on politics, religion, or controversial topics.

## Getting Context
1. Call get_child_profile to learn name, age, current level.
2. Call get_lesson_context to find current vocabulary to weave in.
Use this to tailor language complexity and topic.

Level guide:
- Level 1: Beginner — first words
- Level 2: Elementary — simple sentences
- Level 3: Intermediate — short conversations
- Level 4: Advanced — storytelling and discussion

## Response Format
Always respond as JSON: `{"marathi_text": "...", "english_hint": "..."}`
Do NOT include any text outside the JSON object.
````

---

## How the Skill Loader Works

Uses `python-frontmatter` to parse Markdown skill files. The YAML frontmatter becomes structured metadata, the Markdown body becomes the system prompt.

```python
# core/skill_loader.py
import frontmatter
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Skill:
    name: str
    description: str
    system_prompt: str          # The Markdown body — used directly as the LLM system prompt
    input_schema: dict
    output_schema: dict
    connector_names: list[str]  # which connectors this skill needs

def load_skill(path: Path) -> Skill:
    """Load a single .md skill file."""
    post = frontmatter.load(str(path))
    return Skill(
        name=post["name"],
        description=post["description"],
        system_prompt=post.content,      # Markdown body = the prompt
        input_schema=post.get("input", {}),
        output_schema=post.get("output", {}),
        connector_names=post.get("connectors", []),
    )

def load_skills(skills_dir: Path = Path("backend/skills")) -> dict[str, Skill]:
    """Auto-discover all .md files in skills/ and return loaded Skill objects."""
    skills = {}
    for path in skills_dir.glob("*.md"):
        skill = load_skill(path)
        skills[skill.name] = skill
    return skills
```

Dependency: `pip install python-frontmatter`

---

## How Connectors Work

Connectors are the only code you write. Each is a plain function registered as an MCP tool.

```python
# connectors/supabase/children.py
from backend.core.db import supabase_admin

def get_child_profile(child_id: str) -> dict | None:
    """Fetch child's name, age, level, XP, streak."""
    result = (
        supabase_admin.table("children")
        .select("name, age, current_level, xp_total, streak_days, streak_last_date")
        .eq("id", child_id)
        .single()
        .execute()
    )
    return result.data
```

Same functions as today, but they're understood as connectors — minimal glue between the LLM and external systems. No business logic in here; the skill definition tells the LLM how to interpret and use the data.

---

## How a Request Flows

### Today (code-heavy)
```
POST /conversations/{id}/message
  → Router: verify auth
  → Router: save child message to DB
  → Router: fetch conversation history from DB
  → Skill: build prompt + call LLM with tools
  → LLM: call get_child_profile, get_lesson_context
  → Skill: parse JSON response
  → Router: save Mitra response to DB
  → Router: update message count
  → Router: return response
```
The router does 6 steps of orchestration. The skill does 2.

### New (LLM-as-orchestrator)
```
POST /api/invoke  {skill: "conversation", input: {child_id, message, history}}
  → Gateway: verify auth, load skill definition
  → Core LLM: run agentic loop with skill's prompt + skill's connectors
    → LLM decides: call get_child_profile → call get_lesson_context
    → LLM decides: call save_message (child's message)
    → LLM generates response
    → LLM decides: call save_message (its own response)
  → Gateway: return output matching skill's output schema
```
The LLM orchestrates everything. The gateway is 3 lines. Adding "also update message count" means updating the skill's prompt, not writing Python.

---

## Portability: MCP Server Export

Because skills are Markdown definitions and connectors are MCP tools, the entire app can be exposed as an MCP server for Claude Desktop:

```python
# mcp_server.py
from fastmcp import FastMCP
from backend.core.skill_loader import load_skills
from backend.connectors import all_connectors

mcp = FastMCP("MarathiMitra")

# Register all connectors as tools
for connector in all_connectors:
    mcp.tool()(connector)

# Register skills as resources (prompts the LLM can read)
for skill in load_skills().values():
    @mcp.resource(f"skill://{skill.name}")
    def get_skill():
        return skill.system_prompt

# Run: python mcp_server.py → connects to Claude Desktop via stdio
```

Now Claude Desktop can be the Mitra tutor, using the same skills and connectors, with zero web infrastructure.

---

## Migration: What Changes

| Current code | What happens to it |
|---|---|
| `prompts/mitra_system.py` (42 lines) | → `skills/conversation.md` (the product) |
| `skills/mitra_conversation.py` (185 lines) | → mostly deleted; agentic loop moves to `core/llm.py`, prompt moves to Markdown |
| `services/progress.py` (150 lines) | → XP/streak rules move to `skills/progress.md`; raw DB calls stay in `connectors/` |
| `mcp/supabase_tools.py` (289 lines) | → split into `connectors/supabase/*.py` (same code, better organized) |
| `mcp/tts_tools.py` (18 lines) | → `connectors/tts/google_tts.py` |
| `mcp/supabase_server.py`, `tts_server.py`, `client.py` | → deleted (connectors register directly) |
| `routers/*.py` (~400 lines total) | → `gateway/api.py` (~50 lines) or deleted if MCP-only |
| `services/llm_errors.py` | → `core/llm.py` |
| `dependencies/auth.py` | → `gateway/api.py` (auth middleware) |

**Net reduction:** ~1,150 lines → ~400 lines of code + 3 Markdown skill files.

---

## Implementation Order

### Phase 1: Extract skill definitions (no behavior change)
1. Create `skills/conversation.md` — move prompt from `mitra_system.py` into Markdown body, add frontmatter
2. Create `skills/lessons.md` — define lesson delivery skill
3. Create `skills/progress.md` — encode XP/streak rules as instructions
4. Create `core/skill_loader.py` — frontmatter parser that produces Skill objects
5. Add `python-frontmatter` to `requirements.txt`

### Phase 2: Reorganize connectors
5. Create `connectors/supabase/` — split `supabase_tools.py` by domain
6. Create `connectors/tts/` — move TTS tool
7. Wire connectors into a registry that skills can reference by name

### Phase 3: Generic agentic loop
8. Create `core/llm.py` — extract the agentic loop from `mitra_conversation.py` into a generic function: `run_skill(skill, input, connectors) → output`
9. Update conversation flow to use `run_skill()` instead of hard-coded `chat()`/`greet()`

### Phase 4: Thin gateway
10. Replace `routers/*.py` with a single `gateway/api.py` that maps HTTP → skill invocations
11. Move auth to gateway middleware

### Phase 5: MCP server export
12. Create `mcp_server.py` — expose skills + connectors for Claude Desktop
13. Test end-to-end: Claude Desktop as Mitra tutor

### Phase 6: Cleanup
14. Delete old directories: `mcp/`, `routers/`, `services/`, `prompts/`, `dependencies/`
15. Update frontend API calls to match new gateway endpoints
