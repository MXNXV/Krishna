"""
Process Bhagavad Gita CSV into verse-level metadata for RAG / indexing.

Each row becomes a dict with chunk_id, chapter, chapter_name, verse,
speaker (inferred from EngMeaning), token_count, and text (cleaned EngMeaning).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from config import CHAPTER_NAMES
import pandas as pd

logger = logging.getLogger(__name__)

# Traditional chapter titles (Sanskrit + English) for thematic retrieval metadata.


# CSV columns required for processing (ID, Chapter, Verse, EngMeaning).
REQUIRED_COLUMNS = ("ID", "Chapter", "Verse", "EngMeaning")

# Strip leading "2.47 "-style verse labels before speaker detection.
_VERSE_PREFIX_PATTERN = re.compile(r"^\d+\.\d+\.?\s*")
# Speaker: "<Name> said" at start of English meaning (after prefix strip).
_SPEAKER_PATTERN = re.compile(
    r"^([A-Za-z][A-Za-z\s\-]*?)\s+said\b", flags=re.IGNORECASE
)

# Narrator phrases in EngMeaning that map to Krishna for speaker-filtered retrieval.
_SPEAKER_ALIASES = {
    "The Blessed Lord": "Krishna",
    "Blessed Lord": "Krishna",
    "Sri Bhagavan": "Krishna",
}


def _safe_str(value: Any) -> str:
    """Convert cell to str; treat pandas NA/NaN as empty string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def speaker_name(eng_meaning_after_prefix: str) -> str:
    """
    Infer who is speaking from the English gloss (verse prefix already removed).

    Rules:
    - If text matches "<Name> said" at the start, use Name (with alias map).
    - Otherwise default to Krishna (typical for undecorated Krishna teachings).

    Args:
        eng_meaning_after_prefix: EngMeaning with leading "ch.v " stripped.

    Returns:
        Canonical speaker label, e.g. "Arjuna", "Krishna", "Sanjaya".
    """
    if not eng_meaning_after_prefix or not isinstance(eng_meaning_after_prefix, str):
        return "Krishna"

    text = eng_meaning_after_prefix.strip()
    if not text:
        return "Krishna"

    try:
        m = _SPEAKER_PATTERN.match(text)
        if not m:
            return "Krishna"
        raw_name = m.group(1).strip(" .,:;!-").title()
        return _SPEAKER_ALIASES.get(raw_name, raw_name)
    except (AttributeError, IndexError) as e:
        logger.warning("speaker_name regex failed for text=%r: %s", text[:80], e)
        return "Krishna"


def process_gita_data(csv_path: str | Path) -> list[dict[str, Any]]:
    """
    Read Bhagavad Gita CSV and return one dict per verse with metadata.

    Args:
        csv_path: Path to Bhagwad_Gita.csv (or compatible schema).

    Returns:
        List of verse records suitable for chunk metadata / indexing.

    Raises:
        FileNotFoundError: If csv_path does not exist.
        ValueError: If required columns are missing or CSV is empty.
        KeyError: Not raised; unknown chapters get a fallback chapter_name.

    Side effects:
        Logs warnings for rows that are skipped due to errors.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path.resolve()}")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as e:
        raise ValueError(f"CSV is empty or unreadable: {path}") from e
    except pd.errors.ParserError as e:
        raise ValueError(f"Failed to parse CSV (malformed file?): {path}") from e
    except OSError as e:
        raise OSError(f"Could not read CSV file: {path}") from e

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
            chapter_raw = df["Chapter"].iloc[i]
            verse_raw = df["Verse"].iloc[i]
            eng_raw = df["EngMeaning"].iloc[i]

            # Coerce chapter / verse to int when possible for stable metadata.
            try:
                chapter_number = int(chapter_raw)
            except (TypeError, ValueError) as e:
                logger.warning(
                    "Row %s: invalid Chapter %r, skipping row: %s", i, chapter_raw, e
                )
                continue

            try:
                verse = int(verse_raw)
            except (TypeError, ValueError) as e:
                logger.warning(
                    "Row %s: invalid Verse %r, skipping row: %s", i, verse_raw, e
                )
                continue

            if not chunk_id:
                logger.warning("Row %s: empty ID, skipping", i)
                continue

            # Chapter title for thematic filters; fallback if chapter out of range.
            chapter_name = CHAPTER_NAMES.get(
                chapter_number, f"Chapter {chapter_number} (unknown title)"
            )

            # English gloss: strip NaN, leading space, then verse prefix "2.47 "
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
                # Cleaned English gloss (verse prefix stripped); use for embeddings / display.
                "text": text,
            }
            processed_verses.append(verse_data)

        except Exception as e:
            # Catch-all so one bad row does not abort the whole pipeline.
            logger.warning("Row %s: unexpected error, skipping: %s", i, e, exc_info=True)
            continue

    if not processed_verses:
        raise ValueError(
            f"No verses could be processed from {path}; check logs for row errors."
        )

    return processed_verses


# if __name__ == "__main__":
#     from config import DEFAULT_CSV
#     verses = process_gita_data(DEFAULT_CSV)

#     # Check 1: Total count
#     assert len(verses) == 701, f"Expected 701 verses, got {len(verses)}"

#     # Check 2: First verse speaker
#     assert verses[0]['speaker'] == 'Dhritarashtra', f"First verse speaker wrong: {verses[0]['speaker']}"

#     # Check 3: Find a Krishna verse (verse 2.47 should be Krishna)
#     verse_2_47 = next(v for v in verses if v['chapter'] == 2 and v['verse'] == 47)
#     assert verse_2_47['speaker'] == 'Krishna', f"Verse 2.47 speaker wrong: {verse_2_47['speaker']}"

#     # Check 4: Find an Arjuna verse (3.1 should be Arjuna)
#     verse_3_1 = next(v for v in verses if v['chapter'] == 3 and v['verse'] == 1)
#     assert verse_3_1['speaker'] == 'Arjuna', f"Verse 3.1 speaker wrong: {verse_3_1['speaker']}"

#     print("✅ All checks passed!")
