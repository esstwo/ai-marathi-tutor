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

AVATARS = ["🐘", "🦁", "🦜", "🐢", "🦋", "🐒"]

# --- Step 1: Signup ---
if st.session_state.access_token is None:
    st.subheader("Create your account")

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
                st.session_state.child_created = True
                st.success("Profile created!")
                st.rerun()
            else:
                try:
                    detail = res.json().get("detail", "Failed to create child profile")
                except Exception:
                    detail = res.text or f"Failed to create child profile (status {res.status_code})"
                st.error(detail)

# --- Step 3: Dashboard placeholder ---
else:
    st.success("You're all set! 🎉")
    st.info("Lessons and conversations coming soon.")
