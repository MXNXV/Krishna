from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import re

import chromadb
from chromadb.errors import NotFoundError

from src.config import DEFAULT_CHROMA_DIR, COLLECTION_NAME

logger = logging.getLogger(__name__)

_CHAPTER_BOUNDARIES: dict[int, tuple[int, int]] | None = None


def _get_chapter_boundaries(collection: Any) -> dict[int, tuple[int, int]]:
    """Query ChromaDB for chapter verse ranges."""
    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])
    
    boundaries: dict[int, tuple[int, int]] = {}

    for meta in metadatas:
        chapter = meta.get("chapter")
        verse = meta.get("verse")
        if chapter is None or verse is None:
            continue

        if chapter not in boundaries:
            boundaries[chapter] = (verse, verse)
        else:
            first_verse, last_verse = boundaries[chapter]
            boundaries[chapter] = (min(first_verse, verse), max(last_verse, verse))

    return boundaries


def _parse_verse_id(verse_id: str) -> tuple[int, int]:
    """Parse verse ID (BG2.47 or BG_2_47) into (chapter, verse)."""
    s = verse_id.strip()

    m = re.fullmatch(r"BG(\d+)\.(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.fullmatch(r"BG_(\d+)_(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))

    raise ValueError(f"Invalid verse id format: {verse_id!r}")


def _calculate_window(
    chapter: int, verse: int, window_size: int, boundaries: dict[int, tuple[int, int]]
) -> list[int]:
    """Calculate verse window around center verse, clamped to chapter boundaries."""
    first_verse, last_verse = boundaries[chapter]

    left = (window_size - 1) // 2
    right = window_size - 1 - left
    start = verse - left
    end = verse + right

    if start < first_verse:
        shift = first_verse - start
        start = first_verse
        end = min(last_verse, end + shift)
    if end > last_verse:
        shift = end - last_verse
        end = last_verse
        start = max(first_verse, start - shift)

    return list(range(start, end + 1))


def expand_context(
    verse_ids: list[str], window_size: int = 4, chroma_path: Path | str | None = None
) -> list[dict[str, Any]]:
    """Expand retrieved verses to include neighboring context within chapter boundaries."""
    global _CHAPTER_BOUNDARIES

    db_dir = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_DIR
    if not db_dir.is_dir():
        raise FileNotFoundError(f"Chroma directory not found: {db_dir}")

    client = chromadb.PersistentClient(path=str(db_dir))
    
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except NotFoundError:
        raise FileNotFoundError(f"Collection {COLLECTION_NAME!r} not found")

    if _CHAPTER_BOUNDARIES is None:
        _CHAPTER_BOUNDARIES = _get_chapter_boundaries(collection)

    expanded_chunks = []

    for verse_id in verse_ids:
        chapter, verse = _parse_verse_id(verse_id)
        window_verses = _calculate_window(chapter, verse, window_size, _CHAPTER_BOUNDARIES)
        window_ids = [f"BG{chapter}.{v}" for v in window_verses]

        results = collection.get(ids=window_ids, include=["documents", "metadatas"])
        result_ids = results.get("ids", [])

        if len(result_ids) < len(window_ids):
            missing = set(window_ids) - set(result_ids)
            logger.warning(
                "Context expansion for %s: %d/%d verses missing: %s",
                verse_id, len(missing), len(window_ids), missing
            )

        result_docs = results.get("documents", [])
        result_meta = results.get("metadatas", [])

        rows: list[tuple[int, str]] = []
        for rid, doc, meta in zip(result_ids, result_docs, result_meta):
            if not rid:
                continue
            try:
                _, row_verse = _parse_verse_id(str(rid))
            except ValueError:
                if isinstance(meta, dict) and meta.get("verse"):
                    row_verse = int(meta["verse"])
                else:
                    continue
            rows.append((row_verse, str(doc or "")))

        rows.sort(key=lambda x: x[0])
        combined_text = "\n".join(text for _, text in rows if text)

        chunk = {
            "center_verse_id": verse_id,
            "context_verse_ids": window_ids,
            "combined_text": combined_text,
            "metadata": {
                "chapter": chapter,
                "center_verse": verse,
                "window_size": len(window_ids),
                "chapter_range": _CHAPTER_BOUNDARIES.get(chapter),
                "resolved_context_count": len(rows),
            },
        }
        expanded_chunks.append(chunk)

    return expanded_chunks
