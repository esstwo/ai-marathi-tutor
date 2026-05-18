"""Auth connectors — signup, login, token refresh, parent records."""

from backend.db.supabase_client import supabase, supabase_admin


def signup_user(email: str, password: str, captcha_token: str | None = None):
    """Sign up a new user via Supabase Auth. Lets AuthApiError propagate.

    If captcha_token is provided and Supabase Auth has CAPTCHA enabled, Supabase
    will verify the token with Cloudflare (or hCaptcha) using the configured
    secret and reject the signup if invalid.
    """
    payload: dict = {"email": email, "password": password}
    if captcha_token:
        payload["options"] = {"captcha_token": captcha_token}
    return supabase.auth.sign_up(payload)


def create_parent_record(user_id: str, email: str, name: str) -> dict | None:
    """Insert a parent record."""
    result = (
        supabase_admin.table("parents")
        .insert({"id": user_id, "email": email, "name": name})
        .execute()
    )
    return result.data[0] if result.data else None


def login_user(email: str, password: str, captcha_token: str | None = None):
    """Authenticate a user via Supabase Auth. Lets AuthApiError propagate.

    Supabase's CAPTCHA protection (when enabled) applies to all auth endpoints,
    so login must forward the token too — same shape as signup.
    """
    payload: dict = {"email": email, "password": password}
    if captcha_token:
        payload["options"] = {"captcha_token": captcha_token}
    return supabase.auth.sign_in_with_password(payload)


def refresh_session(refresh_token: str):
    """Refresh a session using a refresh token. Lets AuthApiError propagate."""
    return supabase.auth.refresh_session(refresh_token)
