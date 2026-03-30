#!/usr/bin/env python
"""Generate embeddings for Bhagavad Gita verses."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generate_embeddings import main

if __name__ == "__main__":
    raise SystemExit(main())
