# PRISM - Personal Response Interface for System Management

<div align="center">

![PRISM Logo](ui/assets/icon.png)

**A Beautiful, Siri-Like Voice Assistant for Windows**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/Electron-27+-lightblue.svg)](https://www.electronjs.org/)
[![License](https://img.shields.io/badge/License-Private-red.svg)](LICENSE)

*"Hey PRISM, let's get things done!"* 🚀

</div>

---

## 🌟 Overview

PRISM is a stunning voice-activated AI assistant for Windows that combines the elegance of macOS Siri with the power of modern AI. Featuring a beautiful glassmorphic UI, intelligent responses, and seamless system control, PRISM transforms how you interact with your computer.

### ✨ Key Highlights

- 🎨 **Gorgeous UI** - Glassmorphic design with animated floating orb
- 🎤 **Voice Control** - Wake word detection and natural speech recognition
- 🤖 **AI-Powered** - Intelligent responses using Llama 3.1 70B via Nebius
- 💾 **Memory System** - Remembers past interactions for personalized responses
- 🖥️ **System Control** - Launch apps, manage files, execute commands
- 🔒 **Privacy-Focused** - Voice processed locally, minimal cloud usage

---

## 🎬 Demo

### UI States

**Idle State**
- Floating orb with gentle animation
- Ready for activation

**Listening State**
- Pulsing blue-purple gradient
- Animated waveform visualization
- Recording your voice

**Speaking State**
- Green gradient with dynamic animation
- Playing response through speakers

---

## 🚀 Quick Start

### Prerequisites

- Windows 10/11 (64-bit)
- Python 3.10 or higher
- Node.js 18 or higher
- Nebius AI Studio API key

### Installation (3 Steps)

1. **Run Setup**
   ```bash
   setup.bat
   ```

2. **Configure API Key**
   - Edit `.env` file
   - Add your Nebius API key: `NEBIUS_API_KEY=neb-your-key`

3. **Launch PRISM**
   ```bash
   start.bat
   ```

**That's it!** PRISM will open with the beautiful UI ready to use.

📖 **Detailed Instructions:** See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

---

## 💡 Usage

### Activation Methods

1. **Voice** - Say "Computer" to activate
2. **Click** - Click the floating orb
3. **Keyboard** - Press `Ctrl+Shift+P`

### Example Commands

```
🖥️ System Control
"Computer, open Notepad"
"Computer, launch Calculator"
"Computer, open Documents folder"

💬 Conversation
"Computer, tell me a joke"
"Computer, how are you today?"
"Computer, what can you do?"

📚 Information
"Computer, what is Python?"
"Computer, explain machine learning"
"Computer, what's the weather?"
```

---

## 🎨 Features

### Beautiful UI
- **Glassmorphic Design** - Frosted glass effects with blur
- **Animated Orb** - Siri-inspired floating orb with multiple states
- **Smooth Animations** - CSS animations and canvas waveforms
- **Responsive Panel** - Expandable panel showing queries and responses
- **System Tray** - Minimize to tray, always accessible

### Voice Capabilities
- **Wake Word Detection** - Hands-free activation with Porcupine
- **Speech Recognition** - OpenAI Whisper for accurate transcription
- **Text-to-Speech** - Natural voice output with customization
- **Multi-Modal Input** - Voice, click, or keyboard activation

### AI Intelligence
- **Nebius AI Studio** - Powered by Llama 3.1 70B
- **Contextual Responses** - Understands conversation context
- **Personality** - Friendly, helpful, JARVIS-like character
- **Memory-Aware** - References past interactions

### System Control
- **App Launching** - Open any Windows application
- **File Management** - Navigate folders and files
- **Custom Commands** - Easily extensible command system
- **Productivity Routines** - Chain multiple actions

### Memory System
- **Interaction Storage** - SQLite database for history
- **Personalization** - Learns from past conversations
- **Context Awareness** - Remembers recent actions
- **Privacy-Focused** - All data stored locally

---

## 📁 Project Structure

```
PRISM/
├── backend/              # Python backend
│   ├── main.py          # Main coordinator
│   ├── prism_llm.py     # AI integration
│   ├── voice_pipeline.py # Voice handling
│   ├── tts.py           # Text-to-speech
│   ├── system_control.py # System commands
│   └── memory.py        # Memory management
│
├── ui/                  # Electron frontend
│   ├── main.js          # Electron main
│   ├── renderer.js      # UI logic
│   ├── index.html       # Main UI
│   ├── styles.css       # Styling
│   └── assets/          # Icons
│
├── logs/                # Application logs
├── .env                 # API keys (create from .env.example)
├── requirements.txt     # Python dependencies
├── setup.bat           # Setup script
└── start.bat           # Launch script
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Quick start guide and basic usage |
| [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) | Detailed installation instructions |
| [FEATURES.md](FEATURES.md) | Complete feature documentation |
| [UI_PREVIEW.md](UI_PREVIEW.md) | UI design and visual guide |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview and summary |
| [development.md](development.md) | Development plan and phases |
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |

---

## 🛠️ Technology Stack

### Frontend
- **Electron** - Desktop application framework
- **HTML/CSS/JavaScript** - Modern web technologies
- **Canvas API** - Waveform visualizations
- **Animate.css** - Smooth animations

### Backend
- **Python 3.10+** - Core backend language
- **OpenAI Whisper** - Speech recognition
- **Porcupine** - Wake word detection
- **pyttsx3** - Text-to-speech
- **SQLite** - Memory database

### AI/Cloud
- **Nebius AI Studio** - LLM API (Llama 3.1 70B)
- **OpenAI SDK** - API client

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```env
# Required
NEBIUS_API_KEY=neb-your-key-here

# Optional
PORCUPINE_ACCESS_KEY=your-key-here
SERPAPI_KEY=your-key-here
```

### Customization

- **Voice:** Change TTS voice in `backend/tts.py`
- **Commands:** Add commands in `backend/system_control.py`
- **UI Colors:** Edit `ui/styles.css`
- **Personality:** Adjust prompts in `backend/prism_llm.py`

---

## 🔒 Privacy & Security

- ✅ Voice processing done **locally** (Whisper)
- ✅ Only **text** sent to cloud (Nebius)
- ✅ No telemetry or tracking
- ✅ API keys stored securely in `.env`
- ✅ Memory stored **locally** in SQLite

---

## 🐛 Troubleshooting

### Common Issues

**Microphone not working?**
- Check Windows microphone permissions
- Ensure no other app is using the microphone

**API errors?**
- Verify `NEBIUS_API_KEY` in `.env`
- Check internet connection

**Module not found?**
- Run `setup.bat` again
- Check `logs/prism.log` for details

📖 **Full Troubleshooting:** See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md#troubleshooting)

---

## 🚧 Roadmap

### Coming Soon
- [ ] Web search integration (SerpAPI)
- [ ] Calendar/email integration (Microsoft Graph)
- [ ] Custom productivity routines
- [ ] Voice customization (Coqui TTS)
- [ ] Multi-language support
- [ ] Plugin system
- [ ] Mobile companion app

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Fork and customize for your needs
- Report issues in your fork
- Share improvements

---

## 📄 License

Private use only. Not for distribution.

---

## 🙏 Acknowledgments

- **Nebius AI Studio** - LLM API
- **OpenAI Whisper** - Speech recognition
- **Picovoice Porcupine** - Wake word detection
- **Electron** - Desktop framework
- **Python Community** - Amazing libraries

---

## 📞 Support

- 📖 Check [QUICKSTART.md](QUICKSTART.md) for basic help
- 🔍 Review [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for setup issues
- 📝 Check `logs/prism.log` for error details
- 🧪 Run `python test_setup.py` to verify installation

---

<div align="center">

**Built with ❤️ for personal productivity**

*Transform your Windows experience with PRISM* ✨

[Get Started](QUICKSTART.md) • [Documentation](FEATURES.md) • [Installation](INSTALLATION_GUIDE.md)

</div>
