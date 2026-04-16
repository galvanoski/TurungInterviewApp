"""
Chat service module.
Handles communication with the OpenAI API.
"""

from pyexpat.errors import messages
from xmlrpc import client

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from prompts import SYSTEM_PROMPT


def get_client() -> OpenAI:
    """Creates and returns the OpenAI client."""
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)


# ──────────────────────────────────────────────
#  OPENAI MODEL CALL
# ──────────────────────────────────────────────
def get_interview_response(client: OpenAI, conversation_history: list[dict]) -> str:
    """
    Sends the conversation history to the model and returns the response.

    Args:
        client: OpenAI client instance.
        conversation_history: List of messages with format
            [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        Text of the model's response.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
            
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
       
    )

    return response.choices[0].message.content
