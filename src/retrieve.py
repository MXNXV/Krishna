from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import chromadb
from chromadb.errors import NotFoundError

from src.config import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_DIR,
    DEFAULT_MODEL_NAME,
    DEFAULT_RETRIEVAL_K,
)

logger = logging.getLogger(__name__)

_model: Any = None
_collection: Any = None


def _get_embedding_model() -> Any:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(DEFAULT_MODEL_NAME)
    return _model


def _get_collection(chroma_path: Path | str | None = None) -> Any:
    global _collection
    if _collection is not None and chroma_path is None:
        return _collection

    db_dir = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_DIR
    if not db_dir.is_dir():
        raise FileNotFoundError(
            f"Chroma directory not found: {db_dir}. Run build_index.py first."
        )

    client = chromadb.PersistentClient(path=str(db_dir))
    
    try:
        coll = client.get_collection(COLLECTION_NAME)
    except NotFoundError:
        raise FileNotFoundError(
            f"Collection {COLLECTION_NAME!r} not found. Run build_index.py first."
        )

    if chroma_path is None:
        _collection = coll
    return coll


def retrieve(
    query: str,
    k: int = DEFAULT_RETRIEVAL_K,
    filters: dict[str, Any] | None = None,
    *,
    chroma_path: Path | str | None = None,
) -> dict[str, Any]:
    """Retrieve top-k most similar verses for a query."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")

    model = _get_embedding_model()
    collection = _get_collection(chroma_path)

    query_embedding = model.encode([query.strip()], convert_to_numpy=True)
    vec = query_embedding[0].tolist()

    results = collection.query(
        query_embeddings=[vec],
        n_results=k,
        where=filters,
    )

    return results


def reset_client_cache() -> None:
    global _model, _collection
    _model = None
    _collection = None


def _print_sample_results(results: dict[str, Any], label: str) -> None:
    print(label)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]
    
    if not docs:
        print("  (no documents returned)\n")
        return

    for i, (doc, meta, chunk_id) in enumerate(zip(docs, metas, ids)):
        speaker = meta.get("speaker", "?")
        ch = meta.get("chapter", "?")
        v = meta.get("verse", "?")
        preview = (doc or "")[:100] + ("..." if len(doc or "") > 100 else "")
        print(f"{i + 1}. id={chunk_id!r} | {ch}.{v} ({speaker})")
        print(f"   {preview}\n")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    print("Query: What is yoga?\n")
    results = retrieve("What is yoga according to the Gita?", k=5)
    _print_sample_results(results, "")

    print("\nQuery: What does Arjuna ask? (Speaker filter: Arjuna)\n")
    results = retrieve(
        "What does Arjuna ask Krishna?",
        k=5,
        filters={"speaker": "Arjuna"},
    )
    _print_sample_results(results, "")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
