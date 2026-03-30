from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from src.config import CHAPTER_NAMES
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("ID", "Chapter", "Verse", "EngMeaning")

_VERSE_PREFIX_PATTERN = re.compile(r"^\d+\.\d+\.?\s*")
_SPEAKER_PATTERN = re.compile(
    r"^([A-Za-z][A-Za-z\s\-]*?)\s+said\b", flags=re.IGNORECASE
)

_SPEAKER_ALIASES = {
    "The Blessed Lord": "Krishna",
    "Blessed Lord": "Krishna",
    "Sri Bhagavan": "Krishna",
}


def _safe_str(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def speaker_name(eng_meaning_after_prefix: str) -> str:
    """Extract speaker from text pattern '<Name> said' or default to Krishna."""
    if not eng_meaning_after_prefix:
        return "Krishna"

    text = eng_meaning_after_prefix.strip()
    if not text:
        return "Krishna"

    m = _SPEAKER_PATTERN.match(text)
    if not m:
        return "Krishna"
    raw_name = m.group(1).strip(" .,:;!-").title()
    return _SPEAKER_ALIASES.get(raw_name, raw_name)


def process_gita_data(csv_path: str | Path) -> list[dict[str, Any]]:
    """Read Bhagavad Gita CSV and return verse metadata for indexing."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path.resolve()}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"CSV has no data rows: {path}")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV missing required columns {missing}. Found: {list(df.columns)}"
        )

    processed_verses: list[dict[str, Any]] = []

    for i in range(len(df)):
        try:
            chunk_id = _safe_str(df["ID"].iloc[i])
            chapter_number = int(df["Chapter"].iloc[i])
            verse = int(df["Verse"].iloc[i])
            eng_raw = df["EngMeaning"].iloc[i]

            if not chunk_id:
                continue

            chapter_name = CHAPTER_NAMES.get(
                chapter_number, f"Chapter {chapter_number}"
            )

            text = _safe_str(eng_raw)
            text = _VERSE_PREFIX_PATTERN.sub("", text)
            speaker = speaker_name(text)
            token_count = len(text.split()) if text else 0

            verse_data = {
                "chunk_id": chunk_id,
                "chapter": chapter_number,
                "chapter_name": chapter_name,
                "verse": verse,
                "speaker": speaker,
                "token_count": token_count,
                "text": text,
            }
            processed_verses.append(verse_data)

        except (TypeError, ValueError):
            continue

    if not processed_verses:
        raise ValueError(f"No verses could be processed from {path}")

    return processed_verses

