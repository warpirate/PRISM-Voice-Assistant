"""
Test Snowboy Wake Word Detection
Run this to verify your wake word model is working
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("PRISM Wake Word Test (Snowboy - FREE!)")
print("=" * 60)
print()

# Check if Snowboy is installed
try:
    import snowboydetect
    print("✓ Snowboy installed")
except ImportError:
    print("✗ Snowboy not installed")
    print("\nInstall with: pip install snowboy")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Check if PyAudio is installed
try:
    import pyaudio
    print("✓ PyAudio installed")
except ImportError:
    print("✗ PyAudio not installed")
    print("\nInstall with: pip install pyaudio")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Check for model files
model_path = os.path.join(os.path.dirname(__file__), "models", "prism.pmdl")
resource_path = os.path.join(os.path.dirname(__file__), "models", "common.res")

print()
print("Checking for wake word model files...")
print(f"Model path: {model_path}")
print(f"Resource path: {resource_path}")
print()

if not os.path.exists(model_path):
    print("✗ Wake word model (prism.pmdl) not found!")
    print()
    print("To get started:")
    print("1. Visit: https://snowboy.kitt.ai/")
    print("2. Create account (FREE!)")
    print("3. Train 'PRISM' wake word")
    print("4. Download prism.pmdl to models/ folder")
    print()
    print("Or download a pre-trained model:")
    print("https://github.com/Kitt-AI/snowboy/tree/master/resources/models")
    print()
    input("Press Enter to exit...")
    sys.exit(1)

if not os.path.exists(resource_path):
    print("✗ Resource file (common.res) not found!")
    print()
    print("Download from:")
    print("https://github.com/Kitt-AI/snowboy/blob/master/resources/common.res")
    print(f"Save to: {resource_path}")
    print()
    input("Press Enter to exit...")
    sys.exit(1)

print("✓ Model files found")
print()

# Initialize Snowboy
try:
    detector = snowboydetect.SnowboyDetect(
        resource_filename=resource_path.encode(),
        model_str=model_path.encode()
    )
    detector.SetSensitivity(b"0.5")
    detector.SetAudioGain(1.0)
    print("✓ Snowboy detector initialized")
except Exception as e:
    print(f"✗ Failed to initialize detector: {e}")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Initialize audio
try:
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=2048
    )
    print("✓ Microphone initialized")
except Exception as e:
    print(f"✗ Failed to initialize microphone: {e}")
    input("\nPress Enter to exit...")
    sys.exit(1)

print()
print("=" * 60)
print("🎤 LISTENING FOR WAKE WORD 'PRISM'")
print("=" * 60)
print()
print("Say 'PRISM' to test wake word detection...")
print("Press Ctrl+C to stop")
print()

detection_count = 0

try:
    while True:
        # Read audio
        data = stream.read(2048, exception_on_overflow=False)
        
        # Detect wake word
        ans = detector.RunDetection(data)
        
        if ans == 1:  # Wake word detected!
            detection_count += 1
            print(f"🎉 WAKE WORD DETECTED! (#{detection_count})")
            print(f"   Time: {time.strftime('%H:%M:%S')}")
            print()
            time.sleep(1)  # Cooldown to avoid multiple detections
        elif ans == -1:
            print("⚠ Detection error")

except KeyboardInterrupt:
    print()
    print("=" * 60)
    print("Test stopped by user")
    print(f"Total detections: {detection_count}")
    print("=" * 60)

finally:
    # Cleanup
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print()
    print("✓ Cleanup complete")
    print()
    input("Press Enter to exit...")
