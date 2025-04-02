const axios = require('axios');
require('dotenv').config();

const API_KEY = process.env.GROQ_API_KEY;

async function queryLLM(prompt) {
  try {
    const response = await axios.post(
      'https://api.groq.com/openai/v1/chat/completions',
      {
        model: 'llama-3.3-70b-versatile', // ✅ confirmed model from Groq's list
        messages: [
          {
            role: 'system',
            content: `You are Krishna, a wise, compassionate, and informal mentor. Answer all questions like you're giving heartfelt advice to a dear friend. Base your answers only on the scripture provided. Be kind, concise, and use simple language.`,
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.6,
        max_tokens: 700,
        top_p: 1,
        stream: false
      },
      {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          'Content-Type': 'application/json',
        }
      }
    );

    return response.data.choices[0]?.message?.content?.trim() || '[Krishna is silent right now.]';
  } catch (err) {
    console.error('LLM API error:', err.response?.data || err.message);
    return '[Krishna is silent right now.]';
  }
}

module.exports = { queryLLM };
