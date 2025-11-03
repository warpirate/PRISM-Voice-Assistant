"""
Gemini Live API Integration
Real-time bidirectional voice streaming with Gemini 2.5 Flash Native Audio
"""

import asyncio
import io
from typing import Optional, Callable, Dict, Any
from loguru import logger
from datetime import datetime

try:
    from google import genai
    from google.genai import types
    import pyaudio
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Live Voice dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False


class LiveVoiceSession:
    """
    Manages a live voice session with Gemini 2.5 Flash Native Audio
    Handles bidirectional audio streaming and real-time responses
    """
    
    def __init__(self, api_key: str, model: str = "models/gemini-2.0-flash-exp"):
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError("Live Voice dependencies not available. Install google-generativeai and pyaudio.")
        
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        
        # Audio configuration - Gemini Live uses 24kHz for both input and output
        self.sample_rate = 24000  # 24kHz unified sample rate
        self.channels = 1  # Mono
        self.chunk_size = 2400  # 100ms chunks (24000 * 0.1)
        
        # Session state
        self.session: Optional[Any] = None
        self.is_active = False
        self.audio_input: Optional[pyaudio.PyAudio] = None
        self.audio_output: Optional[pyaudio.PyAudio] = None
        self.input_stream: Optional[Any] = None
        self.output_stream: Optional[Any] = None
        
        # Callbacks
        self.on_response_start: Optional[Callable] = None
        self.on_response_chunk: Optional[Callable[[bytes], None]] = None
        self.on_response_end: Optional[Callable] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_audio_level: Optional[Callable[[float], None]] = None
        
        # Tasks
        self._input_task: Optional[asyncio.Task] = None
        self._output_task: Optional[asyncio.Task] = None
        
        logger.info(f"LiveVoiceSession initialized with model: {model}")
    
    async def start(self, system_instruction: str = "You are PRISM, a helpful AI assistant. Respond naturally and conversationally."):
        """Start the live voice session"""
        if self.is_active:
            logger.warning("Live voice session already active")
            return
        
        try:
            logger.info("Starting live voice session...")
            
            # Initialize PyAudio
            self.audio_input = pyaudio.PyAudio()
            self.audio_output = pyaudio.PyAudio()
            
            # Open input stream (microphone) - 24kHz mono
            self.input_stream = self.audio_input.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Open output stream (speakers) - 24kHz mono
            self.output_stream = self.audio_output.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Configure session for Gemini Live API
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Puck"  # Natural conversational voice
                        )
                    )
                )
            )
            
            if system_instruction:
                config.system_instruction = system_instruction
            
            # Connect to Gemini Live API
            logger.info("Connecting to Gemini Live API...")
            # Note: connect() returns an async context manager, we'll use it in the processing tasks
            self.session = self.client.aio.live.connect(model=self.model, config=config)
            self._session_context = None
            
            self.is_active = True
            logger.success("Live voice session started successfully")
            
            # Start audio processing tasks
            self._input_task = asyncio.create_task(self._process_input_audio())
            self._output_task = asyncio.create_task(self._process_output_audio())
            
        except Exception as e:
            logger.error(f"Failed to start live voice session: {e}", exc_info=True)
            await self.stop()
            if self.on_error:
                self.on_error(str(e))
            raise
    
    async def stop(self):
        """Stop the live voice session"""
        if not self.is_active:
            return
        
        logger.info("Stopping live voice session...")
        self.is_active = False
        
        # Cancel tasks
        if self._input_task:
            self._input_task.cancel()
            try:
                await self._input_task
            except asyncio.CancelledError:
                pass
        
        if self._output_task:
            self._output_task.cancel()
            try:
                await self._output_task
            except asyncio.CancelledError:
                pass
        
        # Close session context
        self._session_context = None
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
        
        # Terminate PyAudio
        if self.audio_input:
            self.audio_input.terminate()
            self.audio_input = None
        
        if self.audio_output:
            self.audio_output.terminate()
            self.audio_output = None
        
        logger.success("Live voice session stopped")
    
    async def _process_input_audio(self):
        """Continuously capture and send audio to Gemini"""
        logger.info("Starting input audio processing...")
        
        try:
            logger.info("Input audio processing ready")
            
            while self.is_active and self.input_stream:
                # Wait for session context to be available (handles reconnections)
                if not self._session_context:
                    await asyncio.sleep(0.1)
                    continue
                
                try:
                    # Read audio chunk from microphone
                    audio_data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Calculate audio level for visualization
                    if self.on_audio_level:
                        import struct
                        samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
                        level = max(abs(s) for s in samples) / 32768.0
                        # Call async callback properly
                        if asyncio.iscoroutinefunction(self.on_audio_level):
                            await self.on_audio_level(level)
                        else:
                            self.on_audio_level(level)
                    
                    # Send to Gemini using correct API
                    if self._session_context:
                        await self._session_context.send_realtime_input(
                            audio=types.Blob(
                                data=audio_data,
                                mime_type=f"audio/pcm;rate={self.sample_rate}"
                            )
                        )
                    
                    # Small delay to prevent overwhelming the API
                    await asyncio.sleep(0.01)
                    
                except Exception as send_error:
                    # If send fails (e.g., session reconnecting), wait and retry
                    error_msg = str(send_error)
                    if "sent 1000" in error_msg or "received 1000" in error_msg or "session" in error_msg.lower():
                        logger.debug("Session reconnecting, pausing input...")
                        self._session_context = None  # Clear context to wait for reconnection
                        await asyncio.sleep(0.5)
                    else:
                        raise  # Re-raise unexpected errors
                
        except asyncio.CancelledError:
            logger.info("Input audio processing cancelled")
        except Exception as e:
            logger.error(f"Error in input audio processing: {e}", exc_info=True)
            if self.on_error:
                self.on_error(f"Input audio error: {str(e)}")
    
    async def _process_output_audio(self):
        """Continuously receive and play audio from Gemini"""
        logger.info("Starting output audio processing...")
        
        # Keep the connection alive and reuse the same session across turns
        while self.is_active:
            try:
                # Enter the async context manager for the session
                async with self.session as session:
                    self._session_context = session
                    logger.info("Session context established")
                    
                    # Continuously listen for server messages across turns without reconnecting
                    while self.is_active:
                        response_active = False
                        
                        # Drain messages for the current turn
                        async for response in session.receive():
                            if not self.is_active:
                                break
                            
                            # Debug: Log response structure
                            logger.debug(f"Received response type: {type(response)}")
                            logger.debug(f"Response attributes: {dir(response)}")
                            
                            # Check for server content
                            if response.server_content:
                                server_content = response.server_content
                                
                                # Check for response start
                                if server_content.model_turn and not response_active:
                                    response_active = True
                                    if self.on_response_start:
                                        self.on_response_start()
                                    logger.debug("Response started")
                                
                                # Extract and play audio from model turn parts
                                if server_content.model_turn and server_content.model_turn.parts:
                                    for part in server_content.model_turn.parts:
                                        # Check for inline audio data
                                        if hasattr(part, 'inline_data') and part.inline_data:
                                            if part.inline_data.mime_type.startswith('audio/'):
                                                audio_bytes = part.inline_data.data
                                                logger.debug(f"Received audio chunk: {len(audio_bytes)} bytes")
                                                
                                                # Play through speakers
                                                if self.output_stream:
                                                    try:
                                                        self.output_stream.write(audio_bytes)
                                                    except Exception as play_error:
                                                        logger.error(f"Error playing audio: {play_error}")
                                                
                                                # Notify callback
                                                if self.on_response_chunk:
                                                    self.on_response_chunk(audio_bytes)
                                
                                # Also check for audio directly in server_content (alternative format)
                                if hasattr(server_content, 'audio') and server_content.audio:
                                    audio_bytes = server_content.audio
                                    logger.debug(f"Received direct audio: {len(audio_bytes)} bytes")
                                    
                                    if not response_active:
                                        response_active = True
                                        if self.on_response_start:
                                            self.on_response_start()
                                    
                                    # Play through speakers
                                    if self.output_stream:
                                        try:
                                            self.output_stream.write(audio_bytes)
                                        except Exception as play_error:
                                            logger.error(f"Error playing audio: {play_error}")
                                    
                                    # Notify callback
                                    if self.on_response_chunk:
                                        self.on_response_chunk(audio_bytes)
                                
                                # Check for response end (but continue listening for next turn)
                                if server_content.turn_complete and response_active:
                                    response_active = False
                                    if self.on_response_end:
                                        self.on_response_end()
                                    logger.debug("Response ended, ready for next input")
                                    # Do not break; allow the async for to finish naturally for this turn
                            
                            # Log other response types for debugging
                            else:
                                logger.debug(f"Received response without server_content: {type(response)}")
                        
                        # Turn finished (receive() iterator completed). Loop to wait for the next turn on the same session.
                        if not self.is_active:
                            break
                        await asyncio.sleep(0.01)
            
            except asyncio.CancelledError:
                logger.info("Output audio processing cancelled")
                break
            except Exception as e:
                # Check if it's a WebSocket close error (normal closure)
                error_msg = str(e)
                if "sent 1000" in error_msg or "received 1000" in error_msg:
                    if self.is_active:
                        logger.info("Session closed, reconnecting...")
                        await asyncio.sleep(0.5)
                        # Recreate the session connection
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
                        self.session = self.client.aio.live.connect(model=self.model, config=config)
                        continue
                    else:
                        logger.info("WebSocket closed, session stopping")
                        break
                else:
                    logger.error(f"Error in output audio processing: {e}", exc_info=True)
                    if self.on_error:
                        self.on_error(f"Output audio error: {str(e)}")
                    break
    
    async def send_text(self, text: str):
        """Send text input to the session (for hybrid text/voice)"""
        if not self.is_active or not self._session_context:
            logger.warning("Cannot send text: session not active")
            return
        
        try:
            # Use client content API for text per official examples
            await self._session_context.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=text)])
            )
            logger.info(f"Sent text to session: {text}")
        except Exception as e:
            logger.error(f"Error sending text: {e}")
            if self.on_error:
                self.on_error(f"Text send error: {str(e)}")


