#!/usr/bin/env python
"""Build ChromaDB index from Bhagavad Gita CSV."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.build_index import main

if __name__ == "__main__":
    raise SystemExit(main())
