"""Child profile connectors — read and update child records."""

from backend.db.supabase_client import supabase_admin


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


def get_children_by_parent(parent_id: str) -> list[dict]:
    """Fetch all children belonging to a parent."""
    result = (
        supabase_admin.table("children")
        .select("id, name, age, avatar, current_level, xp_total, streak_days")
        .eq("parent_id", parent_id)
        .execute()
    )
    return result.data or []


def create_child(parent_id: str, name: str, age: int, avatar: str = "\U0001f418") -> dict | None:
    """Insert a new child record."""
    result = (
        supabase_admin.table("children")
        .insert({
            "parent_id": parent_id,
            "name": name,
            "age": age,
            "avatar": avatar,
        })
        .execute()
    )
    return result.data[0] if result.data else None


def update_child_stats(child_id: str, xp_total: int, streak_days: int, streak_last_date: str) -> dict:
    """Update XP and streak fields on a child record."""
    supabase_admin.table("children").update(
        {
            "xp_total": xp_total,
            "streak_days": streak_days,
            "streak_last_date": streak_last_date,
        }
    ).eq("id", child_id).execute()
    return {"ok": True}


def verify_child_belongs_to_parent(child_id: str, parent_id: str) -> bool:
    """Check if a child belongs to a parent."""
    result = (
        supabase_admin.table("children")
        .select("id")
        .eq("id", child_id)
        .eq("parent_id", parent_id)
        .execute()
    )
    return bool(result.data)
