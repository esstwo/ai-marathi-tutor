"""Rate-limit connectors — persisted per-IP signup throttling."""

from datetime import datetime, timezone, timedelta

from backend.db.supabase_client import supabase_admin


def count_recent_signup_attempts(ip: str, since: datetime) -> int:
    """Count signup attempts from this IP since the given UTC timestamp."""
    result = (
        supabase_admin.table("signup_attempts")
        .select("ip", count="exact")
        .eq("ip", ip)
        .gte("attempted_at", since.isoformat())
        .execute()
    )
    return result.count or 0


def record_signup_attempt(ip: str) -> None:
    """Append a signup attempt row for this IP."""
    supabase_admin.table("signup_attempts").insert(
        {"ip": ip, "attempted_at": datetime.now(timezone.utc).isoformat()}
    ).execute()


def cleanup_old_signup_attempts(ip: str, older_than_hours: int = 24) -> None:
    """Opportunistically prune old rows for this IP to keep the table small."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    supabase_admin.table("signup_attempts").delete().eq("ip", ip).lt(
        "attempted_at", cutoff.isoformat()
    ).execute()
