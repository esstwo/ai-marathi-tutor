"""Progress + stats screen."""

import streamlit as st
from utils.session import init_session, require_child
from utils import api_client

init_session()
require_child()

st.title("Progress")

try:
    progress = api_client.get_progress(st.session_state.child_id)
except Exception:
    st.error("Could not load progress. Please try again.")
    st.stop()

# --- Streak banner ---
streak = progress["streak_days"]
if streak >= 7:
    st.success(f"Amazing! {streak}-day streak — keep it up!")
elif streak >= 3:
    st.info(f"Nice! {streak}-day streak — you're on a roll!")
elif streak >= 1:
    st.info(f"{streak}-day streak — great start!")
else:
    st.warning("No active streak. Start a lesson or chat to begin one!")

st.divider()

# --- Key metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total XP", progress["xp_total"])
with col2:
    st.metric("Level", progress["current_level"])
with col3:
    streak_label = f"{streak} day{'s' if streak != 1 else ''}"
    st.metric("Streak", streak_label)

st.divider()

# --- Activity stats ---
col4, col5 = st.columns(2)
with col4:
    st.metric("Lessons Completed", progress["lessons_completed"])
    st.caption("10 XP per lesson")
with col5:
    st.metric("Conversations", progress["conversations_count"])
    st.caption("5 XP per minute of chat")

st.divider()

# --- Level progress ---
xp = progress["xp_total"]
level = progress["current_level"]
# Simple level thresholds
LEVEL_THRESHOLDS = {1: 0, 2: 100, 3: 300, 4: 600}
next_level = min(level + 1, 4)

if level < 4:
    current_threshold = LEVEL_THRESHOLDS[level]
    next_threshold = LEVEL_THRESHOLDS[next_level]
    xp_in_level = xp - current_threshold
    xp_needed = next_threshold - current_threshold
    pct = min(xp_in_level / xp_needed, 1.0)

    st.subheader(f"Level {level} → Level {next_level}")
    st.progress(pct)
    st.caption(f"{xp_in_level} / {xp_needed} XP to next level")
else:
    st.subheader("Level 4 — Max Level!")
    st.progress(1.0)
    st.caption("You've reached the highest level. Keep practicing!")
