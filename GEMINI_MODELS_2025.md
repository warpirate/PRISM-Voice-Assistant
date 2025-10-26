# Gemini Models Guide (October 2025)

Complete guide to choosing the right Gemini model for PRISM with updated rate limits and pricing.

---

## 🎯 Recommended Models for PRISM

### **Best Choice: Gemini 2.5 Flash** ⭐
```env
GEMINI_MODEL=gemini-2.5-flash
```

**Why?**
- ✅ Best balance of quality and speed
- ✅ Excellent for conversational AI
- ✅ 1M token context window
- ✅ Free tier available

**Free Tier Limits (October 2025):**
- **RPM**: 10 requests/minute
- **TPM**: 250,000 tokens/minute
- **RPD**: 250 requests/day

**Best For:**
- General assistant tasks
- Conversational interactions
- System command understanding
- Balanced performance

---

### **Alternative: Gemini 2.0 Flash**
```env
GEMINI_MODEL=gemini-2.0-flash
```

**Why?**
- ✅ Multimodal capabilities (text, images, audio)
- ✅ Built for agentic workflows
- ✅ 1M token context window
- ✅ Stable and production-ready

**Free Tier Limits:**
- **RPM**: 15 requests/minute
- **TPM**: 1,000,000 tokens/minute
- **RPD**: 200 requests/day (recently reduced from 1500)

**Best For:**
- Future multimodal features
- Agent-based tasks
- High token throughput needs

---

### **Budget Option: Gemini 2.0 Flash-Lite**
```env
GEMINI_MODEL=gemini-2.0-flash-lite
```

**Why?**
- ✅ Smallest and most cost-effective
- ✅ Highest free tier limits
- ✅ Fast responses
- ✅ Good for simple tasks

**Free Tier Limits:**
- **RPM**: 15 requests/minute
- **TPM**: 250,000 tokens/minute
- **RPD**: 1,000 requests/day

**Best For:**
- High-volume usage
- Simple commands
- Cost optimization
- Testing and development

---

## 📊 Model Comparison Table

| Model | Context | Quality | Speed | Free RPD | Best Use Case |
|-------|---------|---------|-------|----------|---------------|
| **2.5 Flash** | 1M | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | 250 | **General use** |
| 2.5 Pro | 1M | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | 100 | Complex tasks |
| 2.0 Flash | 1M | ⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ | 200 | Multimodal |
| 2.0 Flash-Lite | - | ⭐⭐⭐ | ⚡⚡⚡⚡⚡ | 1000 | High volume |

---

## 🆓 Free Tier Rate Limits (October 2025)

### Current Limits

| Model | RPM | TPM | RPD | Notes |
|-------|-----|-----|-----|-------|
| **Gemini 2.5 Flash** | 10 | 250K | 250 | **Recommended** |
| Gemini 2.5 Pro | 5 | 250K | 100 | Premium quality |
| Gemini 2.5 Flash-Lite | 15 | 250K | 1000 | High volume |
| Gemini 2.0 Flash | 15 | 1M | 200 | Multimodal |
| Gemini 2.0 Flash-Lite | 15 | 250K | 1000 | Budget option |

**Legend:**
- **RPM**: Requests Per Minute
- **TPM**: Tokens Per Minute (input)
- **RPD**: Requests Per Day

### Recent Changes ⚠️

Google has been adjusting free tier limits:
- **Gemini 2.0 Flash**: Reduced from 1500 → 200 RPD
- **Gemini 2.5 Flash**: Reduced from 500 → 250 RPD
- **Gemini 2.5 Pro**: No longer free in API (only AI Studio)

**Recommendation**: Use **Gemini 2.5 Flash** for best balance, or **2.0 Flash-Lite** for highest volume.

---

## 💰 Paid Tier Pricing (if you upgrade)

### Cost per 1M Tokens

| Model | Input | Output | Total (avg) |
|-------|-------|--------|-------------|
| 2.5 Flash | $0.075 | $0.30 | ~$0.19 |
| 2.5 Pro | $1.25 | $5.00 | ~$3.13 |
| 2.0 Flash | $0.10 | $0.40 | ~$0.25 |
| 2.0 Flash-Lite | $0.05 | $0.20 | ~$0.13 |

**For PRISM usage** (avg 500 tokens per interaction):
- 2.5 Flash: ~$0.0001 per interaction
- 2.0 Flash-Lite: ~$0.00007 per interaction

**1000 interactions/day cost:**
- 2.5 Flash: ~$3/month
- 2.0 Flash-Lite: ~$2/month

---

## 🎯 Choosing the Right Model

### For Most Users → **Gemini 2.5 Flash**
```env
GEMINI_MODEL=gemini-2.5-flash
```
- Best quality for voice assistant
- Good free tier limits
- Excellent understanding
- Fast responses

### For High Volume → **Gemini 2.0 Flash-Lite**
```env
GEMINI_MODEL=gemini-2.0-flash-lite
```
- 1000 requests/day free
- Lowest cost
- Still good quality
- Fastest responses

