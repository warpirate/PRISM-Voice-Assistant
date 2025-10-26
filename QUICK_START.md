# PRISM Quick Start Guide

Get PRISM running in under 5 minutes!

---

## ⚡ Quick Installation

```bash
# 1. Run setup
setup.bat

# 2. Configure API key
# Edit .env and add:
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-2.5-flash  # Recommended (Oct 2025)
# Get key from: https://makersuite.google.com/app/apikey

# 3. Start PRISM
start.bat
```

---

## 🎯 First Commands to Try

### System Control
- "Open Chrome"
- "Open Notepad"
- "Open Calculator"
- "Launch VS Code"

### File Operations
- "Create a file called todo.txt"
- "Search for Python files"
- "Open my Documents folder"

### Information Queries
- "What's the weather like?"
- "Search for AI tutorials"
- "Tell me about machine learning"
- "What time is it?"

### Conversation
- "Hello, how are you?"
- "What can you do?"
- "Tell me a joke"
- "Help me with Python"

---

## 🎮 Controls

### Activation
- **Voice**: Say "Prism" (if wake word enabled)
- **Click**: Click the central orb
- **Keyboard**: Press `Ctrl+Space`

### Window
- **Minimize**: Click `-` button or `Ctrl+Shift+P`
- **Close**: Click `×` button
- **Settings**: Click gear icon

### Input Methods
- **Voice**: Click microphone button or activate with wake word
- **Text**: Type in input box and press Enter
- **Mixed**: Use both interchangeably

---

## 🎨 UI States

The central orb changes color based on state:

| Color | State | Meaning |
|-------|-------|---------|
| 🔵 Blue | Idle | Ready for input |
| 🟢 Green | Listening | Recording voice |
| 🟠 Orange | Processing | Thinking... |
| 🟣 Purple | Responding | Speaking/showing response |
| 🔴 Red | Error | Something went wrong |

---

## ⌨️ Keyboard Shortcuts

- `Ctrl+Space` - Activate voice
- `Ctrl+Shift+P` - Toggle window
- `Enter` - Send text message
- `Esc` - Close settings panel

---

## 📍 System Tray

Right-click the PRISM icon in system tray for:
- Show/Hide window
- Activate voice
- Clear conversation
- Settings
- Quit

---

## 🔧 Common Issues

### Voice Not Working
→ Click orb or use Ctrl+Space instead

### No Response
→ Check `.env` has valid API key

### Backend Not Starting
→ Check `data/logs/` for errors

### UI Won't Connect
→ Restart both backend and UI

---

## 📚 Learn More

- **Full Docs**: See README.md
- **Setup Help**: See SETUP_GUIDE.md
- **Model Guide**: See GEMINI_MODELS_2025.md
- **Examples**: Try the commands above!

---

## 💡 Pro Tips

1. **Keep Backend Running**: The Python console shows helpful logs
2. **Check Logs**: `data/logs/` has detailed error information
3. **Start Small**: Test with simple commands first
4. **Use Text Mode**: More reliable than voice during testing
5. **Read Responses**: PRISM explains what it's doing

---

<div align="center">

**Ready to go?** Run `start.bat` and say hello to PRISM! 🚀

</div>
