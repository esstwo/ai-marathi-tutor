"""Usage counter connectors — per-child, per-day LLM call tracking.

Persisted in Supabase so counters survive deploys and are shared across workers.
Atomic increment runs in a Postgres function (`increment_usage_counter`).
"""

from datetime import datetime, timezone

from backend.db.supabase_client import supabase_admin


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def increment_child_daily_calls(child_id: str) -> int:
    """Atomically increment today's LLM call counter for a child. Returns the new count."""
    result = supabase_admin.rpc(
        "increment_usage_counter",
        {"p_child_id": child_id, "p_date": _today_utc()},
    ).execute()
    return result.data if isinstance(result.data, int) else int(result.data or 0)


def get_child_daily_calls(child_id: str) -> int:
    """Return today's LLM call count for a child (0 if no row yet)."""
    result = (
        supabase_admin.table("usage_counters")
        .select("llm_calls")
        .eq("child_id", child_id)
        .eq("date", _today_utc())
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        return 0
    return result.data.get("llm_calls", 0)
