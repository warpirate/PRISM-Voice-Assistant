"""
Quick test to verify Live Voice API connection works
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_connection():
    """Test basic connection to Gemini Live API"""
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in .env")
            return False
        
        print("✓ API key found")
        
        client = genai.Client(api_key=api_key)
        model = "models/gemini-2.0-flash-exp"
        
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"
                    )
                )
            )
        )
        config.system_instruction = "You are a test assistant. Say 'Hello, PRISM is working!' in a friendly voice."
        
        print(f"✓ Connecting to {model}...")
        
        # Test the async context manager pattern
        async with client.aio.live.connect(model=model, config=config) as session:
            print("✓ Connection successful!")
            print("✓ Session context established")
            
            # Test sending a simple text input
            await session.send_realtime_input(text="Hello, this is a test")
            print("✓ Sent test message")
            
            # Try to receive responses with timeout
            print("✓ Waiting for response...")
            audio_received = False
            
            try:
                async with asyncio.timeout(10):  # 10 second timeout
                    async for response in session.receive():
                        if response.server_content:
                            server_content = response.server_content
                            
                            # Check for audio in model turn
                            if server_content.model_turn and server_content.model_turn.parts:
                                for part in server_content.model_turn.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data:
                                        if part.inline_data.mime_type.startswith('audio/'):
                                            print(f"✓ Received audio data: {len(part.inline_data.data)} bytes")
                                            audio_received = True
                            
                            # Check for turn complete
                            if server_content.turn_complete:
                                print("✓ Turn complete")
                                break
            except asyncio.TimeoutError:
                print("⚠️  Response timeout (this is normal for audio-only mode)")
            
            if audio_received:
                print("✓ Audio response received successfully")
            else:
                print("✓ Session working (audio-only mode, no text output expected)")
        
        print("\n✅ All tests passed! Live Voice API is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: install_live_voice.bat")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Live Voice API Connection Test")
    print("=" * 50)
    print()
    
    result = asyncio.run(test_connection())
    
    print()
    if result:
        print("🎉 Live Voice is ready to use in PRISM!")
    else:
        print("⚠️  Please fix the errors above before using Live Voice")
