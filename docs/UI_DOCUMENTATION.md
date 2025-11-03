# PRISM UI Documentation

## Overview

PRISM features a premium glassmorphic UI built with Electron, combining modern design aesthetics with functional voice assistant capabilities. The interface is designed to be always accessible yet unobtrusive, with smooth animations and real-time visual feedback.

## Technology Stack

- **Framework**: Electron 28+
- **Languages**: HTML5, CSS3, Vanilla JavaScript
- **Design**: Glassmorphism (frosted glass effects)
- **Communication**: WebSocket (port 9876)
- **Icons**: SVG inline icons
- **Fonts**: System fonts

## UI Architecture

### Main Process (`main.js`)

**Responsibilities**:
- Window lifecycle management
- System tray integration
- Global hotkey registration
- WebSocket server hosting
- Backend process spawning
- IPC message routing

**Window Configuration**:
```javascript
{
    width: 380,
    height: 480,
    frame: false,           // Frameless window
    transparent: true,      // Transparent background
    resizable: false,       // Fixed size
    alwaysOnTop: true,     // Always visible
    skipTaskbar: false,    // Show in taskbar
    webPreferences: {
        nodeIntegration: true,
        contextIsolation: false
    }
}
```

### Renderer Process (`renderer.js`)

**Responsibilities**:
- UI state management
- User interaction handling
- Backend message processing
- Animation control
- Settings management
- Local storage

## UI Components

### 1. Central Orb

**Purpose**: Main visual indicator and interaction point

**States**:
- **Idle** (Blue): Waiting for activation
- **Listening** (Green): Capturing voice input
- **Processing** (Orange): Analyzing request
- **Responding** (Purple): Delivering response
- **Executing** (Yellow): Performing actions
- **Error** (Red): Error occurred
- **Shutdown** (Fade): System shutting down

**Structure**:
```html
<div class="orb" id="prismOrb">
    <div class="orb-inner">
        <div class="orb-pulse"></div>
        <div class="orb-core">
            <div id="matrixDisplay" class="matrix-display"></div>
        </div>
    </div>
</div>
```

**Animations**:
- Pulse effect (breathing animation)
- Color transitions based on state
- Matrix visualization (digital rain)
- Scale on hover
- Glow effects

### 2. Matrix Visualization

**Purpose**: Animated digital rain effect inside orb

**Implementation**: Custom JavaScript animation system

**Presets**:
- **Startup**: Boot sequence animation
- **Idle**: Slow breathing pattern
- **Listening**: Active pulse pattern
- **Processing**: Fast scanning pattern
- **Responding**: Wave pattern
- **Executing**: Loading bar pattern
- **Error**: Alert pattern
- **Shutdown**: Fade out pattern

**Configuration**:
```javascript
{
    rows: 7,
    cols: 7,
    size: 12,
    gap: 3,
    palette: {
        on: 'rgba(138, 180, 248, 1)',
        off: 'rgba(138, 180, 248, 0.08)'
    },
    fps: 30,
    loop: true
}
```

### 3. State Indicator

**Purpose**: Text display of current state

**Location**: Below central orb

**States**:
- "Idle"
- "Listening"
- "Processing"
- "Responding"
- "Executing"
- "Error"

**Styling**: Glassmorphic badge with state-based colors

### 4. Conversation Panel

**Purpose**: Display conversation history

**Features**:
- Scrollable message list
- User/assistant message bubbles
- Timestamps (relative and absolute)
- Markdown formatting support
- Auto-scroll to latest message
- Clear conversation button

**Message Types**:
```javascript
// User message
<div class="message user-message">
    <div class="message-content">User text</div>
    <div class="message-time">Just now</div>
</div>

// Assistant message
<div class="message assistant-message">
    <div class="message-content">Assistant text</div>
    <div class="message-time">2m ago</div>
</div>

// System message
<div class="message system-message">
    <div class="message-content">System notification</div>
    <div class="message-time">Just now</div>
</div>
```

### 5. Input Area

**Components**:
- Voice button (push-to-talk)
- Live Voice button (continuous mode)
- Text input field
- Send button

**Voice Button**:
```html
<button class="voice-btn" id="voiceBtn" title="Activate Voice">
    <svg><!-- Microphone icon --></svg>
</button>
```

**Live Voice Button**:
```html
<button class="live-voice-btn" id="liveVoiceBtn" title="Toggle Live Voice Mode">
    <svg><!-- Radio icon --></svg>
</button>
```

**Text Input**:
```html
<input type="text" class="text-input" id="textInput" 
       placeholder="Type or use voice..." autocomplete="off" />
```

### 6. Header Bar

**Components**:
- Logo (◇ PRISM)
- Settings button
- Minimize button
- Close button

**Controls**:
```html
<div class="controls">
    <button class="control-btn" id="settingsBtn">⚙️</button>
    <button class="control-btn" id="minimizeBtn">−</button>
    <button class="control-btn close" id="closeBtn">×</button>
</div>
```

### 7. Settings Panel

**Purpose**: Configure PRISM preferences

