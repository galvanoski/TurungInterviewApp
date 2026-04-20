"""
Agent tool: search .NET documentation on the web.
"""

import requests
from langchain_core.tools import tool


@tool
def search_dotnet_docs(query: str) -> str:
    """Search the web for current .NET documentation, best practices, or technical details.
    Use this to verify technical concepts, check latest .NET features, or find accurate
    information for interview questions.

    Args:
        query: Technical topic to search (e.g. 'ASP.NET Core middleware pipeline .NET 8')
    """
    try:
        resp = requests.get(
            f"https://s.jina.ai/{query}",
            headers={"Accept": "text/plain", "User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.text[:3000]
    except Exception as e:
        return f"Search unavailable: {e}"
