"""
LLM factory module.
Creates ChatOpenAI instances pointing at OpenRouter.
"""

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


def get_llm(
    temperature: float = 0.7,
    model: str | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
    max_tokens: int | None = None,
    top_k: int | None = None,
) -> ChatOpenAI:
    """Creates a ChatOpenAI instance pointing at OpenRouter."""
    kwargs = {}
    if top_p is not None:
        kwargs["top_p"] = top_p
    if frequency_penalty is not None:
        kwargs["frequency_penalty"] = frequency_penalty
    if presence_penalty is not None:
        kwargs["presence_penalty"] = presence_penalty
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    # top_k is not a native OpenAI param; pass via extra_body for OpenRouter
    extra_body = {}
    if top_k is not None:
        extra_body["top_k"] = top_k

    return ChatOpenAI(
        model=model or OPENAI_MODEL,
        temperature=temperature,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model_kwargs={**kwargs, **({"extra_body": extra_body} if extra_body else {})},
    )
