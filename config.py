import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str | None = None) -> str | None:
    """Read from environment first, then Streamlit secrets (for Cloud deploy)."""
    value = os.getenv(key)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
OPENAI_MODEL = _get_secret("OPENAI_MODEL", "openai/gpt-5-mini")
