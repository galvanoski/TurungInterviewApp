"""
Agent tool: fetch content from a documentation URL.
"""

from langchain_core.tools import tool
from data.scraper import fetch_via_jina


@tool
def fetch_documentation(url: str) -> str:
    """Fetch and read content from a specific documentation URL.
    Use this when you want to reference a specific page from Microsoft docs
    or other .NET technical resources.

    Args:
        url: The full URL to fetch (e.g. 'https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware')
    """
    text = fetch_via_jina(url)
    return text[:3000] if text else "Could not fetch the URL content."
