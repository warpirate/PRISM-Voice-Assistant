# PRISM Troubleshooting Guide

Common issues and their solutions.

---

## 🔧 Quick Fixes

### Issue: "Electron failed to install correctly"

**Error:**
```
Error: Electron failed to install correctly, please delete node_modules/electron and try installing again
```

**Solution:**
```bash
# Run the fix script
.\fix.bat

# OR manually:
rmdir /s /q node_modules\electron
npm install electron@^28.2.0
```

---

### Issue: "ModuleNotFoundError: No module named 'numpy'"

**Error:**
```
ModuleNotFoundError: No module named 'numpy'
```

**Solution:**
```bash
# Activate virtual environment
venv\Scripts\activate

# Install numpy
pip install numpy==1.26.4

# OR run fix script
.\fix.bat
```

---

### Issue: "ModuleNotFoundError: No module named 'distutils'" (Python 3.12+)

**Error:**
```
ModuleNotFoundError: No module named 'distutils'
from distutils.version import LooseVersion
```

**Cause:**
- Python 3.12 removed the `distutils` module
- Some packages (like SpeechRecognition) still depend on it

**Solution:**
```bash
# Run Python 3.12 fix script
.\fix-python312.bat

# OR manually:
venv\Scripts\activate
pip install setuptools==69.0.0
pip install --upgrade SpeechRecognition==3.10.4
pip install --upgrade -r requirements.txt
```

---

### Issue: "PyAudio installation failed"

**Error:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solution:**

