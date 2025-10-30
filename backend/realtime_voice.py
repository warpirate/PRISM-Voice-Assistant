"""
Real-time Voice Module
Handles bidirectional audio streaming with Gemini Live API
Uses WebSocket-based streaming (not WebRTC) via Google GenAI client
"""

import asyncio
import io
import wave
from typing import Optional, Callable, Dict, Any
from loguru import logger
import pyaudio

try:
    from google import genai
    from google.genai import types
    import soundfile as sf
    import librosa
    GENAI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google GenAI or audio libraries not available: {e}")
    GENAI_AVAILABLE = False

from backend.config import config


class RealtimeVoiceSession:
    """
    Manages real-time bidirectional voice conversation with Gemini Live API
    Uses WebSocket streaming for continuous audio input/output
    """

    def __init__(self):
        self.client = None
        self.session = None
        self._context_manager = None
        self.audio: Optional[pyaudio.PyAudio] = None
        self.input_stream: Optional[pyaudio.Stream] = None
        self.output_stream: Optional[pyaudio.Stream] = None
        
        # Audio configuration
        self.input_sample_rate = 16000  # Gemini expects 16kHz PCM input
        self.output_sample_rate = 24000  # Gemini outputs 24kHz PCM
        self.channels = 1  # Mono
        self.chunk_size = 1024  # Match sample code
        self.format = pyaudio.paInt16
        
        # Session state
        self.is_active = False
        self.send_task = None
        self.receive_task = None
        self.play_task = None
        
        # Audio queues
        self.audio_in_queue: Optional[asyncio.Queue] = None
        self.out_queue: Optional[asyncio.Queue] = None
        
        # Callbacks
        self.on_audio_received: Optional[Callable] = None
        self.on_text_received: Optional[Callable] = None
        self.on_user_speech: Optional[Callable] = None
        self.on_function_call: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        
    def _get_session_config(self):
        """Get configuration for Gemini Live session using types.LiveConnectConfig"""
        
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
                )
            )
        )
    
    async def start_audio_streams(self):
        """Initialize audio input/output streams"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Get default input device
            mic_info = self.audio.get_default_input_device_info()
            
            # Input stream (microphone) - 16kHz for Gemini input
            self.input_stream = await asyncio.to_thread(
                self.audio.open,
                format=self.format,
                channels=self.channels,
                rate=self.input_sample_rate,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=self.chunk_size
            )
            
            # Output stream (speakers) - 24kHz for Gemini output
            self.output_stream = await asyncio.to_thread(
                self.audio.open,
                format=self.format,
                channels=self.channels,
                rate=self.output_sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.success("Audio streams initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio streams: {e}")
            raise
    
    async def _listen_audio(self):
        """Read audio from microphone and queue it"""
        logger.info("Starting audio listen loop...")
        
        try:
            while self.is_active:
                if not self.input_stream:
                    await asyncio.sleep(0.1)
                    continue
                
                # Read audio in thread to avoid blocking
                data = await asyncio.to_thread(
                    self.input_stream.read,
                    self.chunk_size,
                    exception_on_overflow=False
                )
                
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                
        except asyncio.CancelledError:
            logger.info("Listen loop cancelled")
        finally:
            logger.info("Audio listen loop stopped")
    
    async def _send_realtime(self):
        """Send queued data to Gemini session"""
        logger.info("Starting realtime send loop...")
        
        try:
            while self.is_active:
                msg = await self.out_queue.get()
                await self.session.send(input=msg)
                
        except asyncio.CancelledError:
            logger.info("Realtime send cancelled")
        finally:
            logger.info("Realtime send loop stopped")
    
    async def _receive_audio_loop(self):
        """Continuously receive audio from Gemini and queue for playback"""
        logger.info("Starting audio receive loop...")
        
        try:
            while self.is_active:
                turn = self.session.receive()
                async for response in turn:
                    if not self.is_active:
                        break
                    
                    # Handle audio data
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        continue
                    
                    # Handle text response
                    if text := response.text:
                        logger.info(f"Assistant: {text}")
                        if self.on_text_received:
                            await self.on_text_received(text)
                
                # Clear audio queue on turn complete (for interruptions)
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
                                        
        except asyncio.CancelledError:
            logger.info("Receive loop cancelled")
        except Exception as e:
            if self.is_active:
                logger.error(f"Receive loop failed: {e}", exc_info=True)
        finally:
            logger.info("Audio receive loop stopped")
    
    async def _play_audio_loop(self):
        """Play audio from queue to speakers"""
        logger.info("Starting audio playback loop...")
        
        try:
            while self.is_active:
                bytestream = await self.audio_in_queue.get()
                if self.output_stream:
                    await asyncio.to_thread(self.output_stream.write, bytestream)
                    
        except asyncio.CancelledError:
            logger.info("Playback loop cancelled")
        finally:
            logger.info("Audio playback loop stopped")
    
    async def start_session(self):
        """Start the real-time voice session with continuous bidirectional streaming"""
        try:
            if not GENAI_AVAILABLE:
                logger.error("Google GenAI library not available - install google-genai package")
                return False
            
            if not config.ai.gemini_api_key or config.ai.gemini_api_key == "your_gemini_api_key_here":
                logger.error("GEMINI_API_KEY not configured in .env file")
                return False
            
            logger.info("Starting Gemini Live API session...")
            
            # Initialize client
            self.client = genai.Client(
                http_options={"api_version": "v1beta"},
                api_key=config.ai.gemini_api_key
            )
            logger.success("GenAI client initialized")
            
            # Initialize audio streams
            await self.start_audio_streams()
            
            # Initialize queues
            self.audio_in_queue = asyncio.Queue()
            self.out_queue = asyncio.Queue(maxsize=5)
            
            # Use native audio model
            model = "models/gemini-2.5-flash-native-audio-preview-09-2025"
            session_config = self._get_session_config()
            
            logger.info(f"Connecting to model: {model}")
            
            # Connect to Live API
            context_manager = self.client.aio.live.connect(model=model, config=session_config)
            self.session = await context_manager.__aenter__()
            self._context_manager = context_manager
            logger.success("Connected to Gemini Live API")
            
            self.is_active = True
            
            # Start all streaming tasks
            self.send_task = asyncio.create_task(self._listen_audio())
            send_realtime_task = asyncio.create_task(self._send_realtime())
            self.receive_task = asyncio.create_task(self._receive_audio_loop())
            self.play_task = asyncio.create_task(self._play_audio_loop())
            
            if self.on_state_change:
                await self.on_state_change("active")
            
            logger.success("Real-time voice session active")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}", exc_info=True)
            await self.stop_session()
            return False
    
    def _on_task_done(self, task_name: str, task):
        """Callback when a streaming task completes"""
        try:
            if not task.cancelled():
                exception = task.exception()
                if exception:
                    logger.error(f"{task_name} task failed with exception: {exception}")
                else:
                    logger.info(f"{task_name} task completed normally")
        except Exception as e:
            logger.error(f"Error in task done callback for {task_name}: {e}")
    
    async def send_function_response(self, function_call_id: str, function_name: str, response_data: Dict[str, Any]):
        """Send function execution result back to Gemini using new API format"""
        try:
            if not self.session or not self.is_active:
                logger.warning("Cannot send function response - session not active")
                return
            
            # Use new send_tool_response API with FunctionResponse
            function_response = types.FunctionResponse(
                id=function_call_id,
                name=function_name,
                response=response_data
            )
            
            await self.session.send_tool_response(function_responses=[function_response])
            logger.info(f"Sent function response for {function_name} (id: {function_call_id})")
        except Exception as e:
            logger.error(f"Error sending function response: {e}", exc_info=True)
    
    async def stop_session(self):
        """Stop the real-time voice session"""
        logger.info("Stopping real-time voice session...")
        
        self.is_active = False
        
        # Cancel streaming tasks
        if self.send_task:
            self.send_task.cancel()
            try:
                await self.send_task
            except asyncio.CancelledError:
                pass
            self.send_task = None
        
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
            self.receive_task = None
        
        if self.play_task:
            self.play_task.cancel()
            try:
                await self.play_task
            except asyncio.CancelledError:
                pass
            self.play_task = None
        
        # Close Live API session
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing session: {e}")
            self._context_manager = None
            self.session = None
        
        # Close audio streams
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
        
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        if self.on_state_change:
            await self.on_state_change("inactive")
        
        logger.success("Real-time voice session stopped")
