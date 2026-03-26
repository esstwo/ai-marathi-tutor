"""Parent progress dashboard — aggregated view across all children."""

import streamlit as st
from utils.session import init_session, require_auth
from utils import api_client

init_session()
require_auth()

st.title("Parent Dashboard")

try:
    progress = api_client.get_parent_progress(st.session_state.user_id)
except Exception:
    st.error("Could not load progress. Please try again.")
    st.stop()

# --- Key metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Lessons Completed",
        f"{progress['lessons_completed']} / {progress['total_lessons']}",
    )
with col2:
    st.metric("Total XP", progress["xp_total"])
with col3:
    streak = progress["streak_days"]
    st.metric("Streak", f"{streak} day{'s' if streak != 1 else ''}")

st.divider()

col4, col5 = st.columns(2)
with col4:
    st.metric("Conversations", progress["conversations_count"])
with col5:
    ratio_pct = round(progress["avg_marathi_ratio"] * 100)
    st.metric("Avg Marathi Usage", f"{ratio_pct}%")
