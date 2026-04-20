"""
Interview service.
Provides the interview chain (simple) and agent (with tools).
"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import OPENAI_MODEL
from core.llm import get_llm
from core.prompts import SYSTEM_PROMPT, AGENT_SYSTEM_PROMPT
from tools.search import search_dotnet_docs
from tools.docs import fetch_documentation
from tools.code_review import evaluate_code

_interview_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("history"),
])

_str_parser = StrOutputParser()

INTERVIEW_TOOLS = [search_dotnet_docs, fetch_documentation, evaluate_code]


def _extract_usage(ai_message) -> dict:
    """Extract token usage from an AIMessage's metadata."""
    # LangChain stores it in response_metadata.token_usage or usage_metadata
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
    return usage


def _history_to_messages(conversation_history: list[dict]) -> list:
    """Convert list-of-dicts history to LangChain message objects."""
    mapping = {"user": HumanMessage, "assistant": AIMessage, "system": SystemMessage}
    return [mapping[m["role"]](content=m["content"]) for m in conversation_history]


def get_interview_response(
    conversation_history: list[dict],
    temperature: float = 0.7,
    model: str = OPENAI_MODEL,
    **kwargs,
) -> tuple[str, dict]:
    """Run the interview chain (no tools). Returns (text, usage_dict)."""
    chain = _interview_prompt | get_llm(temperature=temperature, model=model, **kwargs)
    messages = _history_to_messages(conversation_history)
    ai_message = chain.invoke({"history": messages})
    usage = _extract_usage(ai_message)
    return ai_message.content, usage


def get_agent_interview_response(
    conversation_history: list[dict],
    temperature: float = 0.7,
    model: str = OPENAI_MODEL,
    **kwargs,
) -> tuple[str, list[str], dict]:
    """
    Run the interview agent with tools.
    Returns (response_text, list_of_tool_names_used, usage_dict).
    """
    llm = get_llm(temperature=temperature, model=model, **kwargs)
    agent = create_react_agent(
        model=llm,
        tools=INTERVIEW_TOOLS,
        prompt=AGENT_SYSTEM_PROMPT,
    )

    messages = _history_to_messages(conversation_history)
    result = agent.invoke({"messages": messages})

    tools_used = []
    final_response = ""
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])
        if isinstance(msg, AIMessage) and msg.content:
            final_response = msg.content
        # Aggregate token usage from all AI messages
        if isinstance(msg, AIMessage):
            usage = _extract_usage(msg)
            for key in total_usage:
                total_usage[key] += usage.get(key, 0)

    return (
        final_response or "I apologize, I encountered an issue. Please try again.",
        tools_used,
        total_usage,
    )
