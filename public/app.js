document.addEventListener('DOMContentLoaded', () => {
  const chatBox = document.getElementById('chat-box');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const toggleCitation = document.getElementById('toggle-citation');
  const clearChat = document.getElementById('clear-chat');
  const verseBanner = document.getElementById('verse-of-the-day');

  let conversationHistory = [];

  sendBtn.addEventListener('click', handleSend);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
  });

  clearChat.addEventListener('click', () => {
    chatBox.innerHTML = '';
    conversationHistory = [];
  });

  fetchVerseOfTheDay();

  function handleSend() {
    const question = userInput.value.trim();
    if (!question) return;

    addMessage({ text: question, sender: 'user' });
    userInput.value = '';
    addTypingEffect();

    fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        history: conversationHistory.slice(-4) // last 2 exchanges
      })
    })
      .then(res => res.json())
      .then(data => {
        removeTyping();
        addMessage({
          text: data.response,
          sender: 'krishna',
          citation: data.source,
          sanskrit: data.sanskrit
        });

        conversationHistory.push({ role: 'user', content: question });
        conversationHistory.push({ role: 'assistant', content: data.response });
      });
  }

  function addMessage({ text, sender, citation = '', sanskrit = '' }) {
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} items-start gap-2`;

    const avatar = document.createElement('div');
    avatar.innerHTML = sender === 'krishna'
      ? `<img src="/krishna.png" class="w-8 h-8 rounded-full" />`
      : `<img src="/user.png" class="w-8 h-8 rounded-full" />`;

    const bubble = document.createElement('div');
    bubble.className = `p-3 rounded-lg max-w-[80%] text-sm ${
      sender === 'user' ? 'user-bubble' : 'krishna-bubble'
    }`;
    bubble.innerHTML = `
      ${sanskrit ? `<p class="font-serif mb-2 text-yellow-100">${sanskrit}</p>` : ''}
      <p>${text}</p>
      ${
        citation && toggleCitation.checked
          ? `<small class="block mt-1 italic text-sm text-yellow-200">📜 ${citation}</small>`
          : ''
      }
      ${
        sender === 'krishna'
          ? `<button class="mt-1 text-xs underline text-blue-100 speak-btn">🗣️ Read</button>`
          : ''
      }
    `;

    if (sender === 'krishna') {
      wrapper.appendChild(avatar);
      wrapper.appendChild(bubble);
    } else {
      wrapper.appendChild(bubble);
      wrapper.appendChild(avatar);
    }

    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (sender === 'krishna') {
      const speakBtn = bubble.querySelector('.speak-btn');
      speakBtn?.addEventListener('click', () => speakText(text));
    }
  }

  function addTypingEffect() {
    removeTyping();
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing';
    typingDiv.innerHTML = `
      <div class="mr-2">Krishna is responding</div>
      <span></span><span></span><span></span>
    `;
    const wrapper = document.createElement('div');
    wrapper.className = 'flex justify-start items-start';
    wrapper.appendChild(typingDiv);
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function removeTyping() {
    const typing = document.getElementById('typing');
    if (typing) typing.parentElement.remove();
  }

  function speakText(text) {
    const msg = new SpeechSynthesisUtterance(text);
    msg.lang = 'en-US';
    speechSynthesis.speak(msg);
  }

  function fetchVerseOfTheDay() {
    fetch('/api/verse-of-the-day')
      .then(res => res.json())
      .then(data => {
        const short = summarizeToTwoSentences(data.text);
        verseBanner.innerHTML = `
          🕉️ <span class="font-semibold text-black">${short}</span><br>
          
        `;
        verseBanner.classList.remove('hidden');
      });
  }

  function summarizeToTwoSentences(text) {
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    return sentences.slice(0, 2).join(' ').trim();
  }
});
