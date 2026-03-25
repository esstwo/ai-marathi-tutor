import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="MarathiMitra", page_icon="📚", layout="centered")
st.title("MarathiMitra")

if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "child_created" not in st.session_state:
    st.session_state.child_created = False
if "child_id" not in st.session_state:
    st.session_state.child_id = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

AVATARS = ["🐘", "🦁", "🦜", "🐢", "🦋", "🐒"]

# --- Step 1: Signup or Login ---
if st.session_state.access_token is None:
    signup_tab, login_tab = st.tabs(["Sign Up", "Log In"])

    with signup_tab:
        with st.form("signup_form"):
            name = st.text_input("Your name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign Up")

        if submitted:
            if not name or not email or not password:
                st.error("Please fill in all fields.")
            else:
                res = requests.post(
                    f"{API_BASE_URL}/auth/signup",
                    json={"name": name, "email": email, "password": password},
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.user_id = data["user_id"]
                    st.session_state.access_token = data.get("access_token")
                    st.success("Account created!")
                    st.rerun()
                else:
                    try:
                        detail = res.json().get("detail", "Signup failed")
                    except Exception:
                        detail = res.text or f"Signup failed (status {res.status_code})"
                    st.error(detail)

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Log In")

        if login_submitted:
            if not login_email or not login_password:
                st.error("Please fill in all fields.")
            else:
                res = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    json={"email": login_email, "password": login_password},
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.user_id = data["user_id"]
                    st.session_state.access_token = data["access_token"]
                    # If they already have a child, skip to chat
                    if data.get("children"):
                        st.session_state.child_id = data["children"][0]["id"]
                        st.session_state.child_created = True
                    st.success("Logged in!")
                    st.rerun()
                else:
                    try:
                        detail = res.json().get("detail", "Login failed")
                    except Exception:
                        detail = res.text or f"Login failed (status {res.status_code})"
                    st.error(detail)

# --- Step 2: Child Setup ---
elif not st.session_state.child_created:
    st.subheader("Add your child's profile")

    with st.form("child_form"):
        child_name = st.text_input("Child's name")
        age = st.selectbox("Age", list(range(5, 13)))

        st.write("Pick an avatar:")
        cols = st.columns(len(AVATARS))
        selected_avatar = AVATARS[0]
        for i, avatar in enumerate(AVATARS):
            with cols[i]:
                if st.form_submit_button(avatar):
                    selected_avatar = avatar

        submitted = st.form_submit_button("Create Profile")

    if submitted:
        if not child_name:
            st.error("Please enter your child's name.")
        else:
            headers = {}
            if st.session_state.access_token:
                headers["Authorization"] = f"Bearer {st.session_state.access_token}"

            res = requests.post(
                f"{API_BASE_URL}/children",
                json={"name": child_name, "age": age, "avatar": selected_avatar},
                headers=headers,
            )
            if res.status_code == 200:
                st.session_state.child_id = res.json()["child"]["id"]
                st.session_state.child_created = True
                st.success("Profile created!")
                st.rerun()
            else:
                try:
                    detail = res.json().get("detail", "Failed to create child profile")
                except Exception:
                    detail = res.text or f"Failed to create child profile (status {res.status_code})"
                st.error(detail)

# --- Step 3: Chat with Mitra ---
else:
    st.subheader("Chat with Mitra")

    # Start a conversation on first load
    if st.session_state.conversation_id is None:
        with st.spinner("Mitra is getting ready..."):
            res = requests.post(
                f"{API_BASE_URL}/conversations/start",
                json={"child_id": st.session_state.child_id},
            )
            if res.status_code == 200:
                data = res.json()
                st.session_state.conversation_id = data["conversation_id"]
                st.session_state.chat_messages = [
                    {
                        "role": "mitra",
                        "marathi_text": data["marathi_text"],
                        "english_hint": data.get("english_hint"),
                    }
                ]
                st.rerun()
            else:
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
        # Show child message immediately
        st.session_state.chat_messages.append(
            {"role": "child", "marathi_text": user_input, "english_hint": None}
        )
        with st.chat_message("user", avatar="🧒"):
            st.markdown(user_input)

        # Call Mitra
        with st.chat_message("assistant", avatar="🧑‍🏫"):
            with st.spinner("Mitra is thinking..."):
                res = requests.post(
                    f"{API_BASE_URL}/conversations/{st.session_state.conversation_id}/message",
                    json={"message": user_input},
                )

            if res.status_code == 200:
                data = res.json()
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
            else:
                st.error("Mitra could not respond. Please try again.")
