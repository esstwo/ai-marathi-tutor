"""Child home screen."""

import streamlit as st
from utils.session import init_session, require_child
from utils import api_client

init_session()
require_child()

st.title("Home")

# Quick progress summary
try:
    progress = api_client.get_progress(st.session_state.child_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        streak = progress["streak_days"]
        streak_label = f"{streak} day{'s' if streak != 1 else ''}"
        st.metric("Streak", streak_label)
    with col2:
        st.metric("Total XP", progress["xp_total"])
    with col3:
        st.metric("Level", progress["current_level"])

    st.divider()

    col4, col5 = st.columns(2)
    with col4:
        st.metric("Lessons Completed", progress["lessons_completed"])
    with col5:
        st.metric("Conversations", progress["conversations_count"])

except Exception:
    pass  # Don't block the home page if progress fetch fails

st.divider()

st.page_link("pages/2_lesson.py", label="Start a Lesson", icon="📖")
st.page_link("pages/3_chat.py", label="Chat with Mitra", icon="💬")
st.page_link("pages/5_progress.py", label="View Progress", icon="📊")
