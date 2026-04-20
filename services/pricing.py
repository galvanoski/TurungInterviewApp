"""
Pricing service.
Fetches model pricing from OpenRouter API and calculates prompt costs.
"""

import requests
import streamlit as st

from config import OPENAI_API_KEY


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_all_model_pricing() -> dict:
    """Fetch pricing for all models from OpenRouter. Cached for 1 hour."""
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return {}

    pricing = {}
    for model in data.get("data", []):
        model_id = model.get("id", "")
        p = model.get("pricing", {})
        prompt_cost = float(p.get("prompt", 0))
        completion_cost = float(p.get("completion", 0))
        pricing[model_id] = {
            "prompt": prompt_cost,
            "completion": completion_cost,
        }
    return pricing


def get_model_pricing(model_id: str) -> dict:
    """Return per-token pricing for a specific model."""
    all_pricing = _fetch_all_model_pricing()
    return all_pricing.get(model_id, {"prompt": 0, "completion": 0})


def calculate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the cost in USD for a given number of tokens."""
    pricing = get_model_pricing(model_id)
    return (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])


def format_cost_caption(model_id: str, usage: dict) -> str:
    """Format a human-readable cost caption string."""
    if not usage:
        return ""
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
    cost = calculate_cost(model_id, prompt_tokens, completion_tokens)

    return (
        f"💰 Tokens: {prompt_tokens:,} in / {completion_tokens:,} out "
        f"({total_tokens:,} total) · Cost: ${cost:.6f}"
    )
