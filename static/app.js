// AI Assistant Unlimited - Frontend Application
// This file contains the main UI logic for the chat/build interface

const DEFAULT_SESSION_ID = 'default';
let currentMode = 'chat';
let currentSession = DEFAULT_SESSION_ID;
let currentModel = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  initializeUI();
  loadStatus();
  setupEventListeners();
  loadChatHistory();
});

function initializeUI() {
  const app = document.getElementById('app');
  const theme = localStorage.getItem('theme') || 'dark';
  app.setAttribute('data-theme', theme);
}

function setupEventListeners() {
  // Mode buttons
  document.getElementById('modeChat')?.addEventListener('click', () => switchMode('chat'));
  document.getElementById('modeBuild')?.addEventListener('click', () => switchMode('build'));
  
  // Chat input
  const input = document.getElementById('input');
  const send = document.getElementById('send');
  
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  input?.addEventListener('input', () => {
    send.disabled = !input.value.trim();
    autoResizeTextarea(input);
  });
  
  send?.addEventListener('click', sendMessage);
  
  // Download button
  document.getElementById('downloadBtn')?.addEventListener('click', downloadProject);
  document.getElementById('newBtn')?.addEventListener('click', newProject);
  
  // Model selector
  document.getElementById('modelSelect')?.addEventListener('change', (e) => {
    currentModel = e.target.value;
    localStorage.setItem('selectedModel', currentModel);
  });
  
  // File explorer
  document.getElementById('newFileBtn')?.addEventListener('click', createNewFile);
  document.getElementById('newFolderBtn')?.addEventListener('click', createNewFolder);
  document.getElementById('refreshFilesBtn')?.addEventListener('click', refreshFiles);
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function switchMode(mode) {
  currentMode = mode;
  document.getElementById('modeChat')?.classList.toggle('active', mode === 'chat');
  document.getElementById('modeBuild')?.classList.toggle('active', mode === 'build');
}

async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    
    currentModel = localStorage.getItem('selectedModel') || data.model;
    
    // Update model selector
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
      modelSelect.innerHTML = '';
      data.models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        option.selected = model === currentModel;
        modelSelect.appendChild(option);
      });
    }
    
    // Update status indicator
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const modelDot = document.getElementById('modelDot');
    
    if (data.ollama_running) {
      statusDot?.classList.add('ok');
      statusText.textContent = 'Connected';
      modelDot?.classList.add('ok');
    } else {
      statusDot?.classList.remove('ok');
      statusText.textContent = 'Disconnected';
      modelDot?.classList.remove('ok');
    }
  } catch (e) {
    console.error('Failed to load status:', e);
  }
}

async function sendMessage() {
  const input = document.getElementById('input');
  const message = input.value.trim();
  
  if (!message) return;
  
  const messages = document.getElementById('messages');
  
  // Add user message
  const userBubble = document.createElement('div');
  userBubble.className = 'message user';
  userBubble.innerHTML = `<div class="message-bubble">${escapeHtml(message)}</div>`;
  messages.appendChild(userBubble);
  
  input.value = '';
  input.style.height = 'auto';
  messages.scrollTop = messages.scrollHeight;
  
  try {
    const endpoint = currentMode === 'build' ? '/api/build' : '/api/chat';
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        model: currentModel,
        session_id: currentSession
      })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error || 'Request failed');
    }
    
    // Add assistant message
    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'message assistant';
    assistantBubble.innerHTML = `<div class="message-bubble">${escapeHtml(data.response)}</div>`;
    messages.appendChild(assistantBubble);
    
    messages.scrollTop = messages.scrollHeight;
    
    // Update files if in build mode
    if (currentMode === 'build' && data.files) {
      updateFileList(data.files);
      if (data.has_preview) {
        showPreview();
      }
    }
    
    saveChatHistory();
  } catch (e) {
    const errorBubble = document.createElement('div');
    errorBubble.className = 'message assistant';
    errorBubble.innerHTML = `<div class="message-bubble" style="color: #ef4444;">Error: ${escapeHtml(e.message)}</div>`;
    messages.appendChild(errorBubble);
  }
}

function updateFileList(files) {
  const fileList = document.getElementById('fileList');
  fileList.innerHTML = '';
  
  files.forEach(file => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
      <span>${file.split('/').pop()}</span>
    `;
    item.addEventListener('click', () => openFile(file));
    fileList.appendChild(item);
  });
}

function openFile(path) {
  // TODO: Implement file opening/editing with Monaco Editor
  console.log('Opening file:', path);
}

function showPreview() {
  // Switch to preview tab
  document.getElementById('editorView')?.classList.add('hidden');
  document.getElementById('previewView')?.classList.remove('hidden');
}

function downloadProject() {
  window.location.href = '/api/project/download';
}

async function newProject() {
  if (confirm('Start a new project? This will clear your current files.')) {
    try {
      await fetch('/api/project/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSession })
      });
      
      document.getElementById('messages').innerHTML = `
        <div class="welcome">
          <div class="big-logo">🤖</div>
          <h2>What should we build?</h2>
          <p>Switch to <b>Build</b> mode and describe an app — it appears live on the right in a real code editor, ready to download as a ZIP. Or just <b>Chat</b>.</p>
        </div>
      `;
      
      document.getElementById('fileList').innerHTML = '';
    } catch (e) {
      console.error('Failed to clear project:', e);
    }
  }
}

function createNewFile() {
  const name = prompt('Enter file name:');
  if (name) {
    // TODO: Implement file creation
  }
}

function createNewFolder() {
  const name = prompt('Enter folder name:');
  if (name) {
    // TODO: Implement folder creation
  }
}

async function refreshFiles() {
  try {
    const res = await fetch('/api/project/files');
    const data = await res.json();
    updateFileList(data.files);
  } catch (e) {
    console.error('Failed to refresh files:', e);
  }
}

function saveChatHistory() {
  const messages = document.getElementById('messages');
  const history = [];
  
  messages.querySelectorAll('.message').forEach(msg => {
    history.push({
      role: msg.classList.contains('user') ? 'user' : 'assistant',
      content: msg.querySelector('.message-bubble').textContent
    });
  });
  
  localStorage.setItem(`chat-${currentSession}`, JSON.stringify(history));
}

function loadChatHistory() {
  const history = localStorage.getItem(`chat-${currentSession}`);
  if (history) {
    const messages = document.getElementById('messages');
    messages.innerHTML = '';
    
    JSON.parse(history).forEach(msg => {
      const bubble = document.createElement('div');
      bubble.className = `message ${msg.role}`;
      bubble.innerHTML = `<div class="message-bubble">${escapeHtml(msg.content)}</div>`;
      messages.appendChild(bubble);
    });
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Periodically refresh status
setInterval(loadStatus, 5000);
