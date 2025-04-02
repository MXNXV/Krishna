const fs = require('fs');
const path = require('path');

let scriptures = [];

function loadScripture() {
  if (scriptures.length) return scriptures;

  // Adjusted path to load from /data
  const jsonPath = path.join(__dirname, './data/bhagavad_gita_cleaned_from_csv.json');
  const raw = fs.readFileSync(jsonPath, 'utf-8');
  const parsed = JSON.parse(raw);

  // Add citation field like BG 1.1
  scriptures = parsed.map(verse => ({
    ...verse,
    citation: `BG ${verse.chapter}.${verse.verse}`,
    sanskrit: verse.sanskrit || ''
  }));

  return scriptures;
}

function searchVerses(allVerses, question, topN = 5) {
  const qWords = question.toLowerCase().split(/\W+/);
  return allVerses
    .map(verse => {
      const matchScore = qWords.filter(word => verse.text.toLowerCase().includes(word)).length;
      return { ...verse, score: matchScore };
    })
    .filter(v => v.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topN);
}

module.exports = {
  loadScripture,
  searchVerses
};
