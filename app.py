"""
Streamlit UI entry point for Bhagavad Gita RAG.

Production-quality interface with history and polish.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

import streamlit as st

from answer import answer_question
from config import (
    DEFAULT_ANSWER_MODEL,
    DEFAULT_ANSWER_TEMPERATURE,
    DEFAULT_CONTEXT_WINDOW_SIZE,
    DEFAULT_RETRIEVAL_K,
)

logger = logging.getLogger(__name__)

# Example queries for quick testing
EXAMPLE_QUERIES = [
    "What is yoga according to the Gita?",
    "What does Krishna teach about duty?",
    "How should I deal with success and failure?",
    "What does the Gita say about the mind?",
    "Why did Arjuna refuse to fight?",
    "What is the difference between karma yoga and bhakti yoga?",
]


def _render_header() -> None:
    """Render page header with custom styling."""
    st.set_page_config(
        page_title="Bhagavad Gita AI Assistant",
        page_icon="🕉️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        /* Main container */
        .main {
            padding-top: 2rem;
        }
        
        /* Header styling */
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
            text-align: center;
        }
        
        .subtitle {
            color: #64748b;
            font-size: 1.05rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Answer box with animation */
        .answer-box {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            line-height: 1.7;
            font-size: 1.05rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Verse pills */
        .verse-pills {
            margin: 1rem 0;
            animation: slideIn 0.4s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .pill {
            display: inline-block;
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            padding: 0.35rem 0.9rem;
            margin: 0.25rem;
            font-size: 0.9rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }
        
        .pill:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 3rem;
            padding: 1.5rem;
            border-top: 1px solid #e2e8f0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">Bhagavad Gita RAG Assistant</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Ask questions grounded in retrieved verses with citations</div>',
        unsafe_allow_html=True,
    )


def _render_sidebar() -> tuple[int, int, float, str]:
    """Render sidebar with settings, history, and info."""
    with st.sidebar:
        st.markdown("### Settings")

        k = st.slider(
            "Retrieved verses",
            min_value=1,
            max_value=10,
            value=DEFAULT_RETRIEVAL_K,
            help="Number of verses to retrieve from semantic search",
        )

        window_size = st.slider(
            "Context window size",
            min_value=1,
            max_value=8,
            value=DEFAULT_CONTEXT_WINDOW_SIZE,
            help="Number of verses in each context window",
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=DEFAULT_ANSWER_TEMPERATURE,
            step=0.1,
            help="Lower = more factual, Higher = more creative",
        )

        with st.expander("Advanced"):
            model = st.text_input(
                "Model", value=DEFAULT_ANSWER_MODEL, help="OpenAI model name"
            )

        st.markdown("---")

        # Query history
        st.markdown("### Recent Queries")
        if "history" not in st.session_state:
            st.session_state.history = []

        if st.session_state.history:
            for i, item in enumerate(reversed(st.session_state.history[-5:])):
                query_preview = (
                    item["query"][:40] + "..."
                    if len(item["query"]) > 40
                    else item["query"]
                )
                if st.button(
                    query_preview, key=f"history_{i}", use_container_width=True
                ):
                    st.session_state.query_input = item["query"]
                    st.rerun()
        else:
            st.caption("No queries yet")

        if st.session_state.history:
            if st.button("Clear History", use_container_width=True):
                st.session_state.history = []
                st.rerun()

        st.markdown("---")

        # System info
        st.markdown("### System Info")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Verses", "701")
            st.metric("Chapters", "18")
        with col2:
            st.metric("Embedding", "384D")
            st.metric("Model", "MiniLM")

        st.markdown("---")

        # About
        st.markdown("### About")
        st.markdown(
            """
        **RAG Pipeline:**
        - Retrieval: Semantic search
        - Context: Dynamic expansion
        - Generation: GPT-4o-mini
        - Citations: Verse-level
        """
        )

        st.markdown("---")
        st.caption("Built with Streamlit • ChromaDB • OpenAI")

    return (
        k,
        window_size,
        temperature,
        model if "model" in locals() else DEFAULT_ANSWER_MODEL,
    )


def _render_examples() -> None:
    """Render example queries."""
    st.markdown("### Example Questions")

    # Show first 3 as buttons
    cols = st.columns(3)
    for i, (col, example) in enumerate(zip(cols, EXAMPLE_QUERIES[:3])):
        with col:
            if st.button(
                example[:25] + "..." if len(example) > 25 else example,
                key=f"example_{i}",
                use_container_width=True,
            ):
                st.session_state.query_input = example
                st.rerun()

    # More examples in expander
    with st.expander("More examples"):
        for i, example in enumerate(EXAMPLE_QUERIES[3:], start=3):
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state.query_input = example
                st.rerun()


def _render_result(result: dict[str, Any], query_time: float, query: str) -> None:
    """Render answer with enhanced styling."""
    err = result.get("error")
    if err:
        st.error(f"Could not generate answer: {err}")
        st.info("Check that ChromaDB index is built and OPENAI_API_KEY is set.")
        return

    answer = str(result.get("answer") or "")
    verses = result.get("retrieved_verses", [])

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Response Time", f"{query_time:.2f}s")
    with col2:
        st.metric("Verses Retrieved", len(verses))
    with col3:
        st.metric("Context Chunks", len(result.get("context_chunks", [])))
    with col4:
        st.metric("Answer Length", f"{len(answer)} chars")

    st.markdown("---")

    # Answer section
    st.markdown("### Answer")
    st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

    # Copy button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Copy Answer", use_container_width=True):
            st.session_state.show_copy = True

    # Show copyable text if button was clicked
    if st.session_state.get("show_copy", False):
        with st.expander("Click to select and copy", expanded=True):
            st.code(answer, language=None)
            st.session_state.show_copy = False

    # Retrieved verses
    st.markdown("### Retrieved Verses")
    if verses:
        verse_html = (
            '<div class="verse-pills">'
            + "".join([f'<span class="pill">{v}</span>' for v in verses])
            + "</div>"
        )
        st.markdown(verse_html, unsafe_allow_html=True)
    else:
        st.caption("No verses retrieved.")

    # Context details
    with st.expander("View Expanded Context"):
        chunks = result.get("context_chunks", [])
        if not chunks:
            st.caption("No expanded context chunks.")
        else:
            for i, chunk in enumerate(chunks, 1):
                meta = chunk.get("metadata", {})
                st.markdown(f"**Chunk {i}**: `{chunk.get('center_verse_id')}`")

                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.caption(f"Chapter: {meta.get('chapter')}")
                with mcol2:
                    st.caption(f"Window: {meta.get('window_size')} verses")
                with mcol3:
                    st.caption(f"Resolved: {meta.get('resolved_context_count')}")

                context_text = str(chunk.get("combined_text") or "")
                st.text_area(
                    f"Context {i}",
                    value=context_text,
                    height=150,
                    key=f"context_{i}",
                    label_visibility="collapsed",
                )

                if i < len(chunks):
                    st.markdown("---")

    # Add to history
    if "history" not in st.session_state:
        st.session_state.history = []

    # Avoid duplicates
    if not any(h["query"] == query for h in st.session_state.history):
        st.session_state.history.append(
            {
                "query": query,
                "answer": answer[:100] + "..." if len(answer) > 100 else answer,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "verses": verses,
            }
        )


def main() -> None:
    """Main Streamlit app entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Render header first
    _render_header()

    # Render sidebar
    k, window_size, temperature, model = _render_sidebar()

    # Example queries
    _render_examples()

    # Keep query text in a dedicated session key so it survives reruns.
    if "query_input" not in st.session_state:
        st.session_state.query_input = str(st.session_state.get("selected_query", ""))

    # Backward-compat: migrate one-shot selected_query into query_input if present.
    selected = st.session_state.get("selected_query", "")
    if selected:
        st.session_state.query_input = str(selected)

    # Main query input
    st.markdown("### Your Question")
    query = st.text_area(
        "Enter your question",
        height=100,
        placeholder="e.g., What does Krishna teach about detachment from results?",
        label_visibility="collapsed",
        key="query_input",
    )

    # Clear the selected query after displaying it
    if "selected_query" in st.session_state:
        del st.session_state.selected_query

    # Submit button
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit = st.button(
            "Get Answer",
            type="primary",
            use_container_width=True
        )
    
    # Only show info/return if submit is NOT clicked AND query is empty
    if not submit:
        if query.strip():
            # Query exists but submit not clicked - just show the interface
            return
        else:
            # No query and no submit - show helpful message
            st.info("Enter a question above or click an example to get started")
            return
    
    # If we get here, submit WAS clicked
    if not query.strip():
        st.warning("Please enter a question")
        return

    # Process query
    start_time = time.time()

    with st.spinner("Searching verses and generating answer..."):
        try:
            result = answer_question(
                query=query.strip(),
                k=k,
                window_size=window_size,
                model=model.strip() or DEFAULT_ANSWER_MODEL,
                temperature=temperature,
            )
        except Exception as e:
            logger.error("Unhandled app error: %s", e, exc_info=True)
            st.error(f"Unexpected error: {e}")
            st.info("Please check your configuration and try again")
            return

    query_time = time.time() - start_time

    # Render results
    _render_result(result, query_time, query.strip())

    # Footer
    st.markdown(
        """
    <div class="footer">
        <p>Bhagavad Gita RAG System</p>
        <p style="font-size: 0.85rem; margin-top: 0.5rem;">
            sentence-transformers • ChromaDB • OpenAI GPT-4o-mini
        </p>
        <p style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">
            701 verses • 18 chapters
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
