"""Test imports for PRISM"""
import sys
print("Testing imports...")

try:
    from backend.realtime_voice import RealtimeVoiceSession
    print("✓ realtime_voice imported successfully")
except Exception as e:
    print(f"✗ realtime_voice import failed: {e}")
    sys.exit(1)

try:
    from backend.voice_pipeline import VoicePipeline
    print("✓ voice_pipeline imported successfully")
except Exception as e:
    print(f"✗ voice_pipeline import failed: {e}")
    sys.exit(1)

try:
    from backend.coordinator import coordinator
    print("✓ coordinator imported successfully")
except Exception as e:
    print(f"✗ coordinator import failed: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
print("PRISM is ready to run.")
