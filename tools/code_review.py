"""
Agent tool: in-depth C#/.NET code review.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from core.llm import get_llm


@tool
def evaluate_code(code: str) -> str:
    """Perform an in-depth code review of a C#/.NET code snippet provided by the candidate.
    Use this when the candidate shares code and you want a thorough analysis covering
    correctness, quality, performance, and .NET best practices.

    Args:
        code: The code snippet to analyze
    """
    review_llm = get_llm(temperature=0.2)
    result = review_llm.invoke([
        SystemMessage(content=(
            "You are an expert C#/.NET code reviewer. Analyze the following code and provide:\n"
            "1. **Correctness**: Does the code work as intended? Any bugs?\n"
            "2. **Quality**: Follows .NET conventions? Clean code principles?\n"
            "3. **Performance**: Any performance concerns or optimization opportunities?\n"
            "4. **Improvements**: Specific, actionable suggestions.\n"
            "Be concise and specific."
        )),
        HumanMessage(content=code),
    ])
    return result.content
