"""
Generate dense embeddings for Bhagavad Gita verses using SentenceTransformers.

Reads verse records from process_data (including cleaned English `text` per verse),
runs a MiniLM model, and prints the resulting embedding matrix shape.

Requires: sentence-transformers, torch (and optionally numpy for saving).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

from config import DEFAULT_CSV, DEFAULT_MODEL_NAME
from process_data import process_gita_data

logger = logging.getLogger(__name__)

# Re-export for callers that still import from this module.
__all__ = ["DEFAULT_CSV", "DEFAULT_MODEL_NAME", "generate_embeddings", "main"]


def _build_texts(verses: list[dict]) -> list[str]:
    """
    Extract embedding strings from verse dicts.

    Falls back to empty string if `text` missing (should not happen if process_data
    includes `text`); empty strings still produce a vector but add little signal.
    """
    texts: list[str] = []
    for i, v in enumerate(verses):
        t = v.get("text")
        if t is None:
            logger.warning("Verse index %s missing 'text' key; using empty string", i)
            texts.append("")
        else:
            texts.append(str(t).strip())
    return texts


def generate_embeddings(
    csv_path: Path | str | None = None,
    model_name: str = DEFAULT_MODEL_NAME,
    *,
    show_progress: bool = True,
) -> tuple[np.ndarray, list[dict]]:
    """
    Load verses from CSV, encode `text` field with SentenceTransformer.

    Args:
        csv_path: Path to Bhagwad_Gita.csv; defaults to data/Bhagwad_Gita.csv.
        model_name: HuggingFace / sentence-transformers model id.
        show_progress: Passed to model.encode progress bar.

    Returns:
        (embeddings, verses) where embeddings is shape (n_verses, dim).

    Raises:
        FileNotFoundError, ValueError, OSError: From process_gita_data or file I/O.
        RuntimeError: If encoding produces no rows or unexpected failure.
    """
    path = Path(csv_path) if csv_path is not None else DEFAULT_CSV

    try:
        verses = process_gita_data(path)
    except (FileNotFoundError, ValueError, OSError) as e:
        logger.error("Failed to load or parse CSV %s: %s", path, e)
        raise

    texts = _build_texts(verses)
    if not texts:
        raise ValueError("No texts to embed; verse list is empty.")

    empty_count = sum(1 for t in texts if not t)
    if empty_count:
        logger.warning("%s / %s verses have empty text", empty_count, len(texts))

    # Lazy import so --help or CSV-only checks don't require torch if unused.
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as e:
        raise ImportError(
            "Install sentence-transformers (and torch): "
            "pip install sentence-transformers"
        ) from e

    try:
        model = SentenceTransformer(model_name)
    except OSError as e:
        logger.error(
            "Could not load model %r (disk/network cache issue): %s", model_name, e
        )
        raise
    except Exception as e:
        logger.error("Unexpected error loading model %r: %s", model_name, e)
        raise RuntimeError(
            f"Failed to load SentenceTransformer model: {model_name}"
        ) from e

    try:
        embeddings = model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
    except (MemoryError, RuntimeError) as e:
        logger.error("Encoding failed (memory or backend error): %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error during encode: %s", e, exc_info=True)
        raise RuntimeError("model.encode failed") from e

    if embeddings is None or len(embeddings.shape) != 2:
        raise RuntimeError(f"Expected 2D embedding array, got {embeddings!r}")

    if embeddings.shape[0] != len(verses):
        raise RuntimeError(
            f"Embedding row count {embeddings.shape[0]} != verse count {len(verses)}"
        )

    return embeddings, verses


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(csv_arg) if csv_arg else DEFAULT_CSV

    try:
        embeddings, verses = generate_embeddings(csv_path=path)
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

    print(f"Verses: {len(verses)}")
    print(f"Generated embeddings shape: {embeddings.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
