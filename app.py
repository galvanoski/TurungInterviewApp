"""
Streamlit application entry point.
Run with:  streamlit run app.py
"""

import streamlit as st
from chat_service import get_client, get_interview_response


# ── Page configuration ────────────────────────
st.set_page_config(
    page_title="Senior .NET Interview",
    page_icon="💼",
    layout="centered",
)

st.title("Interview Prep — Senior .NET Developer")
st.caption("Practice with an AI-powered technical interviewer")

# ── Session state ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = get_client()

# ── Auto-start the interview ─────────────────
if not st.session_state.messages:
    with st.spinner("Preparing the interview..."):
        first_message = get_interview_response(
            st.session_state.client,
            st.session_state.messages,
        )
    st.session_state.messages.append({"role": "assistant", "content": first_message})

# ── Display chat history ─────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── User input ────────────────────────────────
if user_input := st.chat_input("Type your answer here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Evaluating your answer..."):
            reply = get_interview_response(
                st.session_state.client,
                st.session_state.messages,
            )
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ── Sidebar: controls ────────────────────────
with st.sidebar:
    st.header("Options")
    if st.button("🔄 Restart interview"):
        st.session_state.messages = []
        st.rerun()
