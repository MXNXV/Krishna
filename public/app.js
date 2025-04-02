// Krishna Chatbot - Vrindavan Theme - app.js

document.addEventListener('DOMContentLoaded', () => {
  const chatBox = document.getElementById('chat-box');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const toggleCitation = document.getElementById('toggle-citation');
  const clearChat = document.getElementById('clear-chat');
  const verseBanner = document.getElementById('verse-of-the-day');

  sendBtn.addEventListener('click', handleSend);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
  });

  clearChat.addEventListener('click', () => {
    chatBox.innerHTML = '';
  });

  fetch('/api/sources')
    .then(res => res.json())
    .then(data => {
      if (data.sources?.length) fetchVerseOfTheDay();
    });

  function handleSend() {
    const question = userInput.value.trim();
    if (!question) return;

    addMessage({ text: question, sender: 'user' });
    userInput.value = '';

    addTypingEffect();

    fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })
      .then(res => res.json())
      .then(data => {
        removeTyping();
        addMessage({
          text: data.response || 'No response available.',
          sender: 'krishna',
          citation: data.source || '',
          sanskrit: data.sanskrit || ''
        });
      })
      .catch(() => {
        removeTyping();
        addMessage({ text: 'Sorry, Krishna is silent at the moment.', sender: 'krishna' });
      });
  }

  function addMessage({ text, sender = 'krishna', citation = '', sanskrit = '' }) {
    const segments = splitTextIntoChunks(text, 2);
  
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} w-full gap-2 items-start`;
  
    const avatar = document.createElement('div');
    avatar.className = 'flex-shrink-0';
    avatar.innerHTML =
      sender === 'krishna'
        ? `<div class="w-10 h-10"><img src="/krishna.png" alt="Krishna" class="w-full h-full rounded-full object-cover" /></div>`
        : `<div class="w-10 h-10"><img src="/user.png" alt="User" class="w-full h-full rounded-full object-cover" /></div>`;
  
    const messageGroup = document.createElement('div');
    messageGroup.className = 'flex flex-col space-y-2 max-w-[90%]';
  
    segments.forEach((segmentText, i) => {
      const bubble = document.createElement('div');
      bubble.className = `p-3 rounded-lg text-sm ${
        sender === 'user' ? 'user-bubble self-end' : 'krishna-bubble self-start'
      }`;
  
      bubble.innerHTML = `
        ${i === 0 && sanskrit ? `<p class="font-serif mb-2 text-yellow-100">${sanskrit}</p>` : ''}
        <p>${segmentText}</p>
        ${
          i === segments.length - 1 && citation && toggleCitation.checked
            ? `<small class="block mt-1 italic text-sm text-yellow-200">📜 ${citation}</small>`
            : ''
        }
        ${
          sender === 'krishna' && i === segments.length - 1
            ? `<button class="mt-1 text-xs underline text-blue-100 speak-btn">🗣️ Read</button>`
            : ''
        }
      `;
  
      messageGroup.appendChild(bubble);
    });
  
    if (sender === 'krishna') {
      wrapper.appendChild(avatar);
      wrapper.appendChild(messageGroup);
    } else {
      wrapper.appendChild(messageGroup);
      wrapper.appendChild(avatar);
    }
  
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
  
    if (sender === 'krishna') {
      const speakBtn = messageGroup.querySelector('.speak-btn');
      speakBtn?.addEventListener('click', () => speakText(text));
    }
  }
  
  

  function addTypingEffect() {
    removeTyping();

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator px-4 py-2 rounded-lg bg-white bg-opacity-10 text-white shadow-md mb-2';
    typingDiv.id = 'typing';
    typingDiv.innerHTML = `
      <div class="flex items-center space-x-2">
        <img src="/krishna.png" class="w-6 h-6 rounded-full" alt="Krishna" />
        <span class="text-sm">Krishna is responding<span class="dot-animation ml-1"></span></span>
      </div>
    `;

    const wrapper = document.createElement('div');
    wrapper.className = 'flex justify-start items-start';
    wrapper.appendChild(typingDiv);
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function removeTyping() {
    const typing = document.getElementById('typing');
    if (typing && typing.parentElement) {
      typing.parentElement.remove();
    }
  }


  function cleanVerse(text) {
    return text.replace(/^(My dear friend.*?)[:.?!]\s*/i, '').trim();
  }
  
  function fetchVerseOfTheDay() {
    fetch('/api/verse-of-the-day')
      .then(res => res.json())
      .then(data => {
        const trimmed = summarizeToTwoSentences(data.text);
        verseBanner.innerHTML = `
          🕉️ <span class="font-semibold text-black">${trimmed}</span><br>
          
        `;
        verseBanner.classList.remove('hidden');
      });
  }
  
  // Helper: summarize to 2 sentences max
  function summarizeToTwoSentences(text) {
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    return sentences.slice(0, 2).join(' ').trim();
  }
  

  

  function speakText(text) {
    const msg = new SpeechSynthesisUtterance(text);
    msg.lang = 'en-US';
    speechSynthesis.speak(msg);
  }
});

// ✂️ Helper: Split response into max 2 chunks
function splitTextIntoChunks(text, sentenceCount = 2) {
  const sentences = text.match(/[^.!?]+[.!?]+[\])'"`’”]*|.+$/g) || [];

  if (sentences.length <= sentenceCount) {
    return [sentences.join(' ').trim()];
  }

  const first = sentences.slice(0, sentenceCount).join(' ').trim();
  const second = sentences.slice(sentenceCount).join(' ').trim();
  return [first, second];
}
