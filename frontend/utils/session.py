"""Auth + session state management."""

import streamlit as st

DEFAULTS = {
    "access_token": None,
    "user_id": None,
    "child_created": False,
    "child_id": None,
    "conversation_id": None,
    "chat_messages": [],
    # Lesson state
    "lesson_data": None,
    "vocab_index": 0,
    "vocab_done": False,
    "quiz_submitted": False,
    "quiz_score": None,
}


def init_session():
    """Initialize all session state keys with defaults if not already set."""
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def is_logged_in() -> bool:
    return st.session_state.get("access_token") is not None


def has_child() -> bool:
    return st.session_state.get("child_created", False)


def require_auth():
    """Stop page execution if user is not logged in."""
    if not is_logged_in():
        st.warning("Please log in first.")
        st.stop()


def require_child():
    """Stop page execution if no child profile exists."""
    require_auth()
    if not has_child():
        st.warning("Please create a child profile first.")
        st.stop()
