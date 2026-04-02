"""XP calculation, streak logic, and children table updates."""

import math
from datetime import date, datetime, timedelta

from backend.mcp.client import call_supabase_tool

XP_PER_LESSON = 10
XP_PER_CONVERSATION_MINUTE = 5


def _update_streak(child: dict) -> dict:
    """Compute new streak_days and streak_last_date based on today.

    Rules:
      - streak_last_date == today  -> no change
      - streak_last_date == yesterday -> increment streak_days
      - otherwise (None or older)  -> reset to 1
    """
    today = date.today()
    last_date_raw = child.get("streak_last_date")

    if last_date_raw:
        last_date = date.fromisoformat(last_date_raw)
    else:
        last_date = None

    current_streak = child.get("streak_days") or 0

    if last_date == today:
        return {"streak_days": current_streak, "streak_last_date": today.isoformat()}
    elif last_date == today - timedelta(days=1):
        return {"streak_days": current_streak + 1, "streak_last_date": today.isoformat()}
    else:
        return {"streak_days": 1, "streak_last_date": today.isoformat()}


async def award_lesson_xp(child_id: str) -> dict:
    """Award XP for completing a lesson and update streak.

    Returns:
        {"xp_earned": int, "xp_total": int, "streak_days": int}
    """
    child = await call_supabase_tool("get_child_profile", {"child_id": child_id})
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + XP_PER_LESSON

    await call_supabase_tool("update_child_stats", {
        "child_id": child_id,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "streak_last_date": streak["streak_last_date"],
    })

    return {
        "xp_earned": XP_PER_LESSON,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
    }


async def award_conversation_xp(child_id: str, conversation_id: str) -> dict:
    """Award XP based on conversation duration (rounded up to nearest minute) and update streak.

    Returns:
        {"xp_earned": int, "xp_total": int, "streak_days": int, "duration_minutes": int}
    """
    conv = await call_supabase_tool("get_conversation", {"conversation_id": conversation_id})

    if not conv or not conv.get("ended_at"):
        child = await call_supabase_tool("get_child_profile", {"child_id": child_id})
        return {"xp_earned": 0, "xp_total": child["xp_total"],
                "streak_days": child.get("streak_days", 0),
                "duration_minutes": 0}

    started = datetime.fromisoformat(conv["started_at"])
    ended = datetime.fromisoformat(conv["ended_at"])
    duration_seconds = (ended - started).total_seconds()
    duration_minutes = math.ceil(max(duration_seconds, 0) / 60)

    xp_earned = duration_minutes * XP_PER_CONVERSATION_MINUTE

    child = await call_supabase_tool("get_child_profile", {"child_id": child_id})
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + xp_earned

    await call_supabase_tool("update_child_stats", {
        "child_id": child_id,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "streak_last_date": streak["streak_last_date"],
    })

    return {
        "xp_earned": xp_earned,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "duration_minutes": duration_minutes,
    }


async def get_parent_progress(parent_id: str) -> dict:
    """Aggregate progress across all children belonging to a parent."""
    children = await call_supabase_tool("get_children_by_parent", {"parent_id": parent_id})

    if not children:
        return {
            "lessons_completed": 0,
            "total_lessons": 3,
            "xp_total": 0,
            "streak_days": 0,
            "conversations_count": 0,
            "avg_marathi_ratio": 0.0,
        }

    child_ids = [c["id"] for c in children]

    xp_total = sum(c["xp_total"] for c in children)
    streak_days = max(c["streak_days"] for c in children)

    lessons_completed = await call_supabase_tool("count_completed_lessons", {"child_ids": child_ids})

    conversations = await call_supabase_tool("get_conversations_with_ratios", {"child_ids": child_ids})
    conversations_count = len(conversations)
    ratios = [c["marathi_ratio"] for c in conversations if c.get("marathi_ratio") is not None]
    avg_marathi_ratio = round(sum(ratios) / len(ratios), 2) if ratios else 0.0

    return {
        "lessons_completed": lessons_completed,
        "total_lessons": 3,
        "xp_total": xp_total,
        "streak_days": streak_days,
        "conversations_count": conversations_count,
        "avg_marathi_ratio": avg_marathi_ratio,
    }


async def get_progress(child_id: str) -> dict:
    """Fetch current progress stats for a child."""
    child = await call_supabase_tool("get_child_profile", {"child_id": child_id})

    lessons_completed = await call_supabase_tool("count_completed_lessons", {"child_id": child_id})
    conversations_count = await call_supabase_tool("count_conversations", {"child_id": child_id})

    return {
        "xp_total": child["xp_total"],
        "streak_days": child["streak_days"],
        "current_level": child["current_level"],
        "lessons_completed": lessons_completed,
        "conversations_count": conversations_count,
    }
