"""Progress query connectors — counts and aggregations for reporting."""

from backend.db.supabase_client import supabase_admin


def count_completed_lessons(child_id: str | None = None, child_ids: list[str] | None = None) -> int:
    """Count completed lessons for one child or a list of children."""
    query = (
        supabase_admin.table("child_lesson_progress")
        .select("id", count="exact")
        .eq("status", "completed")
    )
    if child_id:
        query = query.eq("child_id", child_id)
    elif child_ids:
        query = query.in_("child_id", child_ids)
    return query.execute().count or 0


def count_conversations(child_id: str | None = None, child_ids: list[str] | None = None) -> int:
    """Count conversations for one child or a list of children."""
    query = supabase_admin.table("conversations").select("id", count="exact")
    if child_id:
        query = query.eq("child_id", child_id)
    elif child_ids:
        query = query.in_("child_id", child_ids)
    return query.execute().count or 0


def get_conversations_with_ratios(child_ids: list[str]) -> list[dict]:
    """Fetch conversations with marathi_ratio for parent dashboard."""
    result = (
        supabase_admin.table("conversations")
        .select("id, marathi_ratio")
        .in_("child_id", child_ids)
        .execute()
    )
    return result.data or []
