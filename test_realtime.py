"""
Test script to verify realtime voice dependencies and setup
"""
import sys
import os

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        from google import genai
        print("✓ google.genai imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.genai: {e}")
        return False
    
    try:
        from google.genai import types
        print("✓ google.genai.types imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.genai.types: {e}")
        return False
    
    try:
        import soundfile as sf
        print("✓ soundfile imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import soundfile: {e}")
        return False
    
    try:
        import librosa
        print("✓ librosa imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import librosa: {e}")
        return False
    
    try:
        import pyaudio
        print("✓ pyaudio imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyaudio: {e}")
        return False
    
    return True

def test_api_key():
    """Test API key configuration"""
    print("\nTesting API key...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("✗ GEMINI_API_KEY not configured in .env file")
        return False
    
    print(f"✓ GEMINI_API_KEY configured (length: {len(api_key)})")
    return True

def test_audio_devices():
    """Test audio device availability"""
    print("\nTesting audio devices...")
    
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        
        input_devices = []
        output_devices = []
        
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(info['name'])
            if info['maxOutputChannels'] > 0:
                output_devices.append(info['name'])
        
        print(f"✓ Found {len(input_devices)} input device(s)")
        print(f"✓ Found {len(output_devices)} output device(s)")
        
        audio.terminate()
        return len(input_devices) > 0 and len(output_devices) > 0
        
    except Exception as e:
        print(f"✗ Failed to enumerate audio devices: {e}")
        return False

def test_genai_client():
    """Test GenAI client initialization"""
    print("\nTesting GenAI client...")
    
    try:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("✗ Cannot test client - API key not configured")
            return False
        
        client = genai.Client(api_key=api_key)
        print("✓ GenAI client initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to initialize GenAI client: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PRISM Realtime Voice Dependency Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("API Key", test_api_key()))
    results.append(("Audio Devices", test_audio_devices()))
    results.append(("GenAI Client", test_genai_client()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! Realtime voice should work.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)
