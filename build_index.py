"""
Build a local ChromaDB vector index from Bhagavad Gita verse embeddings.

Pipeline:
1. Load CSV → verse metadata + text (via process_data).
2. Encode verses with SentenceTransformers (via generate_embeddings).
3. Persist vectors + documents + metadata in Chroma for RAG retrieval.

Run from project root (or any cwd): ``python build_index.py [optional_csv_path]``
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import chromadb  # type: ignore
from chromadb.errors import ChromaError, NotFoundError  # type: ignore

from config import (
    COLLECTION_DESCRIPTION,
    COLLECTION_NAME,
    DEFAULT_CHROMA_DIR,
    DEFAULT_CSV,
)
from generate_embeddings import generate_embeddings

logger = logging.getLogger(__name__)


def _verse_to_metadata(v: dict[str, Any]) -> dict[str, Any]:
    """
    Chroma metadata values must be str, int, float, or bool (JSON-friendly).

    We keep chapter/verse as ints for numeric filters and speaker as str.
    """
    return {
        "chapter": int(v["chapter"]),
        "chapter_name": str(v["chapter_name"]),
        "verse": int(v["verse"]),
        "speaker": str(v["speaker"]),
        "token_count": int(v["token_count"]),
    }


def build_index(
    csv_path: Path | str | None = None,
    chroma_path: Path | str | None = None,
) -> int:
    """
    Create (or replace) the Chroma collection with all verse embeddings.

    Args:
        csv_path: Gita CSV; defaults to data/Bhagwad_Gita.csv next to this script.
        chroma_path: Directory for PersistentClient; defaults to ./chroma_db under project.

    Returns:
        Number of rows indexed.

    Raises:
        FileNotFoundError, ValueError, OSError, ImportError, RuntimeError: From embedding step.
        ChromaError: From Chroma client/collection operations.
        RuntimeError: Wrapped failures (e.g. client init, unexpected add errors).
    """
    csv = Path(csv_path) if csv_path is not None else DEFAULT_CSV
    db_dir = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_DIR

    logger.info("Embedding verses from %s", csv)
    try:
        embeddings, verses = generate_embeddings(csv_path=csv)
    except (FileNotFoundError, ValueError, OSError, ImportError, RuntimeError):
        raise

    n = len(verses)
    if n == 0:
        raise ValueError("No verses to index.")

    emb_rows = embeddings.shape[0]
    if emb_rows != n:
        raise ValueError(f"Embedding rows ({emb_rows}) != verse count ({n}).")

    # Ensure parent exists; Chroma creates the leaf directory.
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("Cannot create Chroma directory %s: %s", db_dir, e)
        raise

    try:
        client = chromadb.PersistentClient(path=str(db_dir))
    except Exception as e:
        logger.error("Failed to open Chroma PersistentClient at %s: %s", db_dir, e)
        raise RuntimeError(f"Chroma PersistentClient failed for {db_dir}") from e

    # Fresh index: remove old collection if present (ignore missing).
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Removed existing collection %r", COLLECTION_NAME)
    except NotFoundError:
        logger.debug("No existing collection %r to delete", COLLECTION_NAME)
    except ChromaError as e:
        logger.warning(
            "delete_collection raised (continuing if new create works): %s", e
        )

    try:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": COLLECTION_DESCRIPTION},
        )
    except ChromaError as e:
        logger.error("create_collection failed: %s", e)
        raise

    ids = [str(v["chunk_id"]) for v in verses]
    documents = [str(v.get("text") or "") for v in verses]
    metadatas = [_verse_to_metadata(v) for v in verses]

    try:
        # Chroma expects embeddings as List[List[float]].
        emb_list = embeddings.tolist()
        collection.add(
            ids=ids,
            embeddings=emb_list,
            documents=documents,
            metadatas=metadatas,  # type: ignore
        )
    except ChromaError as e:
        logger.error("collection.add failed: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error during collection.add: %s", e, exc_info=True)
        raise RuntimeError("collection.add failed") from e

    logger.info("Stored %s verses in ChromaDB at %s", n, db_dir)
    return n


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    chroma_arg = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        count = build_index(csv_path=csv_arg, chroma_path=chroma_arg)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except ValueError as e:
        logger.error("%s", e)
        return 1
    except ImportError as e:
        logger.error("%s", e)
        return 1
    except OSError as e:
        logger.error("I/O error: %s", e)
        return 1
    except RuntimeError as e:
        logger.error("%s", e)
        return 1
    except ChromaError as e:
        logger.error("Chroma error: %s", e)
        return 1

    print(f"Stored {count} verses in ChromaDB (collection={COLLECTION_NAME!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
