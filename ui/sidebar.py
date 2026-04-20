"""
Shared sidebar component.
Renders navigation, model settings, and returns the selected page.
"""

import streamlit as st
from core.prompts import AVAILABLE_MODELS


def render_sidebar() -> str:
    """Render the sidebar and return the selected page name."""
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("", ["🎙️ Interview", "🔬 Prompt Lab"], label_visibility="collapsed")
        st.divider()
        st.header("Model Settings")

        selected_model = st.selectbox(
            "🤖 Model",
            options=list(AVAILABLE_MODELS.keys()),
            index=0,
            format_func=lambda x: AVAILABLE_MODELS[x],
            help="Choose the AI model. Mini is the best balance of quality and cost.",
        )
        st.session_state.model = selected_model

        temperature = st.selectbox(
            "🌡️ Temperature",
            options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            index=5,
            format_func=lambda x: f"{x:.1f}" + (" (precise)" if x == 0.0 else " (creative)" if x == 1.0 else " (balanced)" if x == 0.5 else ""),
            help="Lower = more focused and deterministic. Higher = more creative and varied.",
        )
        st.session_state.temperature = temperature
        st.divider()

    return page
