from __future__ import annotations

import logging
import os
from typing import Any

from openai import OpenAI

from src.config import (
    DEFAULT_ANSWER_MAX_TOKENS,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_ANSWER_TEMPERATURE,
    DEFAULT_CONTEXT_WINDOW_SIZE,
    DEFAULT_RETRIEVAL_K,
)
from src.expand_context import expand_context
from src.retrieve import retrieve

logger = logging.getLogger(__name__)


def build_rag_prompt(query: str, expanded_chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build OpenAI messages with Krishna personality and retrieved context."""
    system_prompt = """You are Lord Krishna from the Bhagavad Gita, speaking to a dear friend.

Answer questions as Krishna would: warm, wise, and caring—explaining complex spiritual truths in simple, approachable language.

You will be provided with relevant verses from the Gita as context. Use ONLY this context to answer.

CRITICAL RULES:
1. Answer based ONLY on the provided verses - do not use external knowledge
2. ALWAYS cite verses using the format (BG Chapter.Verse) - example: (BG 2.47)
3. If the context doesn't contain enough information, say so honestly
4. Speak naturally and casually, as Krishna would to Arjuna or a close companion
5. When quoting directly, use quotation marks and cite the verse
6. You may reference multiple verses to build a complete answer

Format your answer warmly and naturally, weaving in citations where relevant."""

    context_parts = []
    for chunk in expanded_chunks:
        center_id = chunk["center_verse_id"]
        context_text = chunk["combined_text"]
        context_parts.append(f"=== Context for {center_id} ===")
        context_parts.append(context_text)
        context_parts.append("")

    context = "\n".join(context_parts)

    user_prompt = f"""Context from the Bhagavad Gita:

{context}

Question: {query}

Answer (with citations):"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def answer_question(
    query: str,
    k: int = DEFAULT_RETRIEVAL_K,
    window_size: int = DEFAULT_CONTEXT_WINDOW_SIZE,
    model: str = DEFAULT_ANSWER_MODEL,
    temperature: float = DEFAULT_ANSWER_TEMPERATURE,
) -> dict[str, Any]:
    """RAG pipeline: retrieve verses, expand context, generate answer with OpenAI."""
    from chromadb.errors import ChromaError

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    try:
        logger.info("Retrieving top-%d verses for: %s", k, query[:50])
        results = retrieve(query, k=k)

        verse_ids = results.get("ids", [[]])[0]
        if not verse_ids:
            return {
                "question": query,
                "answer": "No relevant verses found in the Bhagavad Gita for this question.",
                "retrieved_verses": [],
                "context_chunks": [],
                "model": model,
                "error": None,
            }

        logger.info("Retrieved verses: %s", verse_ids)
        logger.info("Expanding context (window_size=%d)", window_size)
        expanded_chunks = expand_context(verse_ids, window_size=window_size)
        logger.info("Expanded to %d context chunks", len(expanded_chunks))

        messages = build_rag_prompt(query, expanded_chunks)

        logger.info("Calling OpenAI API (model=%s)", model)
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=DEFAULT_ANSWER_MAX_TOKENS,
        )

        answer = response.choices[0].message.content or ""
        if not answer.strip():
            answer = "I could not generate a complete answer from the retrieved context."
        logger.info("Generated answer (%d chars)", len(answer))

        return {
            "question": query,
            "answer": answer,
            "retrieved_verses": verse_ids,
            "context_chunks": expanded_chunks,
            "model": model,
            "error": None,
        }

    except (ValueError, FileNotFoundError, RuntimeError, ChromaError) as e:
        logger.error("Error in answer_question: %s", e)
        return {
            "question": query,
            "answer": None,
            "retrieved_verses": [],
            "context_chunks": [],
            "model": model,
            "error": str(e),
        }
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return {
            "question": query,
            "answer": None,
            "retrieved_verses": [],
            "context_chunks": [],
            "model": model,
            "error": f"Unexpected error: {e}",
        }