**Option 1: Download Pre-compiled Wheel**
1. Visit [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
2. Download for your Python version (e.g., `PyAudio‑0.2.14‑cp312‑cp312‑win_amd64.whl` for Python 3.12)
3. Install:
   ```bash
   venv\Scripts\activate
   pip install path\to\PyAudio-0.2.14-cp312-cp312-win_amd64.whl
   ```

**Option 2: Install Visual C++ Build Tools**
1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
2. Select "Desktop development with C++"
3. Run setup again

---

### Issue: "package.json not found"

**Error:**
```
ERROR: package.json not found in ui directory
```

**Solution:**
This was fixed in the latest setup.bat. Run:
```bash
.\setup.bat
```

---

### Issue: Backend won't start

**Symptoms:**
- Backend window closes immediately
- Import errors in logs

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version
   # Should be 3.8 or higher
   ```

2. **Reinstall dependencies:**
   ```bash
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Check for missing modules:**
   ```bash
   python -c "import numpy, pvporcupine, google.generativeai"
   ```

4. **Check logs:**
   ```bash
   type data\logs\prism_*.log
   ```

---

### Issue: UI won't start

**Symptoms:**
- UI window doesn't appear
- Electron errors

**Solutions:**

1. **Reinstall Electron:**
   ```bash
   rmdir /s /q node_modules\electron
   npm install electron@^28.2.0
   ```

2. **Clear npm cache:**
   ```bash
   npm cache clean --force
   npm install
   ```

3. **Check Node version:**
   ```bash
   node --version
   # Should be 16 or higher
   ```

---

### Issue: "Gemini API key not configured"

**Error:**
```
ValueError: Gemini API key not configured
```

**Solution:**

1. **Get API key:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Click "Create API Key"
   - Copy the key

2. **Add to .env:**
   ```env
   GEMINI_API_KEY=your-actual-key-here
   ```

3. **Restart PRISM:**
   ```bash
   .\start.bat
   ```

---

### Issue: Rate limit exceeded

**Error:**
```
429 Rate limit exceeded
```

**Solutions:**

1. **Wait:** Limits reset every minute (RPM) or at midnight Pacific (RPD)

2. **Switch models:**
   ```env
   # In .env, change to higher-limit model
   GEMINI_MODEL=gemini-2.0-flash-lite  # 1000 RPD
   ```

3. **Check usage:**
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Monitor your quota

---

### Issue: Wake word not detected

**Symptoms:**
- No response when saying "Prism"
- Manual activation works

**Solutions:**

1. **Check microphone permissions:**
   - Windows Settings → Privacy → Microphone
   - Enable for desktop apps

2. **Test microphone:**
   - Open Sound Settings
   - Test microphone input
   - Adjust sensitivity

3. **Check Porcupine key:**
   ```env
   # In .env
   PORCUPINE_ACCESS_KEY=your-key-here
   ```
   Get key from [Picovoice Console](https://console.picovoice.ai/)

4. **Use alternative activation:**
   - Click the orb
   - Press Ctrl+Space
   - Type your command

---

### Issue: Voice recognition not working

**Symptoms:**
- Voice activation works but no transcription
- "Could not understand audio" errors

**Solutions:**

1. **Check internet connection:**
   - Voice recognition requires internet
   - Uses Google Speech Recognition API

2. **Check microphone:**
   - Ensure microphone is working
   - Test in other applications

3. **Adjust audio settings:**
   ```env
   # In .env, try different language
   VOICE_LANGUAGE=en-US
   ```

4. **Use text input:**
   - Type commands instead
   - Works offline

---

### Issue: High CPU usage

**Solutions:**

1. **Disable wake word:**
   ```env
   ENABLE_WAKE_WORD=false
   ```

2. **Close unnecessary apps**

3. **Adjust animation speed:**
   - Open Settings in UI
   - Set to "slow"

---

### Issue: Icons not showing

**Symptoms:**
- Default Electron icon appears
- No system tray icon

**Solution:**

This is normal! Icons are optional. To add custom icons:

1. **Create or download icons:**
   - `icon.png` (256x256px)
   - `tray-icon.png` (32x32px)

2. **Save to:**
   ```
   ui/assets/icon.png
   ui/assets/tray-icon.png
   ```

3. **Restart PRISM**

See `ui/assets/README.md` for details.

---

### Issue: WebSocket connection failed

**Error:**
```
WebSocket connection failed
```

**Solutions:**

1. **Check firewall:**
   - Allow `python.exe` and `node.exe`
   - Port 9876 should be open

2. **Check if port is in use:**
   ```bash
   netstat -ano | findstr :9876
   ```

3. **Restart both components:**
   - Close backend and UI
   - Run `start.bat` again

---

### Issue: Database errors

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Close all PRISM instances:**
   - Check Task Manager
   - Kill any python.exe running PRISM

2. **Delete database (loses history):**
   ```bash
   del data\memory.db
   ```

3. **Restart PRISM**

---

## 🔍 Diagnostic Commands

### Check Python environment
```bash
venv\Scripts\activate
python -c "import sys; print(sys.version)"
pip list
```

### Check Node environment
```bash
node --version
npm --version
npm list
```

### Check PRISM modules
```bash
venv\Scripts\activate
python -c "import backend.config; print('Config OK')"
python -c "import backend.ai_engine; print('AI Engine OK')"
python -c "import backend.voice_pipeline; print('Voice OK')"
```

### View logs
```bash
# Latest log
type data\logs\prism_*.log | more

# All logs
dir data\logs
```

---

## 🆘 Still Having Issues?

### 1. Run Complete Reinstall
```bash
# Backup your .env
copy .env .env.backup

# Remove everything
rmdir /s /q venv
rmdir /s /q node_modules
del data\memory.db

# Reinstall
.\setup.bat

# Restore .env
copy .env.backup .env

# Start
.\start.bat
```

### 2. Check System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 16 or higher
- **OS**: Windows 10/11
- **RAM**: 4GB minimum
- **Disk**: 500MB free space

### 3. Enable Debug Mode
```env
# In .env
LOG_LEVEL=DEBUG
```

Check `data/logs/` for detailed information.

### 4. Get Help
- Check [README.md](README.md)
- Review [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Open GitHub Issue with:
  - Python version
  - Node version
  - Error messages
  - Log files

---

## 📝 Prevention Tips

### 1. Keep Dependencies Updated
```bash
# Python
venv\Scripts\activate
pip install --upgrade -r requirements.txt

# Node
npm update
```

### 2. Regular Cleanup
```bash
# Clear old logs (older than 30 days)
forfiles /p data\logs /s /m *.log /d -30 /c "cmd /c del @path"

# Clear npm cache
npm cache clean --force
```

### 3. Backup Configuration
```bash
# Backup .env regularly
copy .env .env.backup
```

### 4. Monitor Usage
- Check API quotas regularly
- Monitor disk space
- Watch for rate limits

---

## ✅ Verification Checklist

After fixing issues, verify:

- [ ] Backend starts without errors
- [ ] UI window appears
- [ ] Logs show "Gemini initialized"
- [ ] Text input works
- [ ] AI responds
- [ ] Voice activation works (if enabled)
- [ ] System commands execute
- [ ] No errors in logs

---

<div align="center">

**Need more help?** Check the full documentation or open an issue!

</div>
