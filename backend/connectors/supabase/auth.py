"""Auth connectors — signup, login, token refresh, parent records."""

from backend.db.supabase_client import supabase, supabase_admin


def signup_user(email: str, password: str):
    """Sign up a new user via Supabase Auth. Lets AuthApiError propagate."""
    return supabase.auth.sign_up({"email": email, "password": password})


def create_parent_record(user_id: str, email: str, name: str) -> dict | None:
    """Insert a parent record."""
    result = (
        supabase_admin.table("parents")
        .insert({"id": user_id, "email": email, "name": name})
        .execute()
    )
    return result.data[0] if result.data else None


def login_user(email: str, password: str):
    """Authenticate a user via Supabase Auth. Lets AuthApiError propagate."""
    return supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )


def refresh_session(refresh_token: str):
    """Refresh a session using a refresh token. Lets AuthApiError propagate."""
    return supabase.auth.refresh_session(refresh_token)
