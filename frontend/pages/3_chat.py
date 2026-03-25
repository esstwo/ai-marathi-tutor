"""Mitra conversation screen."""

import streamlit as st
from utils.session import init_session, require_child
from utils import api_client

init_session()
require_child()

st.title("Chat with Mitra")

# End Chat button in sidebar
if st.session_state.conversation_id is not None:
    with st.sidebar:
        if st.button("End Chat"):
            try:
                result = api_client.end_conversation(st.session_state.conversation_id)
                xp = result.get("xp_earned", 0)
                mins = result.get("duration_minutes", 0)
                streak = result.get("streak_days", 0)
                st.session_state.conversation_id = None
                st.session_state.chat_messages = []
                st.session_state.chat_ended_msg = (
                    f"Chat ended! You earned **{xp} XP** "
                    f"for {mins} minute{'s' if mins != 1 else ''} of practice. "
                    f"Streak: {streak} day{'s' if streak != 1 else ''}!"
                )
                st.rerun()
            except Exception:
                st.error("Could not end conversation.")

# Show end-of-chat summary if we just ended
if st.session_state.get("chat_ended_msg"):
    st.success(st.session_state.chat_ended_msg)
    del st.session_state.chat_ended_msg
    if st.button("Start New Chat"):
        st.rerun()
    st.stop()

# Start a conversation on first load
if st.session_state.conversation_id is None:
    with st.spinner("Mitra is getting ready..."):
        try:
            data = api_client.start_conversation(st.session_state.child_id)
            st.session_state.conversation_id = data["conversation_id"]
            st.session_state.chat_messages = [
                {
                    "role": "mitra",
                    "marathi_text": data["marathi_text"],
                    "english_hint": data.get("english_hint"),
                }
            ]
            st.rerun()
        except Exception:
            st.error("Could not start conversation. Please try again.")
            st.stop()

# Render chat history
for msg in st.session_state.chat_messages:
    if msg["role"] == "mitra":
        with st.chat_message("assistant", avatar="🧑‍🏫"):
            st.markdown(msg["marathi_text"])
            if msg.get("english_hint"):
                st.caption(msg["english_hint"])
    else:
        with st.chat_message("user", avatar="🧒"):
            st.markdown(msg["marathi_text"])

# Chat input
if user_input := st.chat_input("Type your message..."):
    st.session_state.chat_messages.append(
        {"role": "child", "marathi_text": user_input, "english_hint": None}
    )
    with st.chat_message("user", avatar="🧒"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🧑‍🏫"):
        with st.spinner("Mitra is thinking..."):
            try:
                data = api_client.send_message(
                    st.session_state.conversation_id, user_input
                )
                st.markdown(data["marathi_text"])
                if data.get("english_hint"):
                    st.caption(data["english_hint"])
                st.session_state.chat_messages.append(
                    {
                        "role": "mitra",
                        "marathi_text": data["marathi_text"],
                        "english_hint": data.get("english_hint"),
                    }
                )
            except Exception:
                st.error("Mitra could not respond. Please try again.")
