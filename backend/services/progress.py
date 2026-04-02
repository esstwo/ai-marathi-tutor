"""XP calculation, streak logic, and children table updates."""

import math
from datetime import date, datetime, timedelta

from backend.mcp.supabase_tools import (
    get_child_profile,
    get_children_by_parent,
    get_conversation,
    update_child_stats,
    count_completed_lessons,
    count_conversations,
    get_conversations_with_ratios,
)

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


def award_lesson_xp(child_id: str) -> dict:
    """Award XP for completing a lesson and update streak.

    Returns:
        {"xp_earned": int, "xp_total": int, "streak_days": int}
    """
    child = get_child_profile(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + XP_PER_LESSON

    update_child_stats(child_id, new_xp_total, streak["streak_days"], streak["streak_last_date"])

    return {
        "xp_earned": XP_PER_LESSON,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
    }


def award_conversation_xp(child_id: str, conversation_id: str) -> dict:
    """Award XP based on conversation duration (rounded up to nearest minute) and update streak.

    Returns:
        {"xp_earned": int, "xp_total": int, "streak_days": int, "duration_minutes": int}
    """
    conv = get_conversation(conversation_id)

    if not conv or not conv.get("ended_at"):
        child = get_child_profile(child_id)
        return {"xp_earned": 0, "xp_total": child["xp_total"],
                "streak_days": child.get("streak_days", 0),
                "duration_minutes": 0}

    started = datetime.fromisoformat(conv["started_at"])
    ended = datetime.fromisoformat(conv["ended_at"])
    duration_seconds = (ended - started).total_seconds()
    duration_minutes = math.ceil(max(duration_seconds, 0) / 60)

    xp_earned = duration_minutes * XP_PER_CONVERSATION_MINUTE

    child = get_child_profile(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + xp_earned

    update_child_stats(child_id, new_xp_total, streak["streak_days"], streak["streak_last_date"])

    return {
        "xp_earned": xp_earned,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "duration_minutes": duration_minutes,
    }


def get_parent_progress(parent_id: str) -> dict:
    """Aggregate progress across all children belonging to a parent.

    Returns:
        {"lessons_completed": int, "total_lessons": 3, "xp_total": int,
         "streak_days": int, "conversations_count": int, "avg_marathi_ratio": float}
    """
    children = get_children_by_parent(parent_id)

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

    lessons_completed = count_completed_lessons(child_ids=child_ids)

    conversations = get_conversations_with_ratios(child_ids)
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


def get_progress(child_id: str) -> dict:
    """Fetch current progress stats for a child.

    Returns:
        {"xp_total": int, "streak_days": int, "current_level": int,
         "lessons_completed": int, "conversations_count": int}
    """
    child = get_child_profile(child_id)

    lessons_completed = count_completed_lessons(child_id=child_id)
    conversations_count = count_conversations(child_id=child_id)

    return {
        "xp_total": child["xp_total"],
        "streak_days": child["streak_days"],
        "current_level": child["current_level"],
        "lessons_completed": lessons_completed,
        "conversations_count": conversations_count,
    }
