/**
 * PRISM Renderer Process
 * Handles UI interactions, animations, and communication with main process
 */

const { ipcRenderer } = require('electron');

// ============================================================================
// State Management
// ============================================================================

const AppState = {
    currentState: 'idle',
    isListening: false,
    isProcessing: false,
    isLiveMode: false,
    conversationHistory: [],
    settings: {
        theme: 'dark',
        voiceFeedback: true,
        transparency: 85,
        animationSpeed: 'normal'
    }
};

// ============================================================================
// DOM Elements
// ============================================================================

const elements = {
    // Orb
    orb: document.getElementById('prismOrb'),
    stateIndicator: document.getElementById('stateIndicator'),
    waveform: document.getElementById('waveform'),
    matrixDisplay: document.getElementById('matrixDisplay'),
    
    // Messages
    messagesContainer: document.getElementById('messagesContainer'),
    conversationPanel: document.getElementById('conversationPanel'),
    
    // Input
    voiceBtn: document.getElementById('voiceBtn'),
    liveVoiceBtn: document.getElementById('liveVoiceBtn'),
    textInput: document.getElementById('textInput'),
    sendBtn: document.getElementById('sendBtn'),
    
    // Controls
    minimizeBtn: document.getElementById('minimizeBtn'),
    closeBtn: document.getElementById('closeBtn'),
    clearBtn: document.getElementById('clearBtn'),
    settingsBtn: document.getElementById('settingsBtn'),
    
    // Settings
    settingsPanel: document.getElementById('settingsPanel'),
    closeSettings: document.getElementById('closeSettings'),
    themeSelect: document.getElementById('themeSelect'),
    voiceFeedback: document.getElementById('voiceFeedback'),
    transparencySlider: document.getElementById('transparencySlider'),
    animationSpeed: document.getElementById('animationSpeed')
};

// ============================================================================
// Matrix Display Instance
// ============================================================================

let matrixInstance = null;

// ============================================================================
// Initialization
// ============================================================================

function initialize() {
    setupEventListeners();
    setupWaveform();
    setupMatrix();
    loadSettings();
    
    // Initialize glass effects
    if (typeof glassEffects !== 'undefined') {
        glassEffects.init();
    }
    
    console.log('PRISM UI initialized');
}

function setupEventListeners() {
    // Orb interaction
    elements.orb.addEventListener('click', handleOrbClick);
    
    // Voice button
    elements.voiceBtn.addEventListener('click', activateVoice);
    
    // Live Voice button
    elements.liveVoiceBtn.addEventListener('click', toggleLiveVoice);
    
    // Text input
    elements.textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTextMessage();
        }
    });
    
    // Send button
    elements.sendBtn.addEventListener('click', sendTextMessage);
    
    // Controls
    elements.minimizeBtn.addEventListener('click', () => {
        ipcRenderer.send('minimize-window');
    });
    
    elements.closeBtn.addEventListener('click', () => {
        ipcRenderer.send('close-window');
    });
    
    elements.clearBtn.addEventListener('click', clearConversation);
    
    // Settings
    elements.settingsBtn.addEventListener('click', () => {
        elements.settingsPanel.classList.remove('hidden');
    });
    
    elements.closeSettings.addEventListener('click', () => {
        elements.settingsPanel.classList.add('hidden');
    });
    
    // Settings controls
    elements.themeSelect.addEventListener('change', updateSettings);
    elements.voiceFeedback.addEventListener('change', updateSettings);
    elements.transparencySlider.addEventListener('input', updateSettings);
    elements.animationSpeed.addEventListener('change', updateSettings);
    
    // Backend messages
    ipcRenderer.on('backend-message', (event, data) => {
        handleBackendMessage(data);
    });
}

// ============================================================================
// Voice Activation
// ============================================================================

function handleOrbClick() {
    activateVoice();
}

function activateVoice() {
    if (AppState.isLiveMode) {
        console.log('Cannot use push-to-talk in Live Voice mode');
        return;
    }
    console.log('Activating voice...');
    elements.voiceBtn.classList.add('active');
    ipcRenderer.send('activate-voice');
}

function toggleLiveVoice() {
    console.log('Toggling Live Voice mode...');
    AppState.isLiveMode = !AppState.isLiveMode;
    
    if (AppState.isLiveMode) {
        elements.liveVoiceBtn.classList.add('active');
        elements.voiceBtn.disabled = true;
        elements.voiceBtn.style.opacity = '0.5';
        elements.textInput.placeholder = 'Live Voice active - speak naturally...';
        ipcRenderer.send('toggle-live-voice', { enabled: true });
        addMessage('system', 'Live Voice mode activated. Speak naturally - I\'m listening continuously.');
    } else {
        elements.liveVoiceBtn.classList.remove('active');
        elements.voiceBtn.disabled = false;
        elements.voiceBtn.style.opacity = '1';
        elements.textInput.placeholder = 'Type or use voice...';
        ipcRenderer.send('toggle-live-voice', { enabled: false });
        addMessage('system', 'Live Voice mode deactivated.');
    }
}

