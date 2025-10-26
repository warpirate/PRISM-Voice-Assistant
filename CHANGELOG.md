# Changelog

All notable changes to PRISM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-10-26

### 🎉 Initial Release

This is the first complete release of PRISM - Personal Response Interface for System Management.

### ✨ Added

#### Core System
- Central coordination hub managing all subsystems
- Async architecture for responsive operations
- WebSocket bridge for real-time UI-backend communication
- Comprehensive error handling and logging
- Graceful startup and shutdown procedures

#### Voice Interaction
- Wake word detection using Porcupine
- Speech-to-text with Google Speech Recognition
- Text-to-speech with configurable voices
- Real-time audio level monitoring
- Waveform visualization during voice capture
- Multiple activation methods (voice, click, hotkey)

#### AI Integration
- OpenAI GPT integration
- Anthropic Claude integration
- Context-aware conversation management
- Action extraction from natural language
- Fallback rule-based processing for offline operation
- Configurable temperature and token limits

#### System Control
- Application launching and management
- File system operations (create, search, open)
- Web search integration
- Safe command execution with security blocklists
- System information retrieval
- Cross-application window management

#### Memory & Learning
- SQLite database for persistent storage
- Conversation history with timestamps
- Pattern recognition for common actions
- User preference management
- Configurable data retention policies
- Data export functionality
- Automatic cleanup of old data

#### User Interface
- Glassmorphic design with frosted glass effects
- Central orb with state-based animations
  - Idle (blue pulsing)
  - Listening (green expanding)
  - Processing (orange rotating)
  - Responding (purple morphing)
  - Error (red shaking)
- Real-time waveform visualization
- Conversation history panel
- Text and voice input modes
- Settings panel with live configuration
- System tray integration
- Global keyboard shortcuts
- Minimize to tray functionality

#### Configuration
- Environment-based configuration (.env)
- Pydantic models for type safety
- Hot-reloadable settings
- Multiple theme support
- Customizable keyboard shortcuts
- Privacy controls
- Voice settings (rate, volume, language)
- UI customization (transparency, animations)

#### Developer Experience
- Comprehensive documentation (README, guides)
- Setup automation scripts
- Clear project structure
- Type hints throughout
- Detailed logging
- Error messages with context

### 📚 Documentation
- README.md - Complete project documentation
- SETUP_GUIDE.md - Step-by-step installation guide
- QUICK_START.md - 5-minute getting started guide
- PROJECT_SUMMARY.md - Technical overview
- CHANGELOG.md - Version history

### 🛠️ Tools & Scripts
- setup.bat - Automated setup script
- start.bat - Quick launch script
- .env.example - Configuration template
- .gitignore - Git ignore rules

### 🔧 Technical Details

**Backend Dependencies:**
- Python 3.8+
- pvporcupine 3.0.2
- SpeechRecognition 3.10.1
- pyttsx3 2.90
- openai 1.12.0
- anthropic 0.18.1
- websockets 12.0
- loguru 0.7.2
- pydantic 2.6.1
- And more...

**Frontend Dependencies:**
- Electron 28.2.0
- Node.js 16+
- WebSocket (ws) 8.16.0

### 🎯 Supported Platforms
- Windows 10/11 (primary)
- Future: macOS, Linux

### Known Limitations
- Wake word detection requires Porcupine access key
- PyAudio installation can be tricky on Windows
- AI features require API keys
- Voice recognition requires internet connection
- English language only (for now)

---

## [Unreleased]

### Changed
- **BREAKING**: Migrated from OpenAI/Anthropic to Google Gemini API
  - Updated AI engine to use `google-generativeai` SDK
  - Changed configuration to use `GEMINI_API_KEY`
  - Updated all documentation with Gemini setup instructions
  - Simplified AI provider configuration

### Updated (October 2025)
- **Updated to latest Gemini models**
  - Default model: `gemini-2.5-flash` (October 2025)
  - Added support for `gemini-2.0-flash` and `gemini-2.0-flash-lite`
  - Increased max_tokens to 2048 for better responses
  - Added `GEMINI_MODEL` environment variable for easy model switching
  - Updated rate limits documentation (250 RPD for 2.5 Flash)
  - Created comprehensive model comparison guide (GEMINI_MODELS_2025.md)

### Migration Guide
If upgrading from a previous version:
1. Get Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update `.env`:
   - Remove: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
   - Add: `GEMINI_API_KEY=your-key-here`
   - Change: `AI_PROVIDER=gemini`
3. Reinstall dependencies: `pip install -r requirements.txt`

### Planned for Future Releases

#### v1.1.0 - Enhanced Voice
- Custom wake word training
- Multiple wake word support
- Improved noise cancellation
- Voice activity detection
- Offline speech recognition

#### v1.2.0 - Multi-Platform
- macOS support
- Linux support
- Platform-specific optimizations
- Universal binary builds

#### v1.3.0 - AI Expansion
- Local AI model support (LLaMA, Mistral)
- Streaming responses
- Function calling
- Memory improvements
- Context window expansion

#### v1.4.0 - Integrations
- Calendar integration
- Email management
- Smart home control
- Cloud storage access
- Third-party app plugins

#### v2.0.0 - Major Overhaul
- Plugin architecture
- Mobile companion app
- Multi-language support
- Voice cloning
- Advanced automation
- Team collaboration features

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2024-10-26 | Initial release with core features |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style
- Testing requirements

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/prism/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/prism/discussions)
- **Email**: support@prism.ai

---

<div align="center">

**Thank you for using PRISM!** 🎉

Star us on GitHub if you find it useful!

</div>