class LiveVoiceManager:
    """
    High-level manager for Live Voice sessions
    Handles session lifecycle and state management
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.current_session: Optional[LiveVoiceSession] = None
        self.is_live_mode = False
        
        # Callbacks
        self.on_state_change: Optional[Callable[[str], None]] = None
        self.on_audio_level: Optional[Callable[[float], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    async def start_live_mode(self, system_instruction: str = None):
        """Start live voice mode"""
        if self.is_live_mode:
            logger.warning("Live mode already active")
            return
        
        try:
            logger.info("Starting live voice mode...")
            
            # Create new session
            self.current_session = LiveVoiceSession(self.api_key)
            
            # Set up callbacks
            self.current_session.on_response_start = lambda: self._notify_state("responding")
            self.current_session.on_response_end = lambda: self._notify_state("listening")
            self.current_session.on_audio_level = self.on_audio_level
            self.current_session.on_error = self._handle_error
            
            # Start session
            instruction = system_instruction or "You are PRISM, a helpful AI assistant. Respond naturally and conversationally in a friendly tone."
            await self.current_session.start(system_instruction=instruction)
            
            self.is_live_mode = True
            self._notify_state("listening")
            
            logger.success("Live voice mode started")
            
        except Exception as e:
            logger.error(f"Failed to start live mode: {e}")
            self.is_live_mode = False
            if self.on_error:
                self.on_error(str(e))
            raise
    
    async def stop_live_mode(self):
        """Stop live voice mode"""
        if not self.is_live_mode:
            return
        
        logger.info("Stopping live voice mode...")
        
        self.is_live_mode = False
        
        if self.current_session:
            await self.current_session.stop()
            self.current_session = None
        
        self._notify_state("idle")
        logger.success("Live voice mode stopped")
    
    async def send_text(self, text: str):
        """Send text to current live session"""
        if self.current_session and self.is_live_mode:
            await self.current_session.send_text(text)
    
    def _notify_state(self, state: str):
        """Notify state change"""
        if self.on_state_change:
            self.on_state_change(state)
    
    def _handle_error(self, error: str):
        """Handle session error"""
        logger.error(f"Live session error: {error}")
        if self.on_error:
            self.on_error(error)
        
        # Stop live mode on error
        asyncio.create_task(self.stop_live_mode())
