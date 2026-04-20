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


def _history_to_messages(conversation_history: list[dict]) -> list:
    """Convert list-of-dicts history to LangChain message objects."""
    mapping = {"user": HumanMessage, "assistant": AIMessage, "system": SystemMessage}
    return [mapping[m["role"]](content=m["content"]) for m in conversation_history]


def get_interview_response(
    conversation_history: list[dict],
    temperature: float = 0.7,
    model: str = OPENAI_MODEL,
) -> str:
    """Run the interview chain (no tools)."""
    chain = _interview_prompt | get_llm(temperature=temperature, model=model) | _str_parser
    messages = _history_to_messages(conversation_history)
    return chain.invoke({"history": messages})


def get_agent_interview_response(
    conversation_history: list[dict],
    temperature: float = 0.7,
    model: str = OPENAI_MODEL,
) -> tuple[str, list[str]]:
    """
    Run the interview agent with tools.
    Returns (response_text, list_of_tool_names_used).
    """
    llm = get_llm(temperature=temperature, model=model)
    agent = create_react_agent(
        model=llm,
        tools=INTERVIEW_TOOLS,
        prompt=AGENT_SYSTEM_PROMPT,
    )

    messages = _history_to_messages(conversation_history)
    result = agent.invoke({"messages": messages})

    tools_used = []
    final_response = ""
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])
        if isinstance(msg, AIMessage) and msg.content:
            final_response = msg.content

    return final_response or "I apologize, I encountered an issue. Please try again.", tools_used
