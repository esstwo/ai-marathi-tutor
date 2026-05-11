"""Deterministic XP and streak calculations.

These are pure business logic — no LLM needed. Kept as utility functions
that the gateway calls directly.
"""

import math
from datetime import date, datetime, timedelta

from backend.connectors.supabase.children import get_child_profile, update_child_stats
from backend.connectors.supabase.conversations import get_conversation
from backend.connectors.supabase.progress import (
    count_completed_lessons,
    count_conversations,
    get_conversations_with_ratios,
)
from backend.connectors.supabase.missions import get_mission_by_id
from backend.connectors.supabase.children import get_children_by_parent
from backend.db.supabase_client import supabase_admin

XP_PER_LESSON = 10
XP_PER_CONVERSATION_MINUTE = 5
XP_MISSION_MIN = 10


def _update_streak(child: dict) -> dict:
    """Compute new streak_days and streak_last_date based on today."""
    today = date.today()
    last_date_raw = child.get("streak_last_date")
    last_date = date.fromisoformat(last_date_raw) if last_date_raw else None
    current_streak = child.get("streak_days") or 0

    if last_date == today:
        return {"streak_days": current_streak, "streak_last_date": today.isoformat()}
    elif last_date == today - timedelta(days=1):
        return {"streak_days": current_streak + 1, "streak_last_date": today.isoformat()}
    else:
        return {"streak_days": 1, "streak_last_date": today.isoformat()}


def award_lesson_xp(child_id: str) -> dict:
    """Award XP for completing a lesson and update streak."""
    child = get_child_profile(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + XP_PER_LESSON

    update_child_stats(
        child_id=child_id,
        xp_total=new_xp_total,
        streak_days=streak["streak_days"],
        streak_last_date=streak["streak_last_date"],
    )

    return {
        "xp_earned": XP_PER_LESSON,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
    }


def award_conversation_xp(child_id: str, conversation_id: str) -> dict:
    """Award XP based on conversation duration and update streak."""
    conv = get_conversation(conversation_id)

    if not conv or not conv.get("ended_at"):
        child = get_child_profile(child_id)
        return {
            "xp_earned": 0,
            "xp_total": child["xp_total"],
            "streak_days": child.get("streak_days", 0),
            "duration_minutes": 0,
        }

    started = datetime.fromisoformat(conv["started_at"])
    ended = datetime.fromisoformat(conv["ended_at"])
    duration_minutes = math.ceil(max((ended - started).total_seconds(), 0) / 60)
    xp_earned = duration_minutes * XP_PER_CONVERSATION_MINUTE

    child = get_child_profile(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + xp_earned

    update_child_stats(
        child_id=child_id,
        xp_total=new_xp_total,
        streak_days=streak["streak_days"],
        streak_last_date=streak["streak_last_date"],
    )

    return {
        "xp_earned": xp_earned,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "duration_minutes": duration_minutes,
    }


def award_mission_xp(child_id: str, mission_id: str, score: int) -> dict:
    """Award XP for completing a mission based on score and update streak.

    XP = mission's xp_reward × (score / 100), minimum XP_MISSION_MIN.
    """
    mission = get_mission_by_id(mission_id)
    base_xp = mission["xp_reward"] if mission else 25
    xp_earned = max(XP_MISSION_MIN, round(base_xp * score / 100))

    child = get_child_profile(child_id)
    streak = _update_streak(child)
    new_xp_total = child["xp_total"] + xp_earned

    update_child_stats(
        child_id=child_id,
        xp_total=new_xp_total,
        streak_days=streak["streak_days"],
        streak_last_date=streak["streak_last_date"],
    )

    return {
        "xp_earned": xp_earned,
        "xp_total": new_xp_total,
        "streak_days": streak["streak_days"],
        "score": score,
    }


def _count_completed_missions(child_id: str) -> int:
    """Count missions completed by a child."""
    result = (
        supabase_admin.table("child_mission_progress")
        .select("id", count="exact")
        .eq("child_id", child_id)
        .eq("status", "completed")
        .execute()
    )
    return result.count if result.count is not None else len(result.data or [])


def get_child_progress(child_id: str) -> dict:
    """Fetch current progress stats for a child."""
    child = get_child_profile(child_id)
    return {
        "xp_total": child["xp_total"],
        "streak_days": child["streak_days"],
        "current_level": child["current_level"],
        "lessons_completed": count_completed_lessons(child_id=child_id),
        "conversations_count": count_conversations(child_id=child_id),
        "missions_completed": _count_completed_missions(child_id),
    }


def get_parent_progress(parent_id: str) -> dict:
    """Aggregate progress across all children for a parent."""
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
    conversations = get_conversations_with_ratios(child_ids)
    ratios = [c["marathi_ratio"] for c in conversations if c.get("marathi_ratio") is not None]

    return {
        "lessons_completed": count_completed_lessons(child_ids=child_ids),
        "total_lessons": 3,
        "xp_total": sum(c["xp_total"] for c in children),
        "streak_days": max(c["streak_days"] for c in children),
        "conversations_count": len(conversations),
        "avg_marathi_ratio": round(sum(ratios) / len(ratios), 2) if ratios else 0.0,
    }
