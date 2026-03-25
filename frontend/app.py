"""Main entry — routing, session state."""

import streamlit as st
from utils.session import init_session, is_logged_in, has_child
from utils import api_client

st.set_page_config(page_title="MarathiMitra", page_icon="📚", layout="centered")
init_session()

AVATARS = ["🐘", "🦁", "🦜", "🐢", "🦋", "🐒"]

# --- Logged-in users: show sidebar navigation ---
if is_logged_in() and has_child():
    st.title("MarathiMitra")
    st.success("Welcome back! Use the sidebar to navigate.")
    st.page_link("pages/1_home.py", label="Home", icon="🏠")
    st.page_link("pages/2_lesson.py", label="Lessons", icon="📖")
    st.page_link("pages/3_chat.py", label="Chat with Mitra", icon="💬")
    st.page_link("pages/5_progress.py", label="Progress", icon="📊")
    st.stop()

# --- Auth: Signup / Login ---
if not is_logged_in():
    st.title("MarathiMitra")
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
                try:
                    data = api_client.signup(name, email, password)
                    st.session_state.user_id = data["user_id"]
                    st.session_state.access_token = data.get("access_token")
                    st.success("Account created!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Log In")

        if login_submitted:
            if not login_email or not login_password:
                st.error("Please fill in all fields.")
            else:
                try:
                    data = api_client.login(login_email, login_password)
                    st.session_state.user_id = data["user_id"]
                    st.session_state.access_token = data["access_token"]
                    if data.get("children"):
                        st.session_state.child_id = data["children"][0]["id"]
                        st.session_state.child_created = True
                    st.success("Logged in!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.stop()

# --- Child Setup (logged in but no child yet) ---
st.title("MarathiMitra")
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
        try:
            data = api_client.create_child(
                child_name, age, selected_avatar, st.session_state.access_token
            )
            st.session_state.child_id = data["child"]["id"]
            st.session_state.child_created = True
            st.success("Profile created!")
            st.rerun()
        except Exception as e:
            st.error(str(e))
