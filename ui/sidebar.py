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

        temperature = st.slider(
            "🌡️ Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="Controls randomness. Lower = more focused, higher = more creative.",
        )
        st.session_state.temperature = temperature

        top_p = st.slider(
            "🎯 Top P (nucleus sampling)",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            help="Limits token selection to the top cumulative probability. Lower = more focused.",
        )
        st.session_state.top_p = top_p

        top_k = st.slider(
            "🔢 Top K",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            help="Limits token selection to the top K most likely tokens. 0 = disabled.",
        )
        st.session_state.top_k = top_k

        frequency_penalty = st.slider(
            "🔁 Frequency Penalty",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
            help="Penalizes repeated tokens based on frequency. Positive = less repetition.",
        )
        st.session_state.frequency_penalty = frequency_penalty

        presence_penalty = st.slider(
            "📌 Presence Penalty",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
            help="Penalizes tokens that have appeared at all. Positive = encourages new topics.",
        )
        st.session_state.presence_penalty = presence_penalty

        max_tokens = st.number_input(
            "📏 Max Tokens",
            min_value=0,
            max_value=16384,
            value=0,
            step=256,
            help="Maximum number of tokens to generate. 0 = no limit (model default).",
        )
        st.session_state.max_tokens = max_tokens

        st.divider()

    return page


def get_model_kwargs() -> dict:
    """Collect the current model kwargs from session_state into a dict."""
    kwargs = {}
    top_p = st.session_state.get("top_p", 1.0)
    if top_p < 1.0:
        kwargs["top_p"] = top_p

    top_k = st.session_state.get("top_k", 0)
    if top_k > 0:
        kwargs["top_k"] = top_k

    freq = st.session_state.get("frequency_penalty", 0.0)
    if freq != 0.0:
        kwargs["frequency_penalty"] = freq

    pres = st.session_state.get("presence_penalty", 0.0)
    if pres != 0.0:
        kwargs["presence_penalty"] = pres

    max_tok = st.session_state.get("max_tokens", 0)
    if max_tok > 0:
        kwargs["max_tokens"] = max_tok

    return kwargs
