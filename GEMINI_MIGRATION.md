# Migrating to Google Gemini API

PRISM now uses Google's Gemini API instead of OpenAI or Anthropic. This guide will help you migrate smoothly.

---

## 🎯 Why Gemini?

### Benefits
- ✅ **Free Tier Available** - Generous free quota for personal use
- ✅ **Better Performance** - Fast response times
- ✅ **Multimodal Capable** - Ready for future image/video features
- ✅ **Google Integration** - Seamless with Google ecosystem
- ✅ **Simplified Setup** - Single API key, easy configuration

---

## 🚀 Migration Steps

### Step 1: Get Gemini API Key

1. **Visit Google AI Studio**
   - Go to [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Select "Create API key in new project" (or choose existing)
   - Copy the generated key

3. **Save Your Key**
   - Store it securely (you'll need it for `.env`)

### Step 2: Update Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate

# Update dependencies
pip install -r requirements.txt
```

This will install `google-generativeai` and remove old AI provider packages.

### Step 3: Update Configuration

**Edit your `.env` file:**

**Before:**
```env
AI_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**After:**
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
```

### Step 4: Test the Migration

1. **Start PRISM**
   ```bash
   start.bat
   ```

2. **Test Basic Interaction**
   - Type "Hello, how are you?"
   - Try "What can you do?"
   - Test system commands: "Open Notepad"

3. **Check Logs**
   - Backend console should show: "✓ Gemini initialized"
   - No errors about missing API keys

---

## 🔧 Troubleshooting

### Issue: "Google Generative AI library not available"

**Solution:**
```bash
pip install google-generativeai==0.3.2
```

### Issue: "Gemini API key not configured"

**Solution:**
- Check `.env` file has `GEMINI_API_KEY=...`
- Ensure no extra spaces around the key
- Verify the key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Issue: "Rate limit exceeded"

**Solution:**
- Gemini has generous free limits (60 requests/minute)
- If exceeded, wait 1 minute or upgrade your quota
- Check usage at [Google Cloud Console](https://console.cloud.google.com/)

### Issue: API Errors

**Solution:**
```bash
# Check your API key status
# Visit: https://console.cloud.google.com/apis/credentials
```

---

## 📊 Feature Comparison

| Feature | OpenAI GPT-4 | Anthropic Claude | **Gemini Pro** |
|---------|--------------|------------------|----------------|
| Free Tier | ❌ No | ❌ No | ✅ Yes |
| Speed | Fast | Fast | **Very Fast** |
| Context Window | 8K-128K | 100K-200K | 32K |
| Cost (paid) | $0.03/1K | $0.015/1K | **$0.001/1K** |
| Multimodal | Limited | No | ✅ Yes |

---

## 🎓 Gemini-Specific Features

### Available Models

PRISM uses `gemini-pro` by default. Future versions may support:

- `gemini-pro` - Text generation (current)
- `gemini-pro-vision` - Image understanding (planned)
- `gemini-ultra` - Most capable (when available)

### Configuration Options

You can customize Gemini behavior in `.env`:

```env
# Model selection
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-pro

# Generation parameters
TEMPERATURE=0.7          # Creativity (0.0-1.0)
MAX_TOKENS=1024         # Response length
```

---

## 💡 Best Practices

### 1. API Key Security
- Never commit `.env` to Git
- Use environment variables in production
- Rotate keys periodically

### 2. Rate Limiting
- Gemini free tier: 60 requests/minute
- For high volume, consider paid tier
- Implement exponential backoff for errors

### 3. Context Management
- Gemini Pro: 32K token context window
- Keep conversation history under 10 messages
- PRISM automatically manages context

### 4. Error Handling
- PRISM has fallback mode if API fails
- Basic commands work without internet
- Check logs for detailed error info

---

## 🔄 Rollback (if needed)

If you need to rollback to OpenAI/Anthropic:

1. **Reinstall old dependencies**
   ```bash
   pip install openai==1.12.0
   # or
   pip install anthropic==0.18.1
   ```

2. **Restore old AI engine**
   - Contact support or restore from backup

3. **Update `.env`**
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=your-old-key
   ```

---

## 📈 Performance Notes

### Response Times (Average)

| Provider | First Response | Streaming |
|----------|---------------|-----------|
| OpenAI GPT-4 | 2-4 seconds | ✅ Yes |
| Anthropic Claude | 1-3 seconds | ✅ Yes |
| **Gemini Pro** | **1-2 seconds** | 🔜 Coming |

### Token Efficiency

Gemini Pro is more token-efficient:
- **Fewer tokens** for same output quality
- **Lower costs** on paid tier
- **Better context utilization**

---

## 🎯 What Works Exactly the Same

✅ Voice interaction  
✅ System commands  
✅ File operations  
✅ Conversation history  
✅ Memory system  
✅ UI and animations  
✅ Keyboard shortcuts  
✅ System tray integration  

**The only change is the AI provider - everything else works identically!**

---

## 🆘 Getting Help

### Resources
- [Gemini API Docs](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com/)
- [API Pricing](https://ai.google.dev/pricing)
- [PRISM Issues](https://github.com/yourusername/prism/issues)

### Common Questions

**Q: Is my old conversation history lost?**  
A: No! All conversation data in `data/memory.db` is preserved.

**Q: Can I use both Gemini and OpenAI?**  
A: Currently no, but multi-provider support is planned for v1.3.0.

**Q: Does this affect voice features?**  
A: No, voice recognition and synthesis are unchanged.

**Q: Is Gemini as good as GPT-4?**  
A: Gemini Pro performs excellently for PRISM's use cases. Try it!

---

## 🎉 Welcome to Gemini!

You're now using one of the most advanced AI models available. Enjoy:

- Faster responses
- Lower costs (or free!)
- Better integration
- Future multimodal features

**Test it out with:** "Hey PRISM, what's new with Gemini?"

---

<div align="center">

**Migration Complete!** 🚀

PRISM is now powered by Google Gemini

</div>
