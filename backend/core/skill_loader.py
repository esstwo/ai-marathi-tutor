"""Skill loader — discovers and loads Markdown skill definitions.

Each skill is a .md file with YAML frontmatter (metadata) and a Markdown body
(the system prompt). This mirrors the Claude skill file format.
"""

from dataclasses import dataclass
from pathlib import Path

import frontmatter


@dataclass
class Skill:
    name: str
    description: str
    system_prompt: str          # The Markdown body — used directly as the LLM system prompt
    input_schema: dict
    output_schema: dict
    connector_names: list[str]  # Which connectors this skill needs
    max_tokens: int = 300       # Override global MAX_TOKENS for skills that need longer output


def load_skill(path: Path) -> Skill:
    """Load a single .md skill file."""
    post = frontmatter.load(str(path))
    return Skill(
        name=post["name"],
        description=post["description"],
        system_prompt=post.content,
        input_schema=post.get("input", {}),
        output_schema=post.get("output", {}),
        connector_names=post.get("connectors", []),
        max_tokens=post.get("max_tokens", 300),
    )


def load_skills(skills_dir: Path = Path("backend/skills")) -> dict[str, Skill]:
    """Auto-discover all .md files in skills/ and return loaded Skill objects."""
    skills = {}
    for path in sorted(skills_dir.glob("*.md")):
        skill = load_skill(path)
        skills[skill.name] = skill
    return skills
