# PRISM - Personal Response Interface for System Management

<div align="center">

![PRISM Logo](ui/assets/icon.png)

**An elegant, voice-activated AI assistant with a premium glassmorphic interface**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node-16+-green.svg)](https://nodejs.org/)
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4)](https://ai.google.dev/)

</div>

> 🎉 **Now powered by Google Gemini!** - Faster responses, free tier, and multimodal-ready. [Learn more](GEMINI_MIGRATION.md)

---

## ✨ Features

### 🎤 Voice Interaction
- **Wake Word Detection**: Always-listening for "Prism" activation phrase
- **Speech Recognition**: High-accuracy voice-to-text conversion
- **Natural Voice Synthesis**: Smooth, natural-sounding responses
- **Audio Visualization**: Real-time waveform display during voice interaction

### 🤖 AI Intelligence
- **Natural Language Understanding**: Powered by Google Gemini 2.5 Flash (October 2025)
- **Context-Aware**: Maintains conversation history with 1M token context window
- **Multi-Modal Input**: Voice, text, or keyboard shortcuts
- **Action Processing**: Understands and executes system commands
- **Free Tier**: 250 requests/day with generous rate limits

### 💻 System Control
- **Application Management**: Launch, focus, and manage applications
- **File Operations**: Create, search, and manipulate files
- **Web Search**: Quick access to web information
- **System Commands**: Execute safe system-level operations

### 🎨 Premium UI
- **Glassmorphic Design**: Beautiful frosted glass effects
- **State-Based Animations**: Dynamic visual feedback for different states
- **Responsive Orb**: Central interface element with smooth transitions
- **Always Accessible**: System tray integration and global hotkeys

### 🧠 Memory & Learning
- **Conversation Storage**: Persistent chat history
- **Pattern Recognition**: Learns from user behavior
- **Personalization**: Adapts to user preferences
- **Privacy Controls**: Configurable data retention

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Windows 10/11** (primary platform)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/prism.git
   cd prism
   ```

2. **Run setup script**
   ```bash
   setup.bat
   ```

3. **Configure API key**
   - Copy `.env.example` to `.env`
   - Add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_key_here
     ```
   - Get your free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Start PRISM**
   ```bash
   start.bat
   ```

### First Use

1. **Activation Methods**:
   - Say "Prism" (if wake word detection is working)
   - Click the central orb
   - Press `Ctrl+Space`

2. **Try Commands**:
   - "Open Chrome"
   - "Search for Python tutorials"
   - "Create a file called notes.txt"
   - "What's the weather like?"

---

## 📚 Documentation

### Project Structure

```
PRISM/
├── backend/                 # Python backend
│   ├── main.py             # Entry point
│   ├── coordinator.py      # Central orchestrator
│   ├── voice_pipeline.py   # Voice processing
│   ├── ai_engine.py        # AI integration
│   ├── system_control.py   # System operations
│   ├── memory_system.py    # Data persistence
│   └── config.py           # Configuration
│
├── ui/                      # Electron UI
│   ├── index.html          # Main interface
│   ├── styles.css          # Glassmorphic styles
│   ├── renderer.js         # UI logic
│   ├── main.js             # Electron main process
│   └── assets/             # Icons and images
│
├── data/                    # User data (auto-created)
│   ├── memory.db           # Conversation database
│   ├── logs/               # Application logs
│   └── config.json         # User settings
│
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── package.json            # Node dependencies
├── setup.bat               # Setup script
└── start.bat               # Startup script
```

### System Architecture

#### 1. Central Coordinator
The heart of PRISM that manages all subsystems:
- Routes messages between modules
- Manages application lifecycle
- Handles state transitions
- Coordinates voice, AI, and system control

#### 2. Voice Pipeline
Handles all voice interactions:
- **Wake Word**: Porcupine for "Prism" detection
- **STT**: Google Speech Recognition
- **TTS**: pyttsx3 for voice synthesis
- **Audio Processing**: Real-time audio capture and visualization

#### 3. AI Engine
Powers natural language understanding:
- Supports OpenAI GPT and Anthropic Claude
- Context-aware conversation
- Action extraction from natural language
- Fallback rule-based processing

#### 4. System Control
Executes system operations:
- Application launching and management
- File system operations
- Web searches
- Safe command execution

#### 5. Memory System
Manages data persistence:
- SQLite database for conversations
- Pattern recognition and learning
- User preferences storage
- Automatic data cleanup

#### 6. Glassmorphic UI
Premium Electron interface:
- Frosted glass effects
- State-based animations
- Waveform visualization
- System tray integration

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# AI Provider
AI_PROVIDER=gemini              # gemini, local
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-2.5-flash   # gemini-2.5-flash (recommended), gemini-2.0-flash, gemini-2.0-flash-lite

# Voice Settings
WAKE_WORD=prism
VOICE_LANGUAGE=en-US
TTS_VOICE=default
TTS_RATE=175
TTS_VOLUME=0.9
ENABLE_WAKE_WORD=true
ENABLE_VOICE_FEEDBACK=true

# System
LOG_LEVEL=INFO
MINIMIZE_TO_TRAY=true

# Privacy
STORE_CONVERSATIONS=true
RETENTION_DAYS=30
ENABLE_ANALYTICS=false

# UI
THEME=dark
TRANSPARENCY=0.85
ANIMATION_SPEED=normal

# Shortcuts
ACTIVATION_HOTKEY=ctrl+space
TOGGLE_VISIBILITY_HOTKEY=ctrl+shift+p
```

### Keyboard Shortcuts

- **Ctrl+Space** - Activate voice input
- **Ctrl+Shift+P** - Toggle window visibility
- **Enter** - Send text message
- **Esc** - Close settings panel

---

## 🎨 UI States

PRISM's central orb visually represents the current state:

- **Idle** (Blue) - Waiting for activation
- **Listening** (Green) - Capturing voice input
- **Processing** (Orange) - Analyzing request
- **Responding** (Purple) - Delivering response
- **Error** (Red) - Error occurred

---

## 🔧 Troubleshooting

### PyAudio Installation Issues (Windows)

PyAudio can be tricky on Windows. If installation fails:

1. Download the wheel file for your Python version from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
2. Install manually:
   ```bash
   pip install PyAudio-X.X.X-cpXX-cpXX-win_amd64.whl
   ```

### Wake Word Not Working

Wake word detection requires Porcupine access key:

1. Sign up at [Picovoice Console](https://console.picovoice.ai/)
2. Get your access key
3. Update configuration to use the key
4. Alternatively, use manual activation (click orb or Ctrl+Space)

### UI Not Connecting to Backend

Check that:
- Backend is running (separate window should appear)
- No firewall blocking localhost:9876
- Check backend logs in `data/logs/`

### API Rate Limits

If you hit API rate limits:
- Reduce conversation history length
- Use shorter responses
- Consider fallback rule-based mode

---

## 🛠️ Development

### Running in Development Mode

```bash
# Backend with debug logging
cd backend
python main.py

# UI with DevTools
cd ui
set NODE_ENV=development
npm start
```

### Adding Custom Commands

Edit `backend/ai_engine.py` fallback processing:

```python
async def _process_fallback(self, user_input: str) -> AIResponse:
    user_input_lower = user_input.lower()
    
    # Add your custom command
    if "custom command" in user_input_lower:
        return AIResponse(
            text="Executing custom command...",
            requires_action=True,
            actions=[{
                "type": "custom_action",
                "parameters": {...}
            }]
        )
```

### Extending System Control

Add new actions in `backend/system_control.py`:

```python
async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
    action_type = action.get("type")
    
    if action_type == "your_action":
        return await self.your_custom_function(...)
```

---

## 🔐 Privacy & Security

- **Local-First**: Most processing happens locally
- **Data Control**: Full control over data storage
- **Secure APIs**: Encrypted communication with AI providers
- **No Telemetry**: No usage tracking unless explicitly enabled
- **Data Retention**: Automatic cleanup based on settings

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **Google** - Gemini 2.5 Flash AI model
- **Picovoice** - Porcupine wake word engine
- **Electron** - Cross-platform desktop framework

## 📖 Additional Documentation

- **[GEMINI_MODELS_2025.md](GEMINI_MODELS_2025.md)** - Complete guide to Gemini models and rate limits
- **[GEMINI_MIGRATION.md](GEMINI_MIGRATION.md)** - Migration guide from older versions
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed installation instructions
- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes

---

## 🗺️ Roadmap

- [ ] macOS and Linux support
- [ ] Custom wake word training
- [ ] Plugin system for extensions
- [ ] Local AI model support
- [ ] Mobile companion app
- [ ] Calendar and email integration
- [ ] Smart home control
- [ ] Multi-language support

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/prism/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/prism/discussions)
- **Email**: support@prism.ai

---

<div align="center">

**Made with ❤️ by the PRISM Team**

⭐ Star us on GitHub if you find PRISM useful!

</div>