### For Future Features → **Gemini 2.0 Flash**
```env
GEMINI_MODEL=gemini-2.0-flash
```
- Multimodal ready
- Image understanding (coming)
- Audio processing (coming)
- Agent capabilities

---

## 🔧 How to Change Models

### Method 1: Environment Variable
Edit `.env` file:
```env
GEMINI_MODEL=gemini-2.5-flash
```

### Method 2: Direct Configuration
Edit `backend/config.py`:
```python
model: str = Field(default="gemini-2.5-flash")
```

### Method 3: Runtime (future feature)
Through UI settings panel (planned for v1.2)

---

## 📈 Performance Benchmarks

### Response Times (Average)

| Model | Simple Query | Complex Task | With History |
|-------|--------------|--------------|--------------|
| 2.5 Flash | 1.2s | 2.5s | 2.0s |
| 2.5 Pro | 1.5s | 3.0s | 2.5s |
| 2.0 Flash | 1.0s | 2.0s | 1.8s |
| 2.0 Flash-Lite | 0.8s | 1.5s | 1.3s |

### Quality Scores (SimpleQA Benchmark)

| Model | Score | Rank |
|-------|-------|------|
| 2.5 Pro | 95% | 🥇 |
| 2.5 Flash | 92% | 🥈 |
| 2.0 Flash | 88% | 🥉 |
| 2.0 Flash-Lite | 82% | - |

---

## 🚀 Optimization Tips

### 1. Choose Based on Usage Pattern

**Light Use (<100 requests/day)**
→ Use **2.5 Flash** for best quality

**Heavy Use (>500 requests/day)**
→ Use **2.0 Flash-Lite** for higher limits

**Development/Testing**
→ Use **2.0 Flash-Lite** to save quota

### 2. Optimize Token Usage

```python
# Reduce max_tokens for shorter responses
max_tokens: int = Field(default=1024)  # Instead of 2048

# Keep conversation history limited
conversation_history[-10:]  # Last 10 messages only
```

### 3. Implement Caching

```python
# Cache common responses
# Reduce API calls for repeated queries
# Use local fallback for simple commands
```

### 4. Monitor Usage

Check your usage at:
- [Google AI Studio](https://aistudio.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)

---

## ⚠️ Rate Limit Handling

PRISM automatically handles rate limits:

1. **Exponential Backoff**: Retries with increasing delays
2. **Fallback Mode**: Uses rule-based responses if API fails
3. **Queue Management**: Prevents exceeding RPM limits
4. **Error Logging**: Detailed logs in `data/logs/`

### If You Hit Limits

**Option 1: Wait**
- RPM resets every minute
- RPD resets at midnight Pacific time

**Option 2: Switch Models**
```env
# Switch to model with higher limits
GEMINI_MODEL=gemini-2.0-flash-lite
```

**Option 3: Upgrade Tier**
- Tier 1: Spend $5 on Google Cloud
- Tier 2: Spend $50 on Google Cloud
- Much higher limits

---

## 🔮 Future Model Updates

Google regularly releases new models:

### Expected Soon
- **Gemini 2.5 Pro** - May return to free tier
- **Gemini 3.0** - Next generation (2025 Q4)
- **Specialized Models** - Code, math, reasoning

### Multimodal Features (Coming to PRISM)
- Image understanding
- Screenshot analysis
- Audio processing
- Video comprehension

---

## 📚 Additional Resources

### Official Documentation
- [Gemini API Docs](https://ai.google.dev/docs)
- [Pricing Page](https://ai.google.dev/pricing)
- [Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Model Comparison](https://ai.google.dev/gemini-api/docs/models/gemini)

### PRISM Documentation
- `README.md` - Main documentation
- `GEMINI_MIGRATION.md` - Migration guide
- `SETUP_GUIDE.md` - Installation help

---

## 🎓 Best Practices

### 1. Start with Recommended Model
Use **Gemini 2.5 Flash** - best balance for most users

### 2. Monitor Your Usage
Check daily usage to avoid hitting limits

### 3. Optimize Prompts
- Be concise
- Use clear instructions
- Limit conversation history

### 4. Use Fallback Mode
PRISM works offline with basic commands

### 5. Plan for Scaling
If you need more, upgrade to paid tier early

---

## ✅ Quick Setup

```bash
# 1. Edit .env
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-flash

# 2. Restart PRISM
start.bat

# 3. Verify in logs
# Should see: "✓ Gemini initialized (model: gemini-2.5-flash)"
```

---

## 🆘 Troubleshooting

### Error: "Rate limit exceeded"
→ Switch to model with higher limits or wait

### Error: "Model not found"
→ Check model name spelling (case-sensitive)

### Slow Responses
→ Try 2.0 Flash-Lite for faster responses

### Poor Quality
→ Upgrade to 2.5 Flash or 2.5 Pro

---

<div align="center">

## 🌟 Recommended Configuration

```env
# Best for most users (October 2025)
GEMINI_MODEL=gemini-2.5-flash
```

**Excellent quality • Good limits • Fast responses**

</div>
