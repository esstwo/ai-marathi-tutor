"""Mission connectors — create, list, and track mission progress."""

import json
from datetime import datetime, timezone

from backend.db.supabase_client import supabase_admin


def list_missions(level: int) -> list[dict]:
    """Fetch all missions for a level, ordered by creation date."""
    result = (
        supabase_admin.table("missions")
        .select("*")
        .eq("level", level)
        .order("created_at")
        .execute()
    )
    return result.data or []


def get_mission_by_id(mission_id: str) -> dict | None:
    """Fetch a single mission by ID."""
    result = (
        supabase_admin.table("missions")
        .select("*")
        .eq("id", mission_id)
        .single()
        .execute()
    )
    return result.data


def create_mission(
    level: int,
    title: str,
    title_english: str,
    scenario: str,
    steps: list[dict],
    required_vocab: list[str],
    xp_reward: int = 25,
) -> dict:
    """Save an LLM-generated mission to the shared missions table."""
    result = (
        supabase_admin.table("missions")
        .insert({
            "level": level,
            "title": title,
            "title_english": title_english,
            "scenario": scenario,
            "steps": json.dumps(steps) if isinstance(steps, list) else steps,
            "required_vocab": json.dumps(required_vocab) if isinstance(required_vocab, list) else required_vocab,
            "xp_reward": xp_reward,
        })
        .execute()
    )
    return result.data[0] if result.data else {}


def get_child_mission_progress(child_id: str) -> list[dict]:
    """Fetch all mission progress records for a child, joined with mission data."""
    result = (
        supabase_admin.table("child_mission_progress")
        .select("*, missions(*)")
        .eq("child_id", child_id)
        .execute()
    )
    return result.data or []


def get_mission_progress(child_id: str, mission_id: str) -> dict | None:
    """Fetch progress for a specific child + mission."""
    result = (
        supabase_admin.table("child_mission_progress")
        .select("*")
        .eq("child_id", child_id)
        .eq("mission_id", mission_id)
        .execute()
    )
    return result.data[0] if result.data else None


def upsert_mission_progress(
    child_id: str, mission_id: str, status: str, score: int = 0
) -> dict:
    """Create or update mission progress for a child."""
    existing = (
        supabase_admin.table("child_mission_progress")
        .select("id")
        .eq("child_id", child_id)
        .eq("mission_id", mission_id)
        .execute()
    )

    now = datetime.now(timezone.utc).isoformat()
    completed_at = now if status == "completed" else None

    if existing.data:
        result = (
            supabase_admin.table("child_mission_progress")
            .update({"status": status, "score": score, "completed_at": completed_at})
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = (
            supabase_admin.table("child_mission_progress")
            .insert({
                "child_id": child_id,
                "mission_id": mission_id,
                "status": status,
                "score": score,
                "completed_at": completed_at,
            })
            .execute()
        )
    return result.data[0] if result.data else {}
