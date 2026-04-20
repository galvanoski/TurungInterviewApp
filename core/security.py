"""
Security module.
Two-layer prompt injection detection: regex pre-filter + LLM classification.
"""

import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import get_llm
from core.prompts import INJECTION_DETECTION_PROMPT

# Fast regex pre-filter: catches common injection patterns before calling the model
_INJECTION_PATTERNS = re.compile(
    r"(?i)"
    r"(ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules))"
    r"|(you\s+are\s+now\s+(?:a|an|the)\s+)"
    r"|(disregard\s+(all\s+)?(your|the|prior|previous)\s+)"
    r"|(pretend\s+you\s+are\b)"
    r"|(act\s+as\s+(?:if|though)\s+you)"
    r"|(system\s*:\s*)"
    r"|(new\s+instructions?\s*:)"
    r"|(override\s+(your|system|all)\s+)"
    r"|(forget\s+(everything|all|your)\s+)"
    r"|(do\s+not\s+follow\s+(your|the|any)\s+(original|previous|system))"
    r"|(jailbreak|DAN\s*mode|developer\s*mode)"
    r"|(\[SYSTEM\]|\[INST\]|\<\|im_start\|)"
)

_injection_chain = (
    ChatPromptTemplate.from_messages([
        ("system", INJECTION_DETECTION_PROMPT),
        ("human", "{text}"),
    ])
    | get_llm(temperature=0.0)
    | StrOutputParser()
)


def check_prompt_injection(text: str) -> dict:
    """
    Two-layer prompt injection detection.
    Returns dict: {"injection_detected": bool, "reason": str}
    """
    match = _INJECTION_PATTERNS.search(text)
    if match:
        return {
            "injection_detected": True,
            "reason": f"Suspicious pattern detected: '{match.group().strip()}'",
        }

    raw = _injection_chain.invoke({"text": text})
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"injection_detected": False, "reason": "Could not parse detection response."}
