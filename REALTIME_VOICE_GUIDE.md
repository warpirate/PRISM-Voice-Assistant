# PRISM Real-time Voice Feature Guide

## What is Real-time Voice?

Real-time voice is a continuous, bidirectional audio streaming feature that allows you to have natural conversations with PRISM without pressing any buttons. Unlike push-to-talk mode, real-time voice keeps the microphone active and streams audio directly to Google's Gemini Live API.

## Quick Start

### 1. Verify Setup
Run the test script to ensure all dependencies are working:
```bash
python test_realtime.py
```

All tests should pass (✓ PASS).

### 2. Start PRISM
```bash
start.bat
```

### 3. Activate Real-time Voice
Click the **Real-time Voice button** (microphone icon with circle) in the input area at the bottom of the PRISM window.

### 4. Start Talking
Once you see "🎙️ Real-time voice mode activated!", just start speaking naturally. No need to press any buttons.

## Features

### Continuous Listening
- Microphone stays active
- Natural conversation flow
- No button presses needed
- Automatic speech detection

### Function Calling
Real-time voice can execute commands while you speak:
- **Open apps**: "Open Chrome", "Launch Calculator"
- **Web search**: "Search for weather today"
- **File operations**: "Open my downloads folder"

### Audio Quality
- **Input**: 16kHz PCM (optimized for Gemini)
- **Output**: 24kHz PCM (high-quality voice)
- **Latency**: Low-latency streaming (~500ms)

## How to Use

### Starting Real-time Voice
1. Click the real-time voice button (pink when active)
2. Wait for confirmation message
3. Start speaking naturally

### Stopping Real-time Voice
1. Click the real-time voice button again
2. System returns to push-to-talk mode

### Push-to-Talk Mode (Default)
- Click the regular voice button (blue)
- Speak your command
- System processes after you finish

## Troubleshooting

### "Failed to start real-time voice session"

**Check these:**
1. API key configured in `.env`
2. Internet connection active
3. Microphone permissions enabled
4. No other app using microphone

**Fix:**
```bash
# Verify API key
notepad .env

# Test dependencies
python test_realtime.py
```

### No Audio Output

**Solutions:**
1. Check Windows volume settings
2. Verify default audio device
3. Check PRISM logs in terminal
4. Restart PRISM

### Microphone Not Working

**Solutions:**
1. Windows Settings → Privacy → Microphone → Allow apps
2. Close other apps using microphone (Discord, Teams, etc.)
3. Check microphone is set as default device
4. Test microphone in Windows Sound settings

### "Could not access response.text" Error

This is handled automatically with fallback parsing. If you see it repeatedly:
1. Your input might trigger safety filters
2. Try rephrasing your request
3. Check Gemini API status

## Tips for Best Results

### Speaking Tips
- Speak clearly and naturally
- Avoid background noise
- Use a good quality microphone
- Keep commands concise

### Command Examples
- "What's the weather like today?"
- "Open Chrome and search for Python tutorials"
- "Create a new file called notes.txt"
- "What time is it?"
- "Tell me a joke"

### When to Use Real-time Voice
- Long conversations
- Natural back-and-forth dialogue
- When you want hands-free operation
- When you need quick responses

### When to Use Push-to-Talk
- Noisy environments
- Quick single commands
- When you want precise control
- To save API usage

## Technical Details

### API Model
- Uses `gemini-2.5-flash-native-audio-preview-09-2025`
- Supports bidirectional audio streaming
- Function calling enabled
- System instructions optimized for voice

### Audio Processing
- PyAudio for device access
- Librosa for resampling
- Soundfile for format conversion
- 512-byte chunks for low latency

### Network Requirements
- Stable internet connection
- WebSocket support
- ~50 Kbps upload/download

## Limitations

### Current Limitations
- Requires internet connection
- Uses Gemini API quota
- English language only (currently)
- No offline mode

### API Limits
- Free tier: 250 requests/day
- Real-time voice counts as continuous requests
- Monitor usage in Google AI Studio

## Advanced Configuration

### Adjust Audio Settings
Edit `backend/realtime_voice.py`:
```python
self.input_sample_rate = 16000  # Microphone sample rate
self.output_sample_rate = 24000  # Speaker sample rate
self.chunk_size = 512  # Chunk size (lower = less latency)
```

### Modify System Instructions
Edit `backend/realtime_voice.py` in `_get_session_config()`:
```python
"system_instruction": """Your custom instructions here"""
```

### Change Voice Model
Edit `backend/realtime_voice.py` in `start_session()`:
```python
model = "gemini-2.5-flash-native-audio-preview-09-2025"
```

## FAQ

**Q: Does real-time voice work offline?**
A: No, it requires internet connection to stream to Gemini Live API.

**Q: How much data does it use?**
A: Approximately 50 Kbps (~375 KB/minute) for bidirectional audio.

**Q: Can I use it with other languages?**
A: Currently optimized for English. Other languages may work but aren't tested.

**Q: Is my voice data stored?**
A: Audio is streamed to Google's servers but not stored by PRISM. Check Google's privacy policy for their data handling.

**Q: Can I use a different AI model?**
A: Real-time voice requires Gemini Live API. Other models don't support bidirectional audio streaming.

**Q: Why is there a delay?**
A: Network latency + processing time. Typical delay is 500-1000ms.

## Support

### Getting Help
1. Check PRISM logs in terminal
2. Run `python test_realtime.py`
3. Check `.env` configuration
4. Review this guide

### Reporting Issues
Include:
- Error messages from terminal
- Output of `test_realtime.py`
- Steps to reproduce
- PRISM version

## What's Next?

### Planned Improvements
- [ ] Multi-language support
- [ ] Custom wake words for real-time mode
- [ ] Noise cancellation
- [ ] Echo reduction
- [ ] Voice activity detection tuning
- [ ] Offline fallback mode

---

**Enjoy natural conversations with PRISM! 🎙️**
