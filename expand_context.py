from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import re

import chromadb
from chromadb.errors import ChromaError, NotFoundError

from config import DEFAULT_CHROMA_DIR, COLLECTION_NAME

logger = logging.getLogger(__name__)

# Global cache for chapter boundaries (populated on first use)
_CHAPTER_BOUNDARIES: dict[int, tuple[int, int]] | None = None


def _get_chapter_boundaries(collection: Any) -> dict[int, tuple[int, int]]:
    """
    Build a map of the chapter -> (first_verse, last_verse)

    Queries ChromaDB once and find all verse ranges per chapter

    Returns:
        dict[int, tuple[int, int]] eg. {1: (1,47), 2: (1,72)....}
    """
    try:
        # No filters: fetch all metadatas from the collection in one call.
        results = collection.get(include=["metadatas"])
    except ChromaError:
        raise
    except Exception as e:
        raise RuntimeError("Failed to read metadata from Chroma collection") from e

    metadatas = results.get("metadatas") if isinstance(results, dict) else None
    if not metadatas:
        return {}

    boundaries: dict[int, tuple[int, int]] = {}

    for meta in metadatas:
        if not isinstance(meta, dict):
            continue

        chapter_raw = meta.get("chapter")
        verse_raw = meta.get("verse")
        if chapter_raw is None or verse_raw is None:
            continue

        try:
            chapter = int(chapter_raw)
            verse = int(verse_raw)
        except (TypeError, ValueError):
            continue

        if chapter not in boundaries:
            boundaries[chapter] = (verse, verse)
        else:
            first_verse, last_verse = boundaries[chapter]
            boundaries[chapter] = (min(first_verse, verse), max(last_verse, verse))

    return boundaries


def _parse_verse_id(verse_id: str) -> tuple[int, int]:
    """
    Extract chapter number and verse from chunk ID

    Args:
        verse_id (str) eg. "BG_2_47"

    Returns:
        tuple[int, int] eg. (chapter, verse) like (2, 47)
    """
    # verse_id is in the format "BG_{chapter}_{verse}" (example: BG_2_47)
    s = verse_id.strip()

    # Canonical: BG2.47
    m = re.fullmatch(r"BG(\d+)\.(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))

    # Legacy: BG_2_47
    m = re.fullmatch(r"BG_(\d+)_(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))

    raise ValueError(f"Invalid verse id format: {verse_id!r}")


def _calculate_window(
    chapter: int, verse: int, window_size: int, boundaries: dict[int, tuple[int, int]]
) -> list[int]:
    """
    Calculate verse numbers in the context window

    Args:
        chapter (int): Chapter number
        verse (int): center verse number
        window_size (int): Total verses in the window (eg. 4)
        boundaries (dict[int, tuple[int, int]]): Chapter boundary map from _get_chapter_boundaries

    Returns:
        list[int]: List of verse numbers, eg. [46,47,48,49]

    Respect chapter boundaries and never crosses into another chapter
    """
    if window_size < 1:
        raise ValueError(f"window_size must be >= 1, got {window_size}")

    if chapter not in boundaries:
        raise ValueError(f"Chapter {chapter} not found in boundaries")

    first_verse, last_verse = boundaries[chapter]
    if verse < first_verse or verse > last_verse:
        raise ValueError(
            f"Verse {chapter}.{verse} outside chapter range {first_verse}-{last_verse}"
        )

    # Start with a symmetric window around center verse.
    left = (window_size - 1) // 2
    right = window_size - 1 - left
    start = verse - left
    end = verse + right

    # Clamp to chapter boundaries.
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
    """
    Expand retrieved verses to include neighboring context.

    For each verse, creates a window of surrounding verses while
    respecting chapter boundaries.

    Args:
        verse_ids: List of chunk IDs like ["BG_2_47", "BG_3_1"]
        window_size: Total verses in context window (default 4)
        chroma_path: Override ChromaDB path (optional)

    Returns:
        List of expanded context chunks

    Raises:
        FileNotFoundError: ChromaDB not found
        ValueError: Invalid verse_id format
        ChromaError: Database query failed
    """
    global _CHAPTER_BOUNDARIES

    if window_size < 1:
        raise ValueError(f"window_size must be >= 1, got {window_size}")

    db_dir = Path(chroma_path) if chroma_path is not None else DEFAULT_CHROMA_DIR
    if not db_dir.is_dir():
        raise FileNotFoundError(f"Chroma data directory not found: {db_dir.resolve()}")

    # Open ChromaDB collection
    try:
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection(COLLECTION_NAME)
    except NotFoundError as e:
        raise FileNotFoundError(
            f"Collection {COLLECTION_NAME!r} not found in {db_dir}"
        ) from e
    except ChromaError:
        raise
    except Exception as e:
        raise RuntimeError("Failed to open Chroma collection") from e

    # Get chapter boundaries (cached after first call)
    if _CHAPTER_BOUNDARIES is None:
        _CHAPTER_BOUNDARIES = _get_chapter_boundaries(collection)

    expanded_chunks = []

    for verse_id in verse_ids:
        # Parse verse ID
        chapter, verse = _parse_verse_id(verse_id)

        # Calculate window
        window_verses = _calculate_window(
            chapter, verse, window_size, _CHAPTER_BOUNDARIES
        )

        # Build verse IDs for the window
        window_ids = [f"BG{chapter}.{v}" for v in window_verses]

        # Fetch from ChromaDB
        try:
            results = collection.get(ids=window_ids, include=["documents", "metadatas"])
        except ChromaError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed fetching context for {verse_id}") from e

        result_ids = results.get("ids", []) if isinstance(results, dict) else []

        # CHECK: Log warning if some verses are missing
        if len(result_ids) < len(window_ids):
            missing = set(window_ids) - set(result_ids)
            logger.warning(
                "Context expansion for %s: %d/%d verses missing: %s",
                verse_id,
                len(missing),
                len(window_ids),
                missing,
            )

        result_docs = results.get("documents", []) if isinstance(results, dict) else []
        result_meta = results.get("metadatas", []) if isinstance(results, dict) else []

        rows: list[tuple[int, str]] = []
        for rid, doc, meta in zip(result_ids, result_docs, result_meta):  # type: ignore
            if not rid:
                continue
            try:
                _, row_verse = _parse_verse_id(str(rid))
            except ValueError:
                # Fallback to metadata verse when id format is unexpected.
                if isinstance(meta, dict) and meta.get("verse") is not None:
                    try:
                        row_verse = int(meta["verse"])
                    except (TypeError, ValueError):
                        continue
                else:
                    continue
            rows.append((row_verse, str(doc or "")))

        # Sort results by verse number and combine texts.
        rows.sort(key=lambda x: x[0])
        combined_text = "\n".join(text for _, text in rows if text)

        # Build expanded chunk
        chunk = {
            "center_verse_id": verse_id,
            "context_verse_ids": window_ids,
            "combined_text": combined_text,  # TODO: Create this
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
