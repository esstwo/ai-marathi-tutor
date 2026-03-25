"""XP calculation, streak logic, and children table updates."""

import math
from datetime import date, timedelta

from backend.db.supabase_client import supabase_admin

XP_PER_LESSON = 10
XP_PER_CONVERSATION_MINUTE = 5


def _get_child(child_id: str) -> dict:
    result = (
        supabase_admin.table("children")
        .select("xp_total, streak_days, streak_last_date")
        .eq("id", child_id)
        .single()
        .execute()
    )
    return result.data


def _update_streak(child: dict) -> dict:
    """Compute new streak_days and streak_last_date based on today.

    Rules:
      - streak_last_date == today  → no change
      - streak_last_date == yesterday → increment streak_days
      - otherwise (None or older)  → reset to 1
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
    child = _get_child(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + XP_PER_LESSON

    supabase_admin.table("children").update(
        {
            "xp_total": new_xp_total,
            "streak_days": streak["streak_days"],
            "streak_last_date": streak["streak_last_date"],
        }
    ).eq("id", child_id).execute()

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
    conv = (
        supabase_admin.table("conversations")
        .select("started_at, ended_at")
        .eq("id", conversation_id)
        .single()
        .execute()
    )

    if not conv.data or not conv.data.get("ended_at"):
        return {"xp_earned": 0, "xp_total": _get_child(child_id)["xp_total"],
                "streak_days": _get_child(child_id).get("streak_days", 0),
                "duration_minutes": 0}

    from datetime import datetime
    started = datetime.fromisoformat(conv.data["started_at"])
    ended = datetime.fromisoformat(conv.data["ended_at"])
    duration_seconds = (ended - started).total_seconds()
    duration_minutes = math.ceil(max(duration_seconds, 0) / 60)

    xp_earned = duration_minutes * XP_PER_CONVERSATION_MINUTE

    child = _get_child(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + xp_earned

    supabase_admin.table("children").update(
        {
            "xp_total": new_xp_total,
            "streak_days": streak["streak_days"],
            "streak_last_date": streak["streak_last_date"],
        }
    ).eq("id", child_id).execute()

    return {
        "xp_earned": xp_earned,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "duration_minutes": duration_minutes,
    }


def get_progress(child_id: str) -> dict:
    """Fetch current progress stats for a child.

    Returns:
        {"xp_total": int, "streak_days": int, "current_level": int,
         "lessons_completed": int, "conversations_count": int}
    """
    child = (
        supabase_admin.table("children")
        .select("xp_total, streak_days, current_level")
        .eq("id", child_id)
        .single()
        .execute()
    ).data

    lessons_completed = (
        supabase_admin.table("child_lesson_progress")
        .select("id", count="exact")
        .eq("child_id", child_id)
        .eq("status", "completed")
        .execute()
    ).count or 0

    conversations_count = (
        supabase_admin.table("conversations")
        .select("id", count="exact")
        .eq("child_id", child_id)
        .execute()
    ).count or 0

    return {
        "xp_total": child["xp_total"],
        "streak_days": child["streak_days"],
        "current_level": child["current_level"],
        "lessons_completed": lessons_completed,
        "conversations_count": conversations_count,
    }