**Settings**:
- **Theme**: Dark, Light, Auto
- **Voice Feedback**: Enable/disable TTS
- **Transparency**: 0-100% slider
- **Animation Speed**: Slow, Normal, Fast

**Storage**: LocalStorage for persistence

**Structure**:
```html
<div class="settings-panel hidden" id="settingsPanel">
    <div class="settings-header">
        <h3>Settings</h3>
        <button class="close-settings">×</button>
    </div>
    <div class="settings-content">
        <!-- Setting groups -->
    </div>
</div>
```

## Glassmorphic Design

### Core Principles

1. **Frosted Glass Effect**: Semi-transparent backgrounds with blur
2. **Layering**: Multiple glass layers for depth
3. **Subtle Borders**: Light borders for definition
4. **Smooth Transitions**: All state changes animated
5. **Color Coding**: States indicated by colors

### CSS Variables

```css
:root {
    /* Glass effect */
    --glass-bg: rgba(20, 20, 30, 0.85);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    
    /* Colors */
    --accent-primary: #667eea;
    --accent-secondary: #764ba2;
    --text-primary: rgba(255, 255, 255, 0.9);
    --text-secondary: rgba(255, 255, 255, 0.6);
    
    /* State colors */
    --state-idle: #667eea;
    --state-listening: #48bb78;
    --state-processing: #ed8936;
    --state-responding: #9f7aea;
    --state-executing: #ecc94b;
    --state-error: #f56565;
    
    /* Transitions */
    --transition-fast: 0.15s;
    --transition-normal: 0.3s;
    --transition-slow: 0.7s;
}
```

### Glass Effect Implementation

```css
.glass-panel {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    box-shadow: var(--glass-shadow);
}
```

### State-Based Styling

```css
/* Idle state */
.orb.idle {
    background: radial-gradient(circle, var(--state-idle), transparent);
    box-shadow: 0 0 40px var(--state-idle);
}

/* Listening state */
.orb.listening {
    background: radial-gradient(circle, var(--state-listening), transparent);
    box-shadow: 0 0 60px var(--state-listening);
    animation: pulse 1.5s ease-in-out infinite;
}

/* Processing state */
.orb.processing {
    background: radial-gradient(circle, var(--state-processing), transparent);
    box-shadow: 0 0 50px var(--state-processing);
    animation: rotate 2s linear infinite;
}
```

## Animations

### Orb Pulse Animation

```css
@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.05);
        opacity: 0.8;
    }
}
```

### Orb Rotation Animation

```css
@keyframes rotate {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
```

### Fade In Animation

```css
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Typing Indicator

```css
.typing-dot {
    width: 8px;
    height: 8px;
    background: var(--accent-primary);
    border-radius: 50%;
    animation: typing 1.4s infinite;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.5;
    }
    30% {
        transform: translateY(-10px);
        opacity: 1;
    }
}
```

## State Management

### AppState Object

```javascript
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
```

### State Transitions

```javascript
function setState(newState) {
    const oldState = AppState.currentState;
    AppState.currentState = newState;
    
    // Update orb class
    elements.orb.className = 'orb ' + newState;
    
    // Update indicator text
    stateText.textContent = newState.charAt(0).toUpperCase() + newState.slice(1);
    
    // Update Matrix display
    setMatrixState(newState);
    
    // Handle state-specific actions
    switch (newState) {
        case 'listening':
            startWaveformAnimation();
            break;
        case 'processing':
            showTypingIndicator();
            break;
        case 'idle':
            hideTypingIndicator();
            break;
    }
}
```

## Event Handling

### User Interactions

```javascript
// Orb click
elements.orb.addEventListener('click', activateVoice);

// Voice button
elements.voiceBtn.addEventListener('click', activateVoice);

// Live Voice button
elements.liveVoiceBtn.addEventListener('click', toggleLiveVoice);

// Text input
elements.textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendTextMessage();
});

// Send button
elements.sendBtn.addEventListener('click', sendTextMessage);
```

### Backend Messages

```javascript
ipcRenderer.on('backend-message', (event, data) => {
    handleBackendMessage(data);
});

function handleBackendMessage(data) {
    switch (data.type) {
        case 'state_change':
            setState(data.state);
            break;
        case 'user_message':
            addMessage('user', data.content);
            break;
        case 'assistant_message':
            addMessage('assistant', data.content);
            break;
        case 'error':
            showError(data.message);
            break;
    }
}
```

## WebSocket Communication

### Message Format

```javascript
// From UI to Backend
{
    type: 'activate_voice' | 'process_text' | 'clear_conversation' | 'toggle_live_voice',
    text?: string,
    enabled?: boolean
}

// From Backend to UI
{
    type: 'state_change' | 'user_message' | 'assistant_message' | 'audio_level' | 'error',
    state?: string,
    content?: string,
    timestamp?: string,
    level?: number,
    message?: string
}
```

### Sending Messages

```javascript
function sendToBackend(message) {
    ipcRenderer.send('send-to-backend', message);
}

