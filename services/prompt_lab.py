"""
Prompt Lab service.
Runs a single-turn chain with a custom system prompt for technique comparison.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import OPENAI_MODEL
from core.llm import get_llm

_str_parser = StrOutputParser()


def get_response_with_prompt(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    model: str = OPENAI_MODEL,
    **kwargs,
) -> tuple[str, dict]:
    """Run a single-turn chain with the given system prompt. Returns (text, usage_dict)."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    chain = prompt | get_llm(temperature=temperature, model=model, **kwargs)
    ai_message = chain.invoke({"input": user_message})

    # Extract token usage
    usage = {}
    rm = getattr(ai_message, "response_metadata", {})
    tu = rm.get("token_usage") or rm.get("usage", {})
    if tu:
        usage = {
            "prompt_tokens": tu.get("prompt_tokens", 0),
            "completion_tokens": tu.get("completion_tokens", 0),
            "total_tokens": tu.get("total_tokens", 0),
        }
    elif hasattr(ai_message, "usage_metadata") and ai_message.usage_metadata:
        um = ai_message.usage_metadata
        usage = {
            "prompt_tokens": getattr(um, "input_tokens", 0),
            "completion_tokens": getattr(um, "output_tokens", 0),
            "total_tokens": getattr(um, "total_tokens", 0),
        }

    return ai_message.content, usage
