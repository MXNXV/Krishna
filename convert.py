from pathlib import Path
import re
import json

# Load the uploaded text
txt_path = Path(r"E:\Krishna\Bhagavad-Gita As It Is (Original 1972 Edition).txt")
text = txt_path.read_text(encoding='utf-8', errors='ignore')

# Pattern to extract chapter and verse numbers followed by text
# This assumes format like: "Chapter 1", then lines starting with "1.1", "1.2", etc.
chapter_pattern = re.compile(r'Chapter\s+(\d+)', re.IGNORECASE)
verse_pattern = re.compile(r'(\d+)\.(\d+)\s*[:\-–]?\s*(.*)')

results = []
current_chapter = None

lines = text.splitlines()
for line in lines:
    line = line.strip()
    if not line:
        continue
    # Check for chapter heading
    chapter_match = chapter_pattern.match(line)
    if chapter_match:
        current_chapter = int(chapter_match.group(1))
        continue
    # Check for verse
    verse_match = verse_pattern.match(line)
    if verse_match and current_chapter is not None:
        chapter = current_chapter
        verse = int(verse_match.group(2))
        verse_text = verse_match.group(3).strip()
        results.append({
            "chapter": chapter,
            "verse": verse,
            "text": verse_text,
            "keywords": []
        })

# Save the result as JSON
json_path = r"E:\Krishna\bhagavad_gita_extracted.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

json_path