// ============================================================================
// Text Input
// ============================================================================

function sendTextMessage() {
    const text = elements.textInput.value.trim();
    
    if (!text) return;
    
    console.log('Sending text:', text);
    
    // Add user message to UI immediately
    addMessage('user', text);
    
    // Clear input
    elements.textInput.value = '';
    
    // Mark this message as already displayed to prevent duplication
    elements.textInput.dataset.lastSent = text;
    
    // Send to backend
    ipcRenderer.send('send-text', text);
}

// ============================================================================
// Message Management
// ============================================================================

function addMessage(role, content, timestamp = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    // Apply glass enhancement if available
    if (typeof glassEffects !== 'undefined') {
        messageDiv.classList.add('glass-enhanced');
    }
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessage(content);
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = timestamp || formatTime(new Date());
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    elements.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    
    // Store in history
    AppState.conversationHistory.push({ role, content, timestamp: new Date() });
}

function formatMessage(content) {
    // Basic markdown-like formatting
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function formatTime(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message assistant-message typing-indicator';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
        <div class="message-content">
            <div style="display: flex; gap: 6px;">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    
    elements.messagesContainer.appendChild(indicator);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function clearConversation() {
    // Keep system message
    const systemMessage = elements.messagesContainer.querySelector('.system-message');
    elements.messagesContainer.innerHTML = '';
    if (systemMessage) {
        elements.messagesContainer.appendChild(systemMessage);
    }
    
    AppState.conversationHistory = [];
    
    // Notify backend
    ipcRenderer.send('send-to-backend', { type: 'clear_conversation' });
}

// ============================================================================
// State Management
// ============================================================================

function setState(newState) {
    const oldState = AppState.currentState;
    AppState.currentState = newState;
    
    console.log(`State: ${oldState} -> ${newState}`);
    
    // Update orb
    elements.orb.className = 'orb ' + newState;
    
    // Update indicator text
    const stateText = elements.stateIndicator.querySelector('.state-text');
    stateText.textContent = newState.charAt(0).toUpperCase() + newState.slice(1);
    
    // Update Matrix display
    setMatrixState(newState);
    
    // Handle state-specific actions
    switch (newState) {
        case 'listening':
            elements.voiceBtn.classList.add('active');
            startWaveformAnimation();
            break;
        
        case 'processing':
            elements.voiceBtn.classList.remove('active');
            stopWaveformAnimation();
            showTypingIndicator();
            break;
        
        case 'responding':
            hideTypingIndicator();
            break;
        
        case 'executing':
            // Executing state handled by matrix animation
            break;
        
        case 'idle':
            elements.voiceBtn.classList.remove('active');
            stopWaveformAnimation();
            hideTypingIndicator();
            break;
        
        case 'error':
            elements.voiceBtn.classList.remove('active');
            stopWaveformAnimation();
            hideTypingIndicator();
            break;
        
        case 'shutdown':
            // Shutdown animation will play once
            break;
    }
}

// ============================================================================
// Matrix Display Setup
// ============================================================================

function setupMatrix() {
    if (!elements.matrixDisplay) {
        console.error('Matrix display element not found');
        return;
    }

    // Initialize matrix with startup animation
    matrixInstance = new Matrix(elements.matrixDisplay, {
        rows: 7,
        cols: 7,
        size: 12,
        gap: 3,
        palette: {
            on: 'rgba(138, 180, 248, 1)',
            off: 'rgba(138, 180, 248, 0.08)'
        },
        brightness: 1,
        autoplay: true,
        loop: true,
        ariaLabel: 'PRISM status indicator'
    });

    // Start with startup animation
    matrixInstance.setFrames(MatrixPresets.startup.frames);
    matrixInstance.options.fps = MatrixPresets.startup.fps;
    matrixInstance.options.loop = false;
    matrixInstance.play();

    // After startup, transition to idle
    setTimeout(() => {
        setMatrixState('idle');
    }, 1500);
}

function setMatrixState(state) {
    if (!matrixInstance) return;

    const preset = MatrixPresets[state];
    if (!preset) {
        console.warn(`No matrix preset for state: ${state}`);
        return;
    }

    matrixInstance.setFrames(preset.frames);
    matrixInstance.options.fps = preset.fps;
    matrixInstance.options.loop = state !== 'startup' && state !== 'shutdown';
    matrixInstance.play();
}

// ============================================================================
// Waveform Visualization
// ============================================================================

let waveformContext = null;
let waveformAnimation = null;

function setupWaveform() {
    const canvas = elements.waveform;
    canvas.width = 160;
    canvas.height = 160;
    waveformContext = canvas.getContext('2d');
}

function startWaveformAnimation() {
    if (waveformAnimation) return;
    
    let phase = 0;
    
    function animate() {
        if (!waveformContext) return;
        
        const ctx = waveformContext;
        const width = ctx.canvas.width;
        const height = ctx.canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw waveform
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        const radius = 60;
        const points = 32;
        
        for (let i = 0; i <= points; i++) {
            const angle = (i / points) * Math.PI * 2;
            const wave = Math.sin(angle * 3 + phase) * 8 + Math.cos(angle * 5 + phase * 1.5) * 5;
            const r = radius + wave;
            const x = centerX + Math.cos(angle) * r;
            const y = centerY + Math.sin(angle) * r;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.closePath();
        ctx.stroke();
        
        phase += 0.05;
        waveformAnimation = requestAnimationFrame(animate);
    }
    
    animate();
}

function stopWaveformAnimation() {
    if (waveformAnimation) {
        cancelAnimationFrame(waveformAnimation);
        waveformAnimation = null;
    }
    
    if (waveformContext) {
        waveformContext.clearRect(0, 0, waveformContext.canvas.width, waveformContext.canvas.height);
    }
}

// ============================================================================
// Backend Message Handling
// ============================================================================

function handleBackendMessage(data) {
    console.log('Backend message:', data);
    
    switch (data.type) {
        case 'state_change':
            setState(data.state);
            break;
        
        case 'listening_started':
            console.log('Voice listening started');
            break;
        
        case 'listening_timeout':
            console.log('Voice listening timed out');
            addMessage('system', 'No speech detected. Please try again.');
            setState('idle');
            break;
        
        case 'user_message':
            // Only show if not already displayed (check against last sent message)
            const lastSent = elements.textInput.dataset.lastSent || '';
            if (data.content !== lastSent) {
                // This was from voice input or a different message
                addMessage('user', data.content, data.timestamp);
            } else {
                // Clear the marker after use
                delete elements.textInput.dataset.lastSent;
            }
            break;
        
        case 'assistant_message':
            hideTypingIndicator();
            addMessage('assistant', data.content, data.timestamp);
            break;
        
        case 'audio_level':
            // Update waveform based on audio level
            updateWaveformLevel(data.level);
            break;
        
        case 'live_voice_started':
            console.log('Live Voice session started');
            setState('listening');
            break;
        
        case 'live_voice_stopped':
            console.log('Live Voice session stopped');
            setState('idle');
            AppState.isLiveMode = false;
            elements.liveVoiceBtn.classList.remove('active');
            elements.voiceBtn.disabled = false;
            elements.voiceBtn.style.opacity = '1';
            elements.textInput.placeholder = 'Type or use voice...';
            break;
        
        case 'live_voice_error':
            console.error('Live Voice error:', data.message);
            addMessage('system', `Live Voice error: ${data.message}`);
            setState('error');
            AppState.isLiveMode = false;
            elements.liveVoiceBtn.classList.remove('active');
            elements.voiceBtn.disabled = false;
            elements.voiceBtn.style.opacity = '1';
            elements.textInput.placeholder = 'Type or use voice...';
            setTimeout(() => setState('idle'), 2000);
            break;
        
        case 'error':
            hideTypingIndicator();
            addMessage('system', `Error: ${data.message}`);
            setState('error');
            setTimeout(() => setState('idle'), 2000);
            break;
    }
}

function updateWaveformLevel(level) {
    // Could enhance waveform animation based on actual audio level
    // For now, it's animated independently
}

// ============================================================================
// Settings Management
// ============================================================================

function loadSettings() {
    const saved = localStorage.getItem('prism-settings');
    if (saved) {
        AppState.settings = { ...AppState.settings, ...JSON.parse(saved) };
    }
    
    // Apply settings to UI
    elements.themeSelect.value = AppState.settings.theme;
    elements.voiceFeedback.checked = AppState.settings.voiceFeedback;
    elements.transparencySlider.value = AppState.settings.transparency;
    elements.animationSpeed.value = AppState.settings.animationSpeed;
    
    applySettings();
}

function updateSettings() {
    AppState.settings = {
        theme: elements.themeSelect.value,
        voiceFeedback: elements.voiceFeedback.checked,
        transparency: parseInt(elements.transparencySlider.value),
        animationSpeed: elements.animationSpeed.value
    };
    
    localStorage.setItem('prism-settings', JSON.stringify(AppState.settings));
    applySettings();
}

function applySettings() {
    const { theme, transparency, animationSpeed } = AppState.settings;
    
    // Apply theme (could add light theme styles)
    document.body.setAttribute('data-theme', theme);
    
    // Apply transparency
    document.documentElement.style.setProperty('--glass-bg-alpha', transparency / 100);
    
    // Apply animation speed
    const speeds = { slow: '0.7s', normal: '0.3s', fast: '0.15s' };
    document.documentElement.style.setProperty('--transition-normal', speeds[animationSpeed]);
}

// ============================================================================
// Initialize on load
// ============================================================================

document.addEventListener('DOMContentLoaded', initialize);
