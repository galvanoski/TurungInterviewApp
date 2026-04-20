"""
LLM factory module.
Creates ChatOpenAI instances pointing at OpenRouter.
"""

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


def get_llm(temperature: float = 0.7, model: str | None = None) -> ChatOpenAI:
    """Creates a ChatOpenAI instance pointing at OpenRouter."""
    return ChatOpenAI(
        model=model or OPENAI_MODEL,
        temperature=temperature,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
    )
