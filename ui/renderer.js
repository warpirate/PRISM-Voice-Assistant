// Renderer process for PRISM UI
const { ipcRenderer } = require('electron');

// DOM Elements
const orb = document.getElementById('orb');
const panel = document.getElementById('panel');
const userQuery = document.getElementById('user-query');
const responseContent = document.getElementById('response-content');
const typingIndicator = document.querySelector('.typing-indicator');
const statusText = document.getElementById('status-text');
const closePanel = document.getElementById('close-panel');
const settingsBtn = document.getElementById('settings-btn');
const waveformCanvas = document.getElementById('waveform');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');

// Waveform visualization
let waveformCtx = waveformCanvas.getContext('2d');
let animationId;
let waveformData = [];

// Initialize canvas size
function initWaveform() {
  waveformCanvas.width = 120;
  waveformCanvas.height = 120;
}

// Draw waveform animation
function drawWaveform() {
  waveformCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  
  const centerX = waveformCanvas.width / 2;
  const centerY = waveformCanvas.height / 2;
  const bars = 32;
  const radius = 40;
  
  for (let i = 0; i < bars; i++) {
    const angle = (Math.PI * 2 * i) / bars;
    const barHeight = waveformData[i] || Math.random() * 20 + 5;
    
    const x1 = centerX + Math.cos(angle) * radius;
    const y1 = centerY + Math.sin(angle) * radius;
    const x2 = centerX + Math.cos(angle) * (radius + barHeight);
    const y2 = centerY + Math.sin(angle) * (radius + barHeight);
    
    waveformCtx.strokeStyle = `rgba(255, 255, 255, ${0.3 + Math.random() * 0.4})`;
    waveformCtx.lineWidth = 2;
    waveformCtx.beginPath();
    waveformCtx.moveTo(x1, y1);
    waveformCtx.lineTo(x2, y2);
    waveformCtx.stroke();
  }
  
  // Update waveform data
  waveformData = waveformData.map(() => Math.random() * 20 + 5);
  
  animationId = requestAnimationFrame(drawWaveform);
}

// Start waveform animation
function startWaveform() {
  initWaveform();
  drawWaveform();
}

// Stop waveform animation
function stopWaveform() {
  if (animationId) {
    cancelAnimationFrame(animationId);
    waveformCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  }
}

// Orb state management
function setOrbState(state) {
  orb.className = '';
  
  switch(state) {
    case 'idle':
      orb.classList.add('orb-idle');
      stopWaveform();
      break;
    case 'listening':
      orb.classList.add('orb-listening');
      startWaveform();
      break;
    case 'speaking':
      orb.classList.add('orb-speaking');
      startWaveform();
      break;
    default:
      orb.classList.add('orb-idle');
      stopWaveform();
  }
}

// Show panel with animation
function showPanel(query = '', response = '') {
  panel.classList.remove('hidden', 'animate__fadeOut');
  panel.classList.add('animate__fadeIn');
  
  if (query) {
    userQuery.textContent = query;
    userQuery.style.display = 'block';
  } else {
    userQuery.style.display = 'none';
  }
  
  if (response) {
    typingIndicator.classList.add('hidden');
    responseContent.textContent = response;
  } else {
    typingIndicator.classList.remove('hidden');
    responseContent.textContent = '';
  }
}

// Hide panel with animation
function hidePanel() {
  panel.classList.remove('animate__fadeIn');
  panel.classList.add('animate__fadeOut');
  
  setTimeout(() => {
    panel.classList.add('hidden');
  }, 300);
}

// Update status
function updateStatus(status, color = '#4cd964') {
  statusText.textContent = status;
  document.querySelector('.status-dot').style.background = color;
}

// Event Listeners
orb.addEventListener('click', () => {
  ipcRenderer.send('orb-clicked');
  setOrbState('listening');
  showPanel('', '');
  updateStatus('Listening...', '#667eea');
});

closePanel.addEventListener('click', () => {
  hidePanel();
  setOrbState('idle');
  updateStatus('Ready', '#4cd964');
});

settingsBtn.addEventListener('click', () => {
  ipcRenderer.send('open-settings');
});

function sendTextQuery() {
  const text = (textInput?.value || '').trim();
  if (!text) return;
  setOrbState('listening');
  showPanel('', '');
  updateStatus('Processing...', '#ffa500');
  ipcRenderer.send('text-query', text);
}

if (sendBtn) {
  sendBtn.addEventListener('click', () => {
    sendTextQuery();
  });
}

if (textInput) {
  textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendTextQuery();
    }
  });
}

// IPC Event Handlers
ipcRenderer.on('wake-word-detected', () => {
  setOrbState('listening');
  showPanel('', '');
  updateStatus('Listening...', '#667eea');
});

ipcRenderer.on('speech-recognized', (event, text) => {
  userQuery.textContent = text;
  userQuery.style.display = 'block';
  typingIndicator.classList.remove('hidden');
  responseContent.textContent = '';
  updateStatus('Processing...', '#ffa500');
});

ipcRenderer.on('response-ready', (event, data) => {
  typingIndicator.classList.add('hidden');
  responseContent.textContent = data.text;
  setOrbState('speaking');
  updateStatus('Speaking...', '#4cd964');
});

ipcRenderer.on('response-complete', () => {
  setTimeout(() => {
    hidePanel();
    setOrbState('idle');
    updateStatus('Ready', '#4cd964');
  }, 2000);
});

ipcRenderer.on('error', (event, error) => {
  typingIndicator.classList.add('hidden');
  responseContent.textContent = `Error: ${error}`;
  responseContent.style.color = '#ff6b6b';
  updateStatus('Error', '#ff6b6b');
  
  setTimeout(() => {
    responseContent.style.color = 'white';
    hidePanel();
    setOrbState('idle');
    updateStatus('Ready', '#4cd964');
  }, 3000);
});

ipcRenderer.on('update-status', (event, status) => {
  updateStatus(status.text, status.color || '#4cd964');
});

// Initialize
initWaveform();
setOrbState('idle');
updateStatus('Ready', '#4cd964');

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Escape to close panel
  if (e.key === 'Escape') {
    hidePanel();
    setOrbState('idle');
  }
  
  // Ctrl+Space to activate
  if (e.ctrlKey && e.code === 'Space') {
    orb.click();
  }
});

// Prevent default drag behavior
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => e.preventDefault());
