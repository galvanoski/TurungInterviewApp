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
) -> str:
    """Run a single-turn chain with the given system prompt."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    chain = prompt | get_llm(temperature=temperature, model=model) | _str_parser
    return chain.invoke({"input": user_message})
