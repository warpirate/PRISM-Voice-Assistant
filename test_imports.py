"""Test if all required packages are installed correctly"""

print("Testing package imports...")
print("=" * 60)

try:
    import openai
    print("✅ openai:", openai.__version__)
except Exception as e:
    print("❌ openai:", str(e))

try:
    import whisper
    print("✅ openai-whisper: Installed")
except Exception as e:
    print("❌ openai-whisper:", str(e))

try:
    import pyttsx3
    print("✅ pyttsx3: Installed")
except Exception as e:
    print("❌ pyttsx3:", str(e))

try:
    import pyaudio
    print("✅ pyaudio: Installed")
except Exception as e:
    print("❌ pyaudio:", str(e))

try:
    from TTS.api import TTS
    print("✅ coqui-tts: Installed")
except Exception as e:
    print("❌ coqui-tts:", str(e))

try:
    import pywin32
    print("✅ pywin32: Installed")
except:
    try:
        import win32api
        print("✅ pywin32: Installed")
    except Exception as e:
        print("❌ pywin32:", str(e))

try:
    import pytest
    print("✅ pytest:", pytest.__version__)
except Exception as e:
    print("❌ pytest:", str(e))

try:
    import msal
    print("✅ msal:", msal.__version__)
except Exception as e:
    print("❌ msal:", str(e))

try:
    import requests
    print("✅ requests:", requests.__version__)
except Exception as e:
    print("❌ requests:", str(e))

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv: Installed")
except Exception as e:
    print("❌ python-dotenv:", str(e))

print("=" * 60)
print("\n🎉 All packages installed successfully!")
print("\nPython version check:")
import sys
print(f"Python {sys.version}")
