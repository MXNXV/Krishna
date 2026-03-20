"""
Central paths and constants for the Bhagavad Gita RAG pipeline.

Change values here only; other modules import from this file.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project layout
# ---------------------------------------------------------------------------

# Directory containing this file (project / repo root for these scripts).
PROJECT_ROOT: Path = Path(__file__).resolve().parent

# Subfolder for CSV and other raw data.
DATA_DIR: Path = PROJECT_ROOT / "data"

# ---------------------------------------------------------------------------
# Source data
# ---------------------------------------------------------------------------

GITA_CSV_FILENAME: str = "Bhagwad_Gita.csv"
DEFAULT_CSV: Path = DATA_DIR / GITA_CSV_FILENAME

# ---------------------------------------------------------------------------
# Embeddings (must match between indexing and retrieval)
# ---------------------------------------------------------------------------

DEFAULT_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------

DEFAULT_CHROMA_DIR: Path = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME: str = "bhagavad-gita"
COLLECTION_DESCRIPTION: str = "Bhagavad Gita verses for RAG"

# ---------------------------------------------------------------------------
# Metadata (chapter titles for thematic retrieval)
# ---------------------------------------------------------------------------

CHAPTER_NAMES: dict[int, str] = {
    1: "Arjuna Vishada Yoga (Grief of Arjuna)",
    2: "Sankhya Yoga (Transcendental Knowledge)",
    3: "Karma Yoga (Path of Action)",
    4: "Jnana Karma Sanyasa Yoga (Path of Knowledge)",
    5: "Karma Sanyasa Yoga (Action and Renunciation)",
    6: "Dhyana Yoga (Path of Meditation)",
    7: "Jnana Vijnana Yoga (Knowledge and Wisdom)",
    8: "Aksara Brahma Yoga (The Eternal Godhead)",
    9: "Raja Vidya Raja Guhya Yoga (Sovereign Knowledge)",
    10: "Vibhuti Yoga (Divine Manifestations)",
    11: "Visvarupa Darsana Yoga (Universal Form)",
    12: "Bhakti Yoga (Path of Devotion)",
    13: "Ksetra Ksetrajna Vibhaga Yoga (Field and Knower)",
    14: "Gunatraya Vibhaga Yoga (Three Modes of Nature)",
    15: "Purusottama Yoga (Supreme Divine Person)",
    16: "Daivasura Sampad Vibhaga Yoga (Divine and Demonic)",
    17: "Sraddhatraya Vibhaga Yoga (Three Types of Faith)",
    18: "Moksa Sanyasa Yoga (Liberation and Renunciation)",
}

# ---------------------------------------------------------------------------
# Retrieval defaults
# ---------------------------------------------------------------------------

DEFAULT_RETRIEVAL_K: int = 5
DEFAULT_CONTEXT_WINDOW_SIZE: int = 4

# ---------------------------------------------------------------------------
# Answer-generation defaults
# ---------------------------------------------------------------------------

DEFAULT_ANSWER_MODEL: str = "gpt-4o-mini"
DEFAULT_ANSWER_TEMPERATURE: float = 0.3
DEFAULT_ANSWER_MAX_TOKENS: int = 800

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "GITA_CSV_FILENAME",
    "DEFAULT_CSV",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_CHROMA_DIR",
    "COLLECTION_NAME",
    "COLLECTION_DESCRIPTION",
    "DEFAULT_RETRIEVAL_K",
    "DEFAULT_CONTEXT_WINDOW_SIZE",
    "DEFAULT_ANSWER_MODEL",
    "DEFAULT_ANSWER_TEMPERATURE",
    "DEFAULT_ANSWER_MAX_TOKENS",
]
