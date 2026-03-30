from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import chromadb
from chromadb.errors import NotFoundError

from src.config import (
    COLLECTION_DESCRIPTION,
    COLLECTION_NAME,
    DEFAULT_CHROMA_DIR,
    DEFAULT_CSV,
)
from src.generate_embeddings import generate_embeddings

logger = logging.getLogger(__name__)


def _verse_to_metadata(v: dict[str, Any]) -> dict[str, Any]:
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
    """Create or replace the Chroma collection with all verse embeddings."""
    csv = Path(csv_path) if csv_path is not None else DEFAULT_CSV
    db_dir = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_DIR

    logger.info("Embedding verses from %s", csv)
    embeddings, verses = generate_embeddings(csv_path=csv)

    db_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_dir))

    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Removed existing collection %r", COLLECTION_NAME)
    except NotFoundError:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": COLLECTION_DESCRIPTION},
    )

    ids = [str(v["chunk_id"]) for v in verses]
    documents = [str(v.get("text", "")) for v in verses]
    metadatas = [_verse_to_metadata(v) for v in verses]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=metadatas,
    )

    logger.info("Stored %s verses in ChromaDB at %s", len(verses), db_dir)
    return len(verses)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    chroma_arg = sys.argv[2] if len(sys.argv) > 2 else None

    count = build_index(csv_path=csv_arg, chroma_path=chroma_arg)
    print(f"Stored {count} verses in ChromaDB (collection={COLLECTION_NAME!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
