function toast(message, type = 'success') {
  let e = document.querySelector('.toast');
  if (!e) {
    e = document.createElement('div');
    e.className = 'toast';
    document.body.append(e);
  }
  e.textContent = message;
  e.style.background = type === 'error' ? '#EF4444' : '#2E7D32';
  e.classList.add('show');
  setTimeout(() => e.classList.remove('show'), 3200);
}

function requireAuth() {
  if (!localStorage.getItem('shiksha_token')) location.href = 'login.html';
}

function logout() {
  localStorage.removeItem('shiksha_token');
  localStorage.removeItem('shiksha_user');
  location.href = 'index.html';
}

function formatDate(v) {
  return new Date(v).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function toggleAiAssistant() {
  const drawer = document.querySelector('#aiDrawer');
  if (drawer) drawer.classList.toggle('open');
}

function sendAiQuestion() {
  const input = document.querySelector('#aiInput');
  const body = document.querySelector('#aiBody');
  if (!input || !input.value.trim()) return;
  const q = input.value.trim();
  input.value = '';
  
  const userMsg = document.createElement('div');
  userMsg.className = 'ai-msg user';
  userMsg.textContent = q;
  body.appendChild(userMsg);
  body.scrollTop = body.scrollHeight;

  setTimeout(() => {
    const botMsg = document.createElement('div');
    botMsg.className = 'ai-msg bot';
    botMsg.innerHTML = `✨ <b>Shiksha AI:</b> Great question! Key concepts are summarized in your lesson flashcards & detailed notes. Keep reviewing!`;
    body.appendChild(botMsg);
    body.scrollTop = body.scrollHeight;
  }, 700);
}

function shell(active, title, bodyContent) {
  const nav = [
    ['dashboard.html', '⌂', 'Dashboard'],
    ['upload.html', '⇧', 'Upload PDF'],
    ['summary.html', '▤', 'My Lessons'],
    ['audio.html', '♫', 'Audio Lessons'],
    ['quiz.html', '?', 'Quiz'],
    ['flashcards.html', '▣', 'Flashcards'],
    ['profile.html', '◉', 'Profile']
  ];

  document.body.innerHTML = `
    <div class="app">
      <aside class="sidebar">
        <a class="brand" href="dashboard.html">Shiksha<span>AI</span></a>
        <nav class="menu">
          ${nav.map(x => `<a class="${active === x[0] ? 'active' : ''}" href="${x[0]}"><span>${x[1]}</span> <span>${x[2]}</span></a>`).join('')}
          <a href="#" onclick="logout()" style="margin-top:auto; color:#FCA5A5;"><span>↪</span> <span>Logout</span></a>
        </nav>
      </aside>
      
      <main class="content">
        <header class="topbar">
          <div>
            <h1>${title}</h1>
            <div class="muted" style="font-size:13px; margin-top:2px;">Learn smarter, one lesson at a time.</div>
          </div>
          <div class="topbar-meta">
            <span class="badge badge-gold">🔥 17 Day Streak</span>
            <span class="badge badge-blue">🏆 1200 XP</span>
            <div class="topbar-user">
              <div class="avatar" id="userAvatar">🙂</div>
              <b id="userName" style="font-size:14px;">Student</b>
            </div>
          </div>
        </header>
        ${bodyContent}
      </main>
    </div>

    <!-- Floating AI Assistant Widget -->
    <button class="ai-fab" onclick="toggleAiAssistant()">🤖 <span>Ask AI</span></button>
    <div class="ai-drawer" id="aiDrawer">
      <div class="ai-header">
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:18px;">🤖</span>
          <b>Shiksha Assistant</b>
        </div>
        <button onclick="toggleAiAssistant()" style="background:none; border:0; color:white; font-size:18px; cursor:pointer;">✕</button>
      </div>
      <div class="ai-body" id="aiBody">
        <div class="ai-msg bot">
          👋 Hi! I'm your AI study assistant. Ask me anything about your uploaded textbooks or study notes!
        </div>
      </div>
      <div class="ai-footer">
        <input id="aiInput" type="text" placeholder="Ask a question..." onkeydown="if(event.key==='Enter') sendAiQuestion()">
        <button class="btn" style="padding:8px 14px; border-radius:20px;" onclick="sendAiQuestion()">Send</button>
      </div>
    </div>
  `;

  const u = JSON.parse(localStorage.getItem('shiksha_user') || '{}');
  const name = u.name || 'Student';
  document.querySelector('#userName').textContent = name.split(' ')[0];
  document.querySelector('#userAvatar').textContent = name.charAt(0).toUpperCase() || '🙂';
}

function setSpeechStatus(message) {
  document.querySelectorAll('[data-speech-status]').forEach(x => x.textContent = message);
}

function playLesson(script, voice = 'female') {
  if (!('speechSynthesis' in window)) {
    toast('Audio playback is not supported in this browser', 'error');
    return;
  }
  window.speechSynthesis.cancel();
  let utterance = new SpeechSynthesisUtterance(script);
  utterance.rate = 0.92;
  utterance.pitch = voice === 'female' ? 1.08 : 0.92;
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => voice === 'female' ? /female|zira|samantha/i.test(v.name) : /male|david|mark/i.test(v.name));
  if (preferred) utterance.voice = preferred;
  utterance.onend = () => setSpeechStatus('Ready to play');
  setSpeechStatus('Playing audio lesson…');
  window.speechSynthesis.speak(utterance);
}

function pauseLesson() {
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.pause();
    setSpeechStatus('Paused');
  }
}

function resumeLesson() {
  if (window.speechSynthesis.paused) {
    window.speechSynthesis.resume();
    setSpeechStatus('Playing audio lesson…');
  }
}

function stopLesson() {
  window.speechSynthesis.cancel();
  setSpeechStatus('Ready to play');
}

// Auth Helper Utilities
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    if (btn) btn.innerHTML = '👁️‍🗨️';
  } else {
    input.type = 'password';
    if (btn) btn.innerHTML = '👁️';
  }
}

function checkPasswordStrength(password) {
  let score = 0;
  if (!password) return { score: 0, label: '', color: '#CBD5E1', width: '0%' };
  if (password.length >= 8) score += 25;
  if (password.length >= 12) score += 15;
  if (/[A-Z]/.test(password)) score += 20;
  if (/[0-9]/.test(password)) score += 20;
  if (/[^A-Za-z0-9]/.test(password)) score += 20;

  if (score < 40) {
    return { score, label: 'Weak', color: '#EF4444', width: '33%' };
  } else if (score < 75) {
    return { score, label: 'Medium', color: '#F59E0B', width: '66%' };
  } else {
    return { score, label: 'Strong', color: '#10B981', width: '100%' };
  }
}

