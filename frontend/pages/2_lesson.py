"""Lesson screen — vocabulary flashcards + quiz."""

import streamlit as st
from utils.session import init_session, require_child
from utils import api_client

init_session()
require_child()

st.title("Lessons")

# --- Lesson picker ---
if st.session_state.lesson_data is None:
    st.subheader("Pick a lesson")
    try:
        lesson_list = api_client.list_lessons(level=1)
    except Exception:
        lesson_list = []

    if lesson_list:
        for lesson in lesson_list:
            if st.button(lesson["title"], key=f"lesson_{lesson['id']}"):
                st.session_state.lesson_data = lesson
                st.session_state.vocab_index = 0
                st.session_state.vocab_done = False
                st.session_state.quiz_submitted = False
                st.session_state.quiz_score = None
                st.rerun()
    else:
        st.info("No lessons available yet. Ask your teacher to add some!")

# --- Vocabulary flashcards ---
elif not st.session_state.vocab_done:
    lesson = st.session_state.lesson_data
    vocab = lesson["vocabulary"]
    idx = st.session_state.vocab_index
    total = len(vocab)

    st.subheader(lesson["title"])
    st.caption(lesson["theme"])
    st.progress((idx + 1) / total)
    st.markdown(f"**Word {idx + 1} of {total}**")

    word = vocab[idx]
    st.markdown(f"## {word['marathi']}")
    st.markdown(f"**{word['english']}**")
    st.caption(f"Pronunciation: {word['pronunciation']}")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Previous", disabled=(idx == 0)):
            st.session_state.vocab_index -= 1
            st.rerun()
    with col3:
        if idx < total - 1:
            if st.button("Next"):
                st.session_state.vocab_index += 1
                st.rerun()
        else:
            if st.button("Start Quiz"):
                st.session_state.vocab_done = True
                st.rerun()

# --- Quiz ---
elif not st.session_state.quiz_submitted:
    lesson = st.session_state.lesson_data
    quiz = lesson["quiz_questions"]

    st.subheader(f"Quiz: {lesson['title']}")

    with st.form("quiz_form"):
        answers = []
        for i, q in enumerate(quiz):
            choice = st.radio(
                f"**Q{i + 1}.** {q['question']}",
                options=q["options"],
                index=None,
                key=f"quiz_q_{i}",
            )
            answers.append(choice)

        submitted = st.form_submit_button("Submit Quiz")

    if submitted:
        if None in answers:
            st.warning("Please answer all questions before submitting.")
        else:
            score = sum(
                1
                for i, q in enumerate(quiz)
                if answers[i] == q["options"][q["correct_index"]]
            )

            try:
                api_client.complete_lesson(
                    lesson["id"], st.session_state.child_id, score
                )
            except Exception:
                pass  # don't block the UI if progress tracking fails

            st.session_state.quiz_submitted = True
            st.session_state.quiz_score = score
            st.rerun()

# --- Results ---
else:
    lesson = st.session_state.lesson_data
    quiz = lesson["quiz_questions"]
    score = st.session_state.quiz_score
    total = len(quiz)

    st.subheader(f"Results: {lesson['title']}")

    if score == total:
        st.success(f"Perfect! {score}/{total}")
    elif score >= total // 2:
        st.info(f"Good job! {score}/{total}")
    else:
        st.warning(f"{score}/{total} — Keep practicing!")

    if st.button("Back to Lessons"):
        st.session_state.lesson_data = None
        st.session_state.vocab_index = 0
        st.session_state.vocab_done = False
        st.session_state.quiz_submitted = False
        st.session_state.quiz_score = None
        st.rerun()
