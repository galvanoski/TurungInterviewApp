"""
Validation service.
Validates job descriptions for legitimacy and .NET relevance.
"""

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import get_llm
from core.prompts import VALIDATION_PROMPT

_validation_chain = (
    ChatPromptTemplate.from_messages([
        ("system", VALIDATION_PROMPT),
        ("human", "{text}"),
    ])
    | get_llm(temperature=0.0)
    | StrOutputParser()
)


def validate_job_description(text: str) -> dict:
    """
    Validates whether the input text is a legitimate .NET-related job description.
    Returns dict: {valid, dotnet_related, reason}
    """
    raw = _validation_chain.invoke({"text": text})
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"valid": False, "dotnet_related": False, "reason": "Could not parse validation response."}
