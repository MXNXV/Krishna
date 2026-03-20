"""
Full RAG pipeline: retrieve → expand → generate answer with citations.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from openai import OpenAI

from config import (
    DEFAULT_ANSWER_MAX_TOKENS,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_ANSWER_TEMPERATURE,
    DEFAULT_CONTEXT_WINDOW_SIZE,
    DEFAULT_RETRIEVAL_K,
)
from expand_context import expand_context
from retrieve import retrieve

logger = logging.getLogger(__name__)

def build_rag_prompt(
    query: str, expanded_chunks: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """
    Build messages for OpenAI Chat API with retrieved context.

    Args:
        query: User's question
        expanded_chunks: List of context chunks from expand_context()

    Returns:
        OpenAI messages format: [{"role": "system", "content": ...}, ...]
    """
    # System prompt: define assistant role and citation format.
    system_prompt = """You are a helpful assistant answering questions about the Bhagavad Gita.

You will be provided with relevant verses from the Gita as context. Use ONLY this context to answer the question.

CRITICAL RULES:
1. Answer based ONLY on the provided verses - do not use external knowledge
2. ALWAYS cite verses using the format (BG Chapter.Verse) - example: (BG 2.47)
3. If the context doesn't contain enough information to answer, say so honestly
4. Keep answers clear and concise
5. When quoting directly, use quotation marks and cite the verse
6. You may reference multiple verses to build a complete answer

Format your answer naturally, weaving in citations where relevant."""

    # Build context from expanded chunks
    context_parts = []
    for chunk in expanded_chunks:
        center_id = chunk["center_verse_id"]
        context_text = chunk["combined_text"]

        # Add header showing which verse this context is from
        context_parts.append(f"=== Context for {center_id} ===")
        context_parts.append(context_text)
        context_parts.append("")  # Blank line

    context = "\n".join(context_parts)

    # User message: question + context
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
    """
    Answer a question about the Bhagavad Gita using RAG.

    Pipeline:
    1. Retrieve top-k relevant verses (semantic search)
    2. Expand each to context windows
    3. Build prompt with context
    4. Generate answer with GPT-4o-mini
    5. Return answer + citations

    Args:
        query: User's question
        k: Number of verses to retrieve (default from config)
        window_size: Verses in each context window (default from config)
        model: OpenAI model name (default gpt-4o-mini)
        temperature: LLM temperature (0-1, lower = more factual)

    Returns:
        {
            "question": str,
            "answer": str,
            "retrieved_verses": list[str],  # Center verses retrieved
            "context_chunks": list[dict],  # Full expanded contexts
            "model": str,
            "error": str | None
        }

    Notes:
        This function returns a structured error payload instead of raising to callers.
    """
    # Lazy import to avoid importing Chroma at module load time.
    from chromadb.errors import ChromaError

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if k < 1 or k > 20:
        raise ValueError(f"k must be between 1 and 20, got {k}")

    if window_size < 1:
        raise ValueError(f"window_size must be >= 1, got {window_size}")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable not set. "
            "Get your key from https://platform.openai.com/api-keys"
        )

    try:
        # Step 1: Retrieve relevant verses
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

        # Step 2: Expand context
        logger.info("Expanding context (window_size=%d)", window_size)
        expanded_chunks = expand_context(verse_ids, window_size=window_size)
        logger.info("Expanded to %d context chunks", len(expanded_chunks))

        # Step 3: Build prompt
        messages = build_rag_prompt(query, expanded_chunks)

        # Step 4: Call OpenAI
        logger.info("Calling OpenAI API (model=%s)", model)
        client = OpenAI(api_key=api_key)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=DEFAULT_ANSWER_MAX_TOKENS,
            )
        except Exception as e:
            raise RuntimeError("OpenAI API call failed") from e

        answer = response.choices[0].message.content or ""
        if not answer.strip():
            answer = (
                "I could not generate a complete answer from the retrieved context."
            )
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
        logger.error("Error in answer_question: %s", e, exc_info=True)
        return {
            "question": query,
            "answer": None,
            "retrieved_verses": [],
            "context_chunks": [],
            "model": model,
            "error": str(e),
        }
    except Exception as e:
        logger.error("Unexpected error in answer_question: %s", e, exc_info=True)
        return {
            "question": query,
            "answer": None,
            "retrieved_verses": [],
            "context_chunks": [],
            "model": model,
            "error": f"Unexpected error: {e}",
        }
