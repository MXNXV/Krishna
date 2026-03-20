"""
Semantic retrieval against the local ChromaDB index built by ``build_index.py``.

Uses the same embedding model as indexing (MiniLM) so query vectors match stored
vectors. Optional ``where`` filters use Chroma metadata (e.g. ``speaker``).

Paths and names come from ``config.py`` (same source as ``build_index.py``).
"""

from __future__ import annotations

import logging
import json
import time
import sys
from pathlib import Path
from typing import Any

import chromadb  # type: ignore
from chromadb.errors import ChromaError, NotFoundError  # type: ignore

from config import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_DIR,
    DEFAULT_MODEL_NAME,
    DEFAULT_RETRIEVAL_K,
)

logger = logging.getLogger(__name__)
DEBUG_LOG_PATH = "debug-51ae4c.log"
DEBUG_SESSION_ID = "51ae4c"

# Lazy-loaded after first use (avoids loading torch/model on ``import retrieve``).
_model: Any = None
_collection: Any = None


def _debug_log(
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any],
) -> None:
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _get_embedding_model() -> Any:
    """Load SentenceTransformer once; same model id as ``generate_embeddings``."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as e:
            raise ImportError(
                "Install sentence-transformers for retrieval: pip install sentence-transformers"
            ) from e
        try:
            _model = SentenceTransformer(DEFAULT_MODEL_NAME)
        except OSError as e:
            logger.error("Could not load embedding model %r: %s", DEFAULT_MODEL_NAME, e)
            raise
        except Exception as e:
            logger.error("Unexpected error loading model %r: %s", DEFAULT_MODEL_NAME, e)
            raise RuntimeError(f"Failed to load SentenceTransformer: {DEFAULT_MODEL_NAME}") from e
    return _model


def _get_collection(chroma_path: Path | str | None = None) -> Any:
    """Open PersistentClient and return the Gita collection (cached)."""
    global _collection
    if _collection is not None and chroma_path is None:
        return _collection

    db_dir = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_DIR
    # region agent log
    _debug_log(
        run_id="initial",
        hypothesis_id="H1",
        location="retrieve.py:_get_collection:db_dir",
        message="collection_path_resolved",
        data={
            "db_dir": str(db_dir),
            "db_exists": db_dir.exists(),
            "db_is_dir": db_dir.is_dir(),
            "override_path_used": chroma_path is not None,
        },
    )
    # endregion
    if not db_dir.is_dir():
        raise FileNotFoundError(
            f"Chroma data directory not found: {db_dir.resolve()}. Run build_index.py first."
        )

    sqlite_file = db_dir / "chroma.sqlite3"
    children = sorted([p.name for p in db_dir.iterdir()]) if db_dir.exists() else []
    # region agent log
    _debug_log(
        run_id="initial",
        hypothesis_id="H2",
        location="retrieve.py:_get_collection:layout",
        message="chroma_layout_snapshot",
        data={
            "sqlite_exists": sqlite_file.exists(),
            "sqlite_size": sqlite_file.stat().st_size if sqlite_file.exists() else -1,
            "children_count": len(children),
            "children_sample": children[:12],
        },
    )
    # endregion

    try:
        client = chromadb.PersistentClient(path=str(db_dir))
    except Exception as e:
        # region agent log
        _debug_log(
            run_id="initial",
            hypothesis_id="H3",
            location="retrieve.py:_get_collection:persistent_client",
            message="persistent_client_init_failed",
            data={"error_type": type(e).__name__, "error": str(e)},
        )
        # endregion
        logger.error("Failed to open Chroma at %s: %s", db_dir, e)
        raise RuntimeError(f"Chroma PersistentClient failed: {db_dir}") from e

    try:
        coll = client.get_collection(COLLECTION_NAME)
    except NotFoundError as e:
        # region agent log
        _debug_log(
            run_id="initial",
            hypothesis_id="H4",
            location="retrieve.py:_get_collection:get_collection",
            message="collection_not_found",
            data={"collection_name": COLLECTION_NAME, "error": str(e)},
        )
        # endregion
        logger.error("Collection %r not found in %s", COLLECTION_NAME, db_dir)
        raise FileNotFoundError(
            f"No collection {COLLECTION_NAME!r} in {db_dir}. Run build_index.py first."
        ) from e
    except ChromaError as e:
        # region agent log
        _debug_log(
            run_id="initial",
            hypothesis_id="H5",
            location="retrieve.py:_get_collection:get_collection",
            message="collection_lookup_chroma_error",
            data={"collection_name": COLLECTION_NAME, "error": str(e)},
        )
        # endregion
        logger.error("get_collection failed: %s", e)
        raise

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
    """
    Return the top-``k`` most similar verses for a natural-language query.

    Chroma's ``query`` response includes keys such as ``ids``, ``documents``,
    ``metadatas``, ``distances`` (each a list of one list per query).

    Args:
        query: User question or search text (embedded with MiniLM).
        k: Number of results (``n_results`` in Chroma). Default: ``config.DEFAULT_RETRIEVAL_K``.
        filters: Optional metadata filter dict, e.g. ``{"speaker": "Arjuna"}``.
            Must use fields stored at index time (chapter, verse, speaker, ...).
        chroma_path: Override Chroma directory (disables cache for that path).

    Returns:
        Raw Chroma query result dict.

    Raises:
        ValueError: Empty query or invalid ``k``.
        FileNotFoundError: Missing DB directory or collection.
        ImportError: sentence-transformers not installed.
        RuntimeError: Model load failure.
        ChromaError: Chroma query failure.
    """
    if not query or not str(query).strip():
        raise ValueError("query must be a non-empty string.")
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")

    model = _get_embedding_model()
    collection = _get_collection(chroma_path)

    try:
        query_embedding = model.encode([str(query).strip()], convert_to_numpy=True)
    except (MemoryError, RuntimeError) as e:
        logger.error("Encoding query failed: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error encoding query: %s", e, exc_info=True)
        raise RuntimeError("model.encode failed for query") from e

    # Chroma expects List[List[float]] for query_embeddings.
    try:
        vec = query_embedding[0].tolist()
    except Exception as e:
        raise RuntimeError("Could not convert query embedding to list") from e

    where_clause: dict[str, Any] | None = filters if filters else None

    try:
        results = collection.query(
            query_embeddings=[vec],
            n_results=k,
            where=where_clause,
        )
    except ChromaError as e:
        logger.error("collection.query failed: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error during collection.query: %s", e, exc_info=True)
        raise RuntimeError("collection.query failed") from e

    return results


def reset_client_cache() -> None:
    """Clear cached model/collection (useful in tests or after rebuilding index)."""
    global _model, _collection
    _model = None
    _collection = None


def _print_sample_results(results: dict[str, Any], label: str) -> None:
    """Pretty-print first query batch (used by CLI demo)."""
    print(label)
    docs = results.get("documents") or []
    metas = results.get("metadatas") or []
    ids = results.get("ids") or []
    if not docs or not docs[0]:
        print("  (no documents returned)\n")
        return
    row_docs = docs[0]
    row_metas = metas[0] if metas and metas[0] else [{}] * len(row_docs)
    row_ids = ids[0] if ids and ids[0] else [""] * len(row_docs)

    for i, (doc, meta, chunk_id) in enumerate(zip(row_docs, row_metas, row_ids)):
        speaker = meta.get("speaker", "?")
        ch = meta.get("chapter", "?")
        v = meta.get("verse", "?")
        preview = (doc or "")[:100] + ("..." if len(doc or "") > 100 else "")
        print(f"{i + 1}. id={chunk_id!r} | {ch}.{v} ({speaker})")
        print(f"   {preview}\n")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
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
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except ValueError as e:
        logger.error("%s", e)
        return 1
    except ImportError as e:
        logger.error("%s", e)
        return 1
    except RuntimeError as e:
        logger.error("%s", e)
        return 1
    except ChromaError as e:
        logger.error("Chroma error: %s", e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
