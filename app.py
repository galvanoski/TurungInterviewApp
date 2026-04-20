"""
Streamlit application entry point.
Run with:  streamlit run app.py
"""

import streamlit as st
from ui.sidebar import render_sidebar
from ui import interview_page, prompt_lab_page

# ── Page configuration ────────────────────────
st.set_page_config(
    page_title="Senior .NET Interview",
    page_icon="💼",
    layout="wide",
)

# ── Sidebar & routing ────────────────────────
page = render_sidebar()

if page == "🎙️ Interview":
    interview_page.render()
elif page == "🔬 Prompt Lab":
    prompt_lab_page.render()