// Examples
sendToBackend({ type: 'activate_voice' });
sendToBackend({ type: 'process_text', text: 'Hello' });
sendToBackend({ type: 'toggle_live_voice', enabled: true });
```

## System Tray Integration

### Tray Menu

```javascript
const contextMenu = Menu.buildFromTemplate([
    {
        label: 'Show PRISM',
        click: () => mainWindow.show()
    },
    {
        label: 'Activate Voice',
        click: () => sendToBackend({ type: 'activate_voice' })
    },
    { type: 'separator' },
    {
        label: 'Settings',
        click: () => openSettings()
    },
    {
        label: 'Clear Conversation',
        click: () => sendToBackend({ type: 'clear_conversation' })
    },
    { type: 'separator' },
    {
        label: 'Quit PRISM',
        click: () => app.quit()
    }
]);
```

### Tray Icon States

```javascript
function updateTrayIcon(state) {
    let tooltip = 'PRISM';
    
    switch (state) {
        case 'listening':
            tooltip = 'PRISM - Listening...';
            break;
        case 'processing':
            tooltip = 'PRISM - Processing...';
            break;
        case 'error':
            tooltip = 'PRISM - Error';
            break;
    }
    
    tray.setToolTip(tooltip);
}
```

## Global Hotkeys

### Registered Shortcuts

```javascript
// Activation shortcut (Ctrl+Space)
globalShortcut.register('CommandOrControl+Space', () => {
    sendToBackend({ type: 'activate_voice' });
    mainWindow.show();
});

// Toggle visibility (Ctrl+Shift+P)
globalShortcut.register('CommandOrControl+Shift+P', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
});
```

## Settings Management

### Loading Settings

```javascript
function loadSettings() {
    const saved = localStorage.getItem('prism-settings');
    if (saved) {
        AppState.settings = { ...AppState.settings, ...JSON.parse(saved) };
    }
    applySettings();
}
```

### Applying Settings

```javascript
function applySettings() {
    const { theme, transparency, animationSpeed } = AppState.settings;
    
    // Apply theme
    document.body.setAttribute('data-theme', theme);
    
    // Apply transparency
    document.documentElement.style.setProperty('--glass-bg-alpha', transparency / 100);
    
    // Apply animation speed
    const speeds = { slow: '0.7s', normal: '0.3s', fast: '0.15s' };
    document.documentElement.style.setProperty('--transition-normal', speeds[animationSpeed]);
}
```

### Saving Settings

```javascript
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
```

## Responsive Design

### Window Positioning

```javascript
// Position at bottom-right corner
const { screen } = require('electron');
const primaryDisplay = screen.getPrimaryDisplay();
const { width, height } = primaryDisplay.workAreaSize;

mainWindow.setPosition(
    width - 400,   // 20px from right edge
    height - 500   // 20px from bottom edge
);
```

### Adaptive Sizing

```css
/* Conversation panel adapts to content */
.conversation-panel {
    max-height: 200px;
    overflow-y: auto;
}

/* Input area always at bottom */
.input-area {
    position: sticky;
    bottom: 0;
}
```

## Performance Optimization

### Debouncing

```javascript
// Debounce text input
let inputTimeout;
elements.textInput.addEventListener('input', () => {
    clearTimeout(inputTimeout);
    inputTimeout = setTimeout(() => {
        // Process input
    }, 300);
});
```

### Virtual Scrolling

```javascript
// Limit displayed messages
const MAX_DISPLAYED_MESSAGES = 50;
if (messagesContainer.children.length > MAX_DISPLAYED_MESSAGES) {
    messagesContainer.removeChild(messagesContainer.firstChild);
}
```

### Animation Frame Optimization

```javascript
let animationFrameId;

function startAnimation() {
    function animate() {
        // Animation logic
        animationFrameId = requestAnimationFrame(animate);
    }
    animate();
}

function stopAnimation() {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
}
```

## Accessibility

### ARIA Labels

```html
<button aria-label="Activate voice input" id="voiceBtn">
    <svg aria-hidden="true">...</svg>
</button>

<div role="log" aria-live="polite" id="messagesContainer">
    <!-- Messages -->
</div>
```

### Keyboard Navigation

```javascript
// Tab navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        // Handle tab navigation
    }
    if (e.key === 'Escape') {
        // Close panels
        elements.settingsPanel.classList.add('hidden');
    }
});
```

## Best Practices

### 1. State Management
- Single source of truth (AppState)
- Immutable state updates
- Clear state transitions

### 2. Event Handling
- Event delegation for dynamic elements
- Cleanup event listeners on destroy
- Debounce expensive operations

### 3. Performance
- Use CSS transforms for animations
- Minimize DOM manipulations
- Virtual scrolling for long lists
- RequestAnimationFrame for smooth animations

### 4. Accessibility
- ARIA labels for all interactive elements
- Keyboard navigation support
- Focus management
- Screen reader friendly

### 5. Error Handling
- Graceful degradation
- User-friendly error messages
- Automatic error recovery
- Fallback UI states
