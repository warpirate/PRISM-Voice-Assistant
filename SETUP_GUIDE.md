# PRISM Setup Guide

Complete step-by-step guide to get PRISM running on your system.

---

## 📋 Prerequisites

### Required Software

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Node.js 16 or higher**
   - Download from [nodejs.org](https://nodejs.org/)
   - Includes npm (Node Package Manager)
   - Verify: `node --version` and `npm --version`

3. **Git** (optional, for cloning)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

### Windows-Specific Requirements

- **Visual C++ Build Tools** (for some Python packages)
  - Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
  - Select "Desktop development with C++" workload
  - This is needed for PyAudio and some other native extensions

---

## 🚀 Installation Steps

### Step 1: Get the Code

**Option A: Clone with Git**
```bash
git clone https://github.com/yourusername/prism.git
cd prism
```

**Option B: Download ZIP**
- Download and extract the ZIP file
- Navigate to the extracted folder

### Step 2: Run Setup Script

Open Command Prompt in the PRISM directory and run:

```bash
setup.bat
```

This script will:
- ✅ Check for Python and Node.js
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Install Node.js dependencies
- ✅ Create data directories
- ✅ Generate `.env` configuration file

**Expected Duration:** 3-5 minutes

### Step 3: Configure API Key

- Copy `.env.example` to `.env`
- Add your Gemini API key:

**Get Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

**Add to `.env`:**
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-actual-gemini-key-here
GEMINI_MODEL=gemini-2.5-flash  # Recommended (October 2025)
```

**Model Options:**
- `gemini-2.5-flash` - Best quality (recommended)
- `gemini-2.0-flash` - Multimodal ready
- `gemini-2.0-flash-lite` - Highest free limits (1000/day)

See [GEMINI_MODELS_2025.md](GEMINI_MODELS_2025.md) for detailed comparison.

### Step 4: (Optional) Configure Wake Word

For wake word detection, you need a Porcupine access key:

1. Sign up at [Picovoice Console](https://console.picovoice.ai/)
2. Create a new project
3. Copy your access key
4. Add to `.env`:
```env
PORCUPINE_ACCESS_KEY=your-access-key-here
```

**Note:** If you skip this, you can still use manual activation (clicking orb or Ctrl+Space).

### Step 5: Start PRISM

Run the startup script:

```bash
start.bat
```

Two windows will open:
- **PRISM Backend** - Python console (shows logs)
- **PRISM UI** - Electron window (glassmorphic interface)

---

## 🔧 Troubleshooting

### Issue: PyAudio Installation Fails

**Symptoms:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solution:**

1. **Download Pre-compiled Wheel**
   - Visit [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   - Download the wheel matching your Python version:
     - Python 3.8: `PyAudio‑0.2.11‑cp38‑cp38‑win_amd64.whl`
     - Python 3.9: `PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl`
     - Python 3.10: `PyAudio‑0.2.11‑cp310‑cp310‑win_amd64.whl`
     - Python 3.11: `PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl`

2. **Install Manually**
   ```bash
   venv\Scripts\activate
   pip install path\to\downloaded\PyAudio-xxx.whl
   ```

### Issue: Backend Won't Start

**Symptoms:**
- Backend window closes immediately
- Import errors

**Solutions:**

1. **Check Python Version**
   ```bash
   python --version
   ```
   Must be 3.8 or higher

2. **Reinstall Dependencies**
   ```bash
   venv\Scripts\activate
   pip install --upgrade -r requirements.txt
   ```

3. **Check Logs**
   Look in `data/logs/` for error details

### Issue: UI Won't Connect to Backend

**Symptoms:**
- UI loads but shows "Connecting..."
- No response to interactions

**Solutions:**

1. **Check Firewall**
   - Ensure Windows Firewall allows `python.exe` and `node.exe`
   - Check for antivirus blocking

2. **Check Port Availability**
   ```bash
   netstat -ano | findstr :9876
   ```
   Port 9876 should be free or used by PRISM

3. **Restart Both Components**
   - Close both backend and UI windows
   - Run `start.bat` again

### Issue: Wake Word Not Detected

**Symptoms:**
- No response when saying "Prism"
- Manual activation works fine

**Solutions:**

1. **Check Microphone Permissions**
   - Windows Settings → Privacy → Microphone
   - Enable for desktop apps

2. **Test Microphone**
   - Open Sound Settings
   - Test your microphone input
   - Adjust sensitivity if needed

3. **Use Alternative Activation**
   - Click the orb
   - Press Ctrl+Space
   - Type your command

4. **Check Porcupine Key**
   - Verify `PORCUPINE_ACCESS_KEY` in `.env`
   - Try generating a new key

### Issue: High CPU Usage

**Solutions:**

1. **Disable Wake Word Detection**
   ```env
   ENABLE_WAKE_WORD=false
   ```

2. **Adjust Animation Speed**
   - Open Settings in UI
   - Set animation speed to "slow"

3. **Close Unnecessary Applications**

### Issue: API Rate Limits

**Symptoms:**
- "Rate limit exceeded" errors
- Slow responses

**Solutions:**

1. **Wait and Retry**
   - Most APIs reset limits after a few minutes

2. **Upgrade API Plan**
   - Check your OpenAI/Anthropic usage dashboard

3. **Use Fallback Mode**
   - Set `AI_PROVIDER=fallback` in `.env`
   - Limited functionality but works offline

---

## 🎯 Verification Steps

After installation, verify everything works:

### 1. Check Backend
- Backend console should show:
  ```
  ✓ PRISM system started successfully
  ✓ WebSocket bridge listening on ws://localhost:9876
  ```

### 2. Check UI
- UI window should appear with animated orb
- State indicator should show "Idle"

### 3. Test Text Input
1. Click in the text input box
2. Type "hello"
3. Press Enter or click send
4. You should see response within seconds

### 4. Test Voice Activation
1. Click the central orb
2. Speak clearly into microphone
3. Watch for state changes (Listening → Processing → Responding)

### 5. Test System Commands
Try these commands:
- "Open notepad"
- "Search for Python tutorials"
- "What time is it?"

---

## 🔄 Updating PRISM

To update to the latest version:

1. **Backup Your Data**
   ```bash
   copy .env .env.backup
   xcopy data data_backup /E /I
   ```

2. **Get Latest Code**
   ```bash
   git pull origin main
   ```
   Or download and extract new ZIP

3. **Update Dependencies**
   ```bash
   setup.bat
   ```

4. **Restore Configuration**
   - Keep your `.env` file
   - Merge any new settings from `.env.example`

---

## 📁 Important File Locations

- **Configuration:** `.env`
- **Logs:** `data/logs/prism_YYYY-MM-DD.log`
- **Database:** `data/memory.db`
- **Settings:** `data/config.json`

---

## 🆘 Getting Help

If you're still having issues:

1. **Check Logs**
   - Backend logs: `data/logs/`
   - Look for ERROR or WARNING messages

2. **Search Issues**
   - [GitHub Issues](https://github.com/yourusername/prism/issues)

3. **Ask for Help**
   - Create a new issue with:
     - Your Python version
     - Your Node.js version
     - Error messages from logs
     - Steps to reproduce

4. **Community Support**
   - [GitHub Discussions](https://github.com/yourusername/prism/discussions)

---

## ✅ Next Steps

Once PRISM is running:

1. **Customize Settings**
   - Click settings icon in UI
   - Adjust theme, transparency, etc.

2. **Explore Commands**
   - Try different types of requests
   - Open applications
   - Search for information
   - Manage files

3. **Set Up Shortcuts**
   - Learn keyboard shortcuts
   - Customize in `.env` if needed

4. **Review Privacy Settings**
   - Configure data retention
   - Enable/disable conversation storage

---

## 🎓 Learning Resources

- **README.md** - Full documentation
- **ARCHITECTURE.md** - System architecture
- **CONTRIBUTING.md** - Development guide
- **examples/** - Example use cases

---

<div align="center">

**Need more help?** Open an issue or start a discussion on GitHub!

</div>
