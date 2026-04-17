"""
Vector store module.
Uses ChromaDB to persist interview sessions keyed by job description embeddings.
When a similar job description is submitted, the previous session can be resumed.
"""

import json
import hashlib
import chromadb
from pathlib import Path

# Persistent storage directory
_DB_DIR = Path(__file__).parent / "chroma_db"
_COLLECTION_NAME = "interview_sessions"

# Similarity threshold — lower distance = more similar (cosine distance)
SIMILARITY_THRESHOLD = 0.25


def _get_collection() -> chromadb.Collection:
    """Get or create the ChromaDB collection with persistent storage."""
    client = chromadb.PersistentClient(path=str(_DB_DIR))
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _make_id(job_desc: str) -> str:
    """Create a deterministic ID from the job description text."""
    return hashlib.sha256(job_desc.encode()).hexdigest()[:16]


def search_similar_session(job_desc: str) -> dict | None:
    """
    Search for a previously stored interview session with a similar job description.

    Args:
        job_desc: The new job description text.

    Returns:
        dict with keys {id, job_desc, messages, distance} if a similar session
        is found within the threshold, else None.
    """
    collection = _get_collection()

    if collection.count() == 0:
        return None

    results = collection.query(
        query_texts=[job_desc],
        n_results=1,
        include=["documents", "metadatas", "distances"],
    )

    if not results["ids"][0]:
        return None

    distance = results["distances"][0][0]

    if distance > SIMILARITY_THRESHOLD:
        return None

    metadata = results["metadatas"][0][0]
    messages = json.loads(metadata.get("messages", "[]"))

    return {
        "id": results["ids"][0][0],
        "job_desc": results["documents"][0][0],
        "messages": messages,
        "distance": distance,
    }


def save_session(job_desc: str, messages: list[dict]) -> str:
    """
    Save or update an interview session in the vector store.

    Args:
        job_desc: The job description text (used for embedding).
        messages: The conversation history list.

    Returns:
        The session ID.
    """
    collection = _get_collection()
    session_id = _make_id(job_desc)

    # Strip tools_used from messages before storing (not needed for resume)
    clean_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]

    collection.upsert(
        ids=[session_id],
        documents=[job_desc],
        metadatas=[{
            "messages": json.dumps(clean_messages),
            "message_count": len(clean_messages),
        }],
    )

    return session_id


def delete_session(session_id: str) -> None:
    """Delete a specific session from the vector store."""
    collection = _get_collection()
    collection.delete(ids=[session_id])


def list_sessions() -> list[dict]:
    """List all stored sessions with their metadata."""
    collection = _get_collection()

    if collection.count() == 0:
        return []

    results = collection.get(include=["documents", "metadatas"])

    sessions = []
    for i, sid in enumerate(results["ids"]):
        meta = results["metadatas"][i]
        sessions.append({
            "id": sid,
            "job_desc_preview": results["documents"][i][:150] + "...",
            "message_count": meta.get("message_count", 0),
        })

    return sessions
