(function () {
  const LOGO_SVG = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white"/>
    <circle cx="8" cy="10" r="1.5" fill="#1565C0"/>
    <circle cx="12" cy="10" r="1.5" fill="#1565C0"/>
    <circle cx="16" cy="10" r="1.5" fill="#1565C0"/>
  </svg>`;

  const css = `
    #__chat-fab {
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      font-family: 'Instrument Sans', 'Segoe UI', sans-serif;
    }
    #__chat-fab-btn {
      width: 56px; height: 56px; border-radius: 50%;
      background: linear-gradient(135deg, #1565C0, #2196F3);
      box-shadow: 0 4px 20px rgba(33,150,243,0.45);
      border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: transform 0.22s cubic-bezier(0.4,0,0.2,1), box-shadow 0.22s;
      position: relative;
    }
    #__chat-fab-btn:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(33,150,243,0.58);
    }
    #__chat-fab-badge {
      position: absolute; top: -2px; right: -2px;
      width: 18px; height: 18px; border-radius: 50%;
      background: #ef4444; color: #fff;
      font-size: 10px; font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      border: 2px solid #fff;
      animation: __pulse 2s infinite;
    }
    @keyframes __pulse {
      0%,100% { transform: scale(1); }
      50%      { transform: scale(1.15); }
    }
    #__chat-panel {
      position: fixed; bottom: 90px; right: 24px; z-index: 9998;
      width: 360px; height: 520px;
      background: var(--surface, #fff);
      border: 1px solid rgba(21,101,192,0.14);
      border-radius: 20px;
      box-shadow: 0 16px 56px rgba(21,101,192,0.18), 0 4px 12px rgba(0,0,0,0.08);
      display: flex; flex-direction: column; overflow: hidden;
      opacity: 0; pointer-events: none;
      transform: translateY(16px) scale(0.96);
      transition: opacity 0.25s cubic-bezier(0.4,0,0.2,1),
                  transform 0.25s cubic-bezier(0.4,0,0.2,1);
    }
    #__chat-panel.open {
      opacity: 1; pointer-events: all;
      transform: translateY(0) scale(1);
    }
    #__chat-panel-header {
      padding: 14px 16px;
      background: linear-gradient(135deg, #1565C0, #2196F3);
      display: flex; align-items: center; gap: 10px;
      flex-shrink: 0;
    }
    #__chat-panel-header .hd-title {
      flex: 1; color: #fff; font-weight: 700; font-size: 15px;
    }
    #__chat-panel-header .hd-sub {
      color: rgba(255,255,255,0.7); font-size: 12px;
    }
    #__chat-panel-header .hd-actions { display: flex; gap: 4px; }
    #__chat-panel-header button {
      width: 30px; height: 30px; border-radius: 8px;
      background: rgba(255,255,255,0.15); border: none;
      color: #fff; font-size: 16px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }
    #__chat-panel-header button:hover { background: rgba(255,255,255,0.28); }
    #__mini-conv-list {
      flex-shrink: 0; border-bottom: 1px solid rgba(21,101,192,0.10);
    }
    .mini-conv {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 14px; cursor: pointer;
      transition: background 0.15s; border-bottom: 1px solid rgba(21,101,192,0.07);
    }
    .mini-conv:hover { background: #F4F6FA; }
    .mini-conv.active { background: #E3F2FD; }
    .mini-av {
      width: 34px; height: 34px; border-radius: 50%;
      background: #E3F2FD; color: #1565C0;
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 12px; flex-shrink: 0;
      position: relative;
    }
    .mini-online {
      position: absolute; bottom: 0; right: 0;
      width: 9px; height: 9px; border-radius: 50%;
      background: #22C55E; border: 2px solid #fff;
    }
    .mini-body { flex: 1; min-width: 0; }
    .mini-name { font-size: 13px; font-weight: 600; color: #0D1B2A; }
    .mini-prev { font-size: 11px; color: #6B7C93; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .mini-badge {
      min-width: 16px; height: 16px; padding: 0 4px;
      border-radius: 999px; background: #2196F3;
      color: #fff; font-size: 10px; font-weight: 700;
      display: flex; align-items: center; justify-content: center;
    }
    #__mini-chat {
      flex: 1; display: none; flex-direction: column; overflow: hidden;
    }
    #__mini-chat.show { display: flex; }
    #__mini-chat-header {
      padding: 10px 14px; border-bottom: 1px solid rgba(21,101,192,0.10);
      display: flex; align-items: center; gap: 8px; flex-shrink: 0;
    }
    #__mini-chat-header .back {
      background: none; border: none; cursor: pointer;
      font-size: 18px; color: #6B7C93; padding: 2px 4px;
    }
    #__mini-msgs {
      flex: 1; overflow-y: auto; padding: 12px 14px;
      display: flex; flex-direction: column; gap: 6px;
    }
    .mb { max-width: 80%; padding: 8px 12px; border-radius: 14px; font-size: 13px; line-height: 1.5; }
    .mb.me  { background: linear-gradient(135deg,#1565C0,#2196F3); color:#fff; align-self:flex-end; border-bottom-right-radius:4px; }
    .mb.them{ background:#F4F6FA; color:#0D1B2A; border:1px solid rgba(21,101,192,0.10); align-self:flex-start; border-bottom-left-radius:4px; }
    .mb-time{ font-size:10px; opacity:0.6; margin-top:3px; }
    #__mini-input-row {
      padding: 10px 12px; border-top: 1px solid rgba(21,101,192,0.10);
      display: flex; gap: 8px; align-items: flex-end; flex-shrink: 0;
    }
    #__mini-input-row textarea {
      flex: 1; border: 1.5px solid rgba(21,101,192,0.18);
      border-radius: 14px; padding: 8px 12px;
      font-size: 13px; font-family: inherit;
      background: #F4F6FA; color: #0D1B2A;
      outline: none; resize: none; max-height: 80px; line-height: 1.4;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    #__mini-input-row textarea:focus {
      border-color: #2196F3; box-shadow: 0 0 0 3px rgba(33,150,243,0.10);
    }
    #__mini-send {
      width: 36px; height: 36px; border-radius: 50%;
      background: linear-gradient(135deg,#1565C0,#2196F3);
      color: #fff; border: none; cursor: pointer;
      font-size: 16px; display: flex; align-items: center;
      justify-content: center; flex-shrink: 0;
      transition: transform 0.15s, box-shadow 0.15s;
      box-shadow: 0 2px 8px rgba(33,150,243,0.30);
    }
    #__mini-send:hover { transform: scale(1.1); }
    #__full-chat-link {
      text-align: center; padding: 10px;
      border-top: 1px solid rgba(21,101,192,0.08); flex-shrink: 0;
    }
    #__full-chat-link a {
      font-size: 13px; color: #1565C0; font-weight: 600; text-decoration: none;
    }
    #__full-chat-link a:hover { text-decoration: underline; }
    @media (max-width: 480px) {
      #__chat-panel { width: calc(100vw - 32px); right: 16px; bottom: 80px; height: 480px; }
      #__chat-fab   { right: 16px; bottom: 16px; }
    }
  `;

  const styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  const convos = [
    { id: 'c1', name: 'Karim Boudjemaa', av: 'كب', online: true,  unread: 3, last: 'Sure, I can start Monday…',   bg: '#E3F2FD', color: '#1565C0',
      msgs: [
        { from: 'them', text: 'Hi! I saw your profile and I\'m interested in your design services.', time: '10:02 AM' },
        { from: 'me',   text: 'Thank you! Happy to help. What do you need?', time: '10:04 AM' },
        { from: 'them', text: 'We need 3 social media posts per week.', time: '10:06 AM' },
        { from: 'me',   text: 'I can handle that. What platforms?', time: '10:07 AM' },
        { from: 'them', text: 'Sure, I can start Monday if that works…', time: '10:09 AM' },
      ]
    },
    { id: 'c2', name: 'Sara Mansouri',   av: 'سم', online: true,  unread: 0, last: 'Attached the revised version.', bg: 'rgba(255,193,7,0.15)', color: '#8a6010',
      msgs: [
        { from: 'me',   text: 'Hi Sara, interested in your landing page service.', time: 'Yesterday' },
        { from: 'them', text: 'Great! What kind of page?', time: 'Yesterday' },
        { from: 'them', text: 'Thank you! I attached the revised version.', time: 'Yesterday' },
      ]
    },
    { id: 'c3', name: 'TechStore DZ',    av: 'تد', online: false, unread: 0, last: 'We\'d like to hire you.',      bg: 'rgba(255,193,7,0.12)', color: '#8a6010',
      msgs: [
        { from: 'them', text: 'We\'d like to hire you for our project.', time: '2 days ago' },
        { from: 'me',   text: 'I\'d love to hear more details!', time: '2 days ago' },
      ]
    },
  ];

  let open = false;
  let currentConvo = null;
  let totalUnread  = convos.reduce((s, c) => s + c.unread, 0);

  const fab = document.createElement('div');
  fab.id = '__chat-fab';
  fab.innerHTML = `
    <div id="__chat-panel">
      <div id="__chat-panel-header">
        <div>
          <div class="hd-title">💬 Messages</div>
          <div class="hd-sub" id="__panel-sub">You have ${totalUnread} unread</div>
        </div>
        <div class="hd-actions">
          <button onclick="window.location.href='chat.html'" title="Open full chat">⤢</button>
          <button id="__panel-close" title="Close">✕</button>
        </div>
      </div>
      <div id="__mini-conv-list"></div>
      <div id="__mini-chat">
        <div id="__mini-chat-header">
          <button class="back" id="__mini-back">←</button>
          <div class="mini-av" id="__mini-chat-av">?</div>
          <div>
            <div style="font-weight:700;font-size:13px;" id="__mini-chat-name">User</div>
            <div style="font-size:11px;color:#22C55E;" id="__mini-chat-status">Online</div>
          </div>
          <a href="chat.html" style="margin-left:auto;font-size:12px;color:#1565C0;font-weight:600;text-decoration:none;">Full view →</a>
        </div>
        <div id="__mini-msgs"></div>
        <div id="__mini-input-row">
          <textarea id="__mini-txt" rows="1" placeholder="Type a message…"
            onkeydown="window.__widgetSendKey(event)"
            oninput="this.style.height='';this.style.height=Math.min(this.scrollHeight,80)+'px'"></textarea>
          <button id="__mini-send" onclick="window.__widgetSend()">➤</button>
        </div>
      </div>
      <div id="__full-chat-link">
        <a href="chat.html">Open full messages page →</a>
      </div>
    </div>
    <button id="__chat-fab-btn" aria-label="Open messages">
      ${LOGO_SVG}
      ${totalUnread > 0 ? `<div id="__chat-fab-badge">${totalUnread}</div>` : ''}
    </button>
  `;
  document.body.appendChild(fab);

  const panel    = document.getElementById('__chat-panel');
  const convList = document.getElementById('__mini-conv-list');
  const miniChat = document.getElementById('__mini-chat');
  const miniMsgs = document.getElementById('__mini-msgs');

  function renderConvList() {
    convList.innerHTML = '';
    convos.forEach(c => {
      const div = document.createElement('div');
      div.className = 'mini-conv';
      div.innerHTML = `
        <div class="mini-av" style="background:${c.bg};color:${c.color};">
          ${c.av}
          ${c.online ? '<div class="mini-online"></div>' : ''}
        </div>
        <div class="mini-body">
          <div class="mini-name">${c.name}</div>
          <div class="mini-prev">${c.last}</div>
        </div>
        ${c.unread > 0 ? `<div class="mini-badge">${c.unread}</div>` : ''}
      `;
      div.onclick = () => openMiniChat(c.id);
      convList.appendChild(div);
    });
  }

  function openMiniChat(id) {
    currentConvo = convos.find(c => c.id === id);
    if (!currentConvo) return;

    currentConvo.unread = 0;
    totalUnread = convos.reduce((s, c) => s + c.unread, 0);
    updateBadge();
    renderConvList();

    document.getElementById('__mini-chat-av').textContent = currentConvo.av;
    document.getElementById('__mini-chat-av').style.cssText = `background:${currentConvo.bg};color:${currentConvo.color};width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex-shrink:0;`;
    document.getElementById('__mini-chat-name').textContent = currentConvo.name;
    const st = document.getElementById('__mini-chat-status');
    st.textContent = currentConvo.online ? '🟢 Online' : '⚫ Offline';
    st.style.color = currentConvo.online ? '#22C55E' : '#6B7C93';

    convList.style.display = 'none';
    miniChat.classList.add('show');
    document.getElementById('__full-chat-link').style.display = 'none';
    document.getElementById('__panel-sub').textContent = currentConvo.name;

    renderMiniMsgs();
  }

  function renderMiniMsgs() {
    miniMsgs.innerHTML = '';
    currentConvo.msgs.forEach(m => appendMiniMsg(m));
    miniMsgs.scrollTop = miniMsgs.scrollHeight;
  }

  function appendMiniMsg(m) {
    const div = document.createElement('div');
    div.innerHTML = `<div class="mb ${m.from}">${escW(m.text)}<div class="mb-time">${m.time}</div></div>`;
    miniMsgs.appendChild(div);
    miniMsgs.scrollTop = miniMsgs.scrollHeight;
  }

  window.__widgetSend = function () {
    const ta   = document.getElementById('__mini-txt');
    const text = ta.value.trim();
    if (!text || !currentConvo) return;
    const now = new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' });
    const msg = { from: 'me', text, time: now };
    currentConvo.msgs.push(msg);
    currentConvo.last = text;
    appendMiniMsg(msg);
    ta.value = ''; ta.style.height = '';
    if (Math.random() > 0.4) {
      setTimeout(() => {
        const replies = ['Got it!', 'Thanks for the message 👍', 'I\'ll get back to you shortly.', 'Sounds good!'];
        const r = { from: 'them', text: replies[Math.floor(Math.random() * replies.length)], time: new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' }) };
        currentConvo.msgs.push(r);
        currentConvo.last = r.text;
        appendMiniMsg(r);
      }, 1600);
    }
  };

  window.__widgetSendKey = function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); window.__widgetSend(); }
  };

  document.getElementById('__mini-back').onclick = function () {
    miniChat.classList.remove('show');
    convList.style.display = '';
    document.getElementById('__full-chat-link').style.display = '';
    document.getElementById('__panel-sub').textContent = `You have ${totalUnread} unread`;
    currentConvo = null;
  };

  document.getElementById('__chat-fab-btn').onclick = function () {
    open = !open;
    panel.classList.toggle('open', open);
    if (open) renderConvList();
  };

  document.getElementById('__panel-close').onclick = function () {
    open = false; panel.classList.remove('open');
  };

  document.addEventListener('click', function (e) {
    if (open && !fab.contains(e.target)) {
      open = false; panel.classList.remove('open');
    }
  });

  function updateBadge() {
    const old = document.getElementById('__chat-fab-badge');
    if (old) old.remove();
    if (totalUnread > 0) {
      const b = document.createElement('div');
      b.id = '__chat-fab-badge';
      b.textContent = totalUnread;
      document.getElementById('__chat-fab-btn').appendChild(b);
    }
    const sub = document.getElementById('__panel-sub');
    if (sub && !currentConvo) sub.textContent = `You have ${totalUnread} unread`;
  }

  function escW(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
  }

  renderConvList();
})();
