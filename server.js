const express = require('express');
const cors = require('cors');
const path = require('path');
const dotenv = require('dotenv');
const bodyParser = require('body-parser');

const { queryLLM } = require('./llm-helper');
const { loadScripture, searchVerses } = require('./file-processor');

dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.static('public'));
app.use(bodyParser.json());

// Load scriptures on startup
const allVerses = loadScripture();

// Root route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public/index.html'));
});

// Get list of sources (if needed)
app.get('/api/sources', (req, res) => {
  res.json({ sources: ['bhagavad_gita'] });
});

// 🔮 Random verse of the day
app.get('/api/verse-of-the-day', (req, res) => {
  const random = allVerses[Math.floor(Math.random() * allVerses.length)];
  res.json({
    text: random.text,
    citation: random.citation || `BG ${random.chapter}.${random.verse}`,
    sanskrit: random.sanskrit || ''
  });
});

// 🕉️ Main query to Krishna
app.post('/api/query', async (req, res) => {
  const question = req.body.question;
  if (!question) return res.status(400).json({ error: 'No question provided.' });

  const matches = searchVerses(allVerses, question, 5);
  const context = matches.map(v => `• ${v.text} (${v.citation})`).join('\n');

  const prompt = `
You are Shri Krishna, speaking in the present day as a wise, playful, compassionate friend.

Your words are grounded in SCRIPTURES provided below — but you explain them using modern language.
You can use today's metaphors: social media, careers, stress, relationships, emotions — but stay true to the meaning of the scripture.
If there's no suitable verse, say: "This is beyond what I can reveal right now."

Speak casually and warmly. Like you’re helping a friend over chai. No formal lecture vibes. Keep it simple, clear, and honest.

SCRIPTURES:
${context}

QUESTION:
${question}

KRISHNA'S RESPONSE:
`;

  try {
    const rawReply = await queryLLM(prompt);
    const trimmedReply = trimToThreeSentences(rawReply);

    res.json({
      response: trimmedReply,
      source: matches.map(v => v.citation).join(', '),
      sanskrit: matches.map(v => v.sanskrit).filter(Boolean).join('\n')
    });
  } catch (err) {
    console.error('LLM error:', err.message);
    res.status(500).json({ error: 'Krishna is silent right now.' });
  }
});

// ✂️ Helper: limit to 3 sentences
function trimToThreeSentences(text) {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  return sentences.slice(0, 4).join(' ').trim();
}

// Start server
app.listen(PORT, () => {
  console.log(`✅ Krishna Chatbot running at http://localhost:${PORT}`);
});
