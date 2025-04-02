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

app.use(cors());
app.use(express.static('public'));
app.use(bodyParser.json());

const allVerses = loadScripture();

// Serve homepage
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public/index.html'));
});

// Verse of the Day — randomized
app.get('/api/verse-of-the-day', (req, res) => {
  const random = allVerses[Math.floor(Math.random() * allVerses.length)];
  res.json({
    text: random.text,
    citation: random.citation || `BG ${random.chapter}.${random.verse}`,
    sanskrit: random.sanskrit || ''
  });
});

// Krishna response with memory
app.post('/api/query', async (req, res) => {
  const { question, history = [] } = req.body;
  if (!question) return res.status(400).json({ error: 'No question provided.' });

  const matches = searchVerses(allVerses, question, 5);
  const context = matches.map(v => `• ${v.text} (${v.citation})`).join('\n');

  const chatHistory = history.map(msg => {
    const who = msg.role === 'assistant' ? 'Krishna' : 'User';
    return `${who}: ${msg.content}`;
  }).join('\n');

  const prompt = `
You are Shri Krishna, speaking in the present day as a wise, playful, compassionate friend.

Use only the SCRIPTURES below to answer the QUESTION.
You may use casual, modern language — like you're texting a dear friend — but stay true to the verses.
If nothing fits, say: "This is beyond what I can reveal right now."

Here’s the conversation so far:
${chatHistory}

SCRIPTURES:
${context}

QUESTION:
${question}

KRISHNA'S RESPONSE:
`;

  try {
    const rawReply = await queryLLM(prompt);
    const trimmed = trimToThreeSentences(rawReply);

    res.json({
      response: trimmed,
      source: matches.map(v => v.citation).join(', '),
      sanskrit: matches.map(v => v.sanskrit).filter(Boolean).join('\n')
    });
  } catch (err) {
    console.error('LLM error:', err.message);
    res.status(500).json({ error: 'Krishna is sleeping right now.' });
  }
});

function trimToThreeSentences(text) {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  return sentences.slice(0, 3).join(' ').trim();
}

app.listen(PORT, () => {
  console.log(`✅ Krishna Chatbot running at http://localhost:${PORT}`);
});
