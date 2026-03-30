from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

from src.config import DEFAULT_CSV, DEFAULT_MODEL_NAME
from src.process_data import process_gita_data

logger = logging.getLogger(__name__)


def generate_embeddings(
    csv_path: Path | str | None = None,
    model_name: str = DEFAULT_MODEL_NAME,
    *,
    show_progress: bool = True,
) -> tuple[np.ndarray, list[dict]]:
    """Generate embeddings for all verses using SentenceTransformer."""
    path = Path(csv_path) if csv_path is not None else DEFAULT_CSV
    
    verses = process_gita_data(path)
    texts = [v.get("text", "") for v in verses]
    
    if not texts:
        raise ValueError("No texts to embed")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
    )

    return embeddings, verses


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(csv_arg) if csv_arg else DEFAULT_CSV

    embeddings, verses = generate_embeddings(csv_path=path)
    print(f"Verses: {len(verses)}")
    print(f"Generated embeddings shape: {embeddings.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
