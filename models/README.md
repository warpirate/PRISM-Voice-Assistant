# Wake Word Models Directory

This directory contains wake word detection models for Snowboy.

## Quick Setup (Free!)

### Option 1: Use Pre-trained Model (Easiest)
Download a pre-trained "Alexa" or "Computer" model:
- https://github.com/Kitt-AI/snowboy/tree/master/resources/models

Place the `.pmdl` file here and rename to `prism.pmdl`

### Option 2: Train Your Own "PRISM" Wake Word (Recommended!)

1. **Go to Snowboy Website**
   - Visit: https://snowboy.kitt.ai/
   - Create a free account (no credit card needed!)

2. **Train Your Model**
   - Click "Create Hotword"
   - Name it: "PRISM"
   - Record yourself saying "PRISM" 3 times
   - Click "Train" and download the `.pmdl` file

3. **Install the Model**
   - Save the downloaded file as `prism.pmdl` in this directory
   - Also download `common.res` from: https://github.com/Kitt-AI/snowboy/blob/master/resources/common.res
   - Place both files here

## Required Files

```
models/
├── prism.pmdl      # Your trained wake word model
└── common.res      # Snowboy resource file (required)
```

## Testing Your Model

After placing the files, run:
```bash
python test_wake_word.py
```

Say "PRISM" and it should detect it!

## Troubleshooting

**Model not detected?**
- Make sure files are named exactly: `prism.pmdl` and `common.res`
- Check file permissions
- Try adjusting sensitivity in `voice_pipeline.py` (line 88)

**Want better accuracy?**
- Record more samples on Snowboy website
- Speak clearly and consistently
- Train in a quiet environment

---

**100% Free, No API Keys Needed!** 🎉
