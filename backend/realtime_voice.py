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
        self.chunk_size = 512  # Smaller chunks for lower latency
        self.format = pyaudio.paInt16
        
        # Session state
        self.is_active = False
        self.send_task = None
        self.receive_task = None
        
        # Callbacks
        self.on_audio_received: Optional[Callable] = None
        self.on_text_received: Optional[Callable] = None
        self.on_user_speech: Optional[Callable] = None
        self.on_function_call: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        
    def _get_session_config(self):
        """Get configuration for Gemini Live session"""
        
        tools = [
            {
                "function_declarations": [
                    {
                        "name": "open_application",
                        "description": "Open an application on the user's computer",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the application to open (e.g., 'notepad', 'chrome', 'calculator')"
                                }
                            },
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "open_file",
                        "description": "Open a file on the user's computer",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to the file"
                                }
                            },
                            "required": ["path"]
                        }
                    },
                    {
                        "name": "system_command",
                        "description": "Execute a system command",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The command to execute"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                ]
            }
        ]
        
        return {
            "response_modalities": ["AUDIO"],
            "tools": tools,
            "system_instruction": """You are PRISM, a personal AI assistant with real-time voice interaction capabilities.

Key guidelines:
- Respond naturally and conversationally in voice
- Keep responses concise (1-2 sentences typically)
- Be helpful, friendly, and efficient
- Never mention technical details
- Use the provided tools to execute user requests

When the user asks you to perform actions:
1. Acknowledge their request naturally
2. Call the appropriate function tool
3. The system will execute it and provide feedback

Examples:
- "Open Chrome" -> Call open_application with name="chrome" and say "Opening Chrome for you"
- "Search for Python tutorials" -> Call web_search with query="Python tutorials" and say "Searching for Python tutorials"
- "Open my documents folder" -> Call open_file with appropriate path""",
            "generation_config": {
                "temperature": 0.8,
                "max_output_tokens": 1024,
            }
        }
    
    async def start_audio_streams(self):
        """Initialize audio input/output streams"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Input stream (microphone) - 16kHz for Gemini input
            self.input_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.input_sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=None
            )
            
            # Start the input stream
            if not self.input_stream.is_active():
                self.input_stream.start_stream()
            
            # Output stream (speakers) - 24kHz for Gemini output
            self.output_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.output_sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Start the output stream
            if not self.output_stream.is_active():
                self.output_stream.start_stream()
            
            logger.success("Audio streams initialized and started")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio streams: {e}")
            raise
    
    async def _send_audio_loop(self):
        """Continuously send audio from microphone to Gemini"""
        logger.info("Starting audio send loop...")
        
        chunk_count = 0
        last_audio_time = asyncio.get_event_loop().time()
        
        try:
            while self.is_active and self.session:
                try:
                    # Read audio chunk from microphone
                    if not self.input_stream or not self.input_stream.is_active():
                        logger.warning("Input stream not active, waiting...")
                        await asyncio.sleep(0.1)
                        continue
                    
                    audio_data = self.input_stream.read(
                        self.chunk_size, 
                        exception_on_overflow=False
                    )
                    
                    current_time = asyncio.get_event_loop().time()
                    
                    # If audio stream was paused for >1 second, send stream end signal
                    if current_time - last_audio_time > 1.5:
                        logger.info("Audio stream pause detected, sending stream end signal")
                        await self.session.send_realtime_input(audio_stream_end=True)
                    
                    last_audio_time = current_time
                    
                    # Send raw PCM data directly to Gemini
                    await self.session.send_realtime_input(
                        audio=types.Blob(
                            data=audio_data,
                            mime_type=f"audio/pcm;rate={self.input_sample_rate}"
                        )
                    )
                    
                    chunk_count += 1
                    if chunk_count % 100 == 1:
                        logger.info(f"Sent {chunk_count} audio chunks so far...")
                    
                    # Small delay to prevent overwhelming the API
                    await asyncio.sleep(0.01)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    if self.is_active:
                        logger.error(f"Error in send loop: {e}")
                        await asyncio.sleep(0.1)
                    else:
                        break
                    
        except asyncio.CancelledError:
            logger.info("Send loop cancelled")
        except Exception as e:
            logger.error(f"Send loop failed: {e}")
        finally:
            # Send final stream end signal
            try:
                if self.session:
                    await self.session.send_realtime_input(audio_stream_end=True)
            except:
                pass
            logger.info("Audio send loop stopped")
    
    async def _receive_audio_loop(self):
        """Continuously receive audio from Gemini and play it"""
        logger.info("Starting audio receive loop...")
        
        try:
            if not self.session:
                logger.error("No session available for receive loop")
                return
            
            logger.info("Starting to receive from session...")
            response_count = 0
            
            async for response in self.session.receive():
                response_count += 1
                if response_count % 10 == 1:
                    logger.info(f"Received {response_count} responses so far...")
                
                # Log all response attributes for debugging
                if response_count <= 3:
                    attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                    logger.info(f"Response #{response_count} attributes: {attrs}")
                    for attr in ['data', 'text', 'server_content', 'tool_call']:
                        if hasattr(response, attr):
                            val = getattr(response, attr)
                            logger.info(f"  {attr} = {val if val is None or isinstance(val, (str, int, bool)) else type(val).__name__}")
                
                if not self.is_active:
                    logger.info("Session no longer active, stopping receive loop")
                    break
                
                try:
                    # Check for direct audio data (native audio models)
                    if hasattr(response, 'data') and response.data is not None:
                        audio_data = response.data
                        logger.info(f"Received audio data: {len(audio_data)} bytes")
                        
                        if self.output_stream and self.output_stream.is_active():
                            self.output_stream.write(audio_data)
                        
                        if self.on_audio_received:
                            await self.on_audio_received(audio_data)
                    
                    # Check for text response (for debugging or text mode)
                    if hasattr(response, 'text') and response.text is not None:
                        logger.info(f"Received text: {response.text}")
                        if self.on_text_received:
                            await self.on_text_received(response.text)
                    
                    # Handle server content structure
                    if hasattr(response, 'server_content') and response.server_content:
                        server_content = response.server_content
                        
                        # Handle interruptions (VAD)
                        if hasattr(server_content, 'interrupted') and server_content.interrupted:
                            logger.info("Generation interrupted by user speech")
                            # Stop any ongoing audio playback
                            if self.output_stream and self.output_stream.is_active():
                                # Clear the output buffer
                                try:
                                    self.output_stream.stop_stream()
                                    self.output_stream.start_stream()
                                except:
                                    pass
                        
                        # Handle turn complete with user speech transcription
                        if hasattr(server_content, 'turn_complete') and server_content.turn_complete:
                            if hasattr(server_content, 'user_turn') and server_content.user_turn:
                                user_turn = server_content.user_turn
                                if hasattr(user_turn, 'parts') and user_turn.parts:
                                    for part in user_turn.parts:
                                        if hasattr(part, 'text') and part.text:
                                            logger.info(f"User said: {part.text}")
                                            if self.on_user_speech:
                                                await self.on_user_speech(part.text)
                        
                        # Handle model turn (assistant response)
                        if hasattr(server_content, 'model_turn') and server_content.model_turn:
                            model_turn = server_content.model_turn
                            if hasattr(model_turn, 'parts') and model_turn.parts:
                                for part in model_turn.parts:
                                    # Handle inline audio data (alternative format)
                                    if hasattr(part, 'inline_data') and part.inline_data:
                                        if hasattr(part.inline_data, 'data') and part.inline_data.data:
                                            audio_data = part.inline_data.data
                                            logger.info(f"Playing inline audio: {len(audio_data)} bytes")
                                            
                                            if self.output_stream and self.output_stream.is_active():
                                                self.output_stream.write(audio_data)
                                            
                                            if self.on_audio_received:
                                                await self.on_audio_received(audio_data)
                                    
                                    # Handle text response
                                    if hasattr(part, 'text') and part.text:
                                        logger.info(f"Assistant: {part.text}")
                                        if self.on_text_received:
                                            await self.on_text_received(part.text)
                                    
                                    # Handle function calls
                                    if hasattr(part, 'function_call') and part.function_call:
                                        func_call = part.function_call
                                        logger.info(f"Function call: {func_call.name} with args: {func_call.args}")
                                        if self.on_function_call:
                                            await self.on_function_call({
                                                "id": func_call.id if hasattr(func_call, 'id') else None,
                                                "name": func_call.name,
                                                "args": dict(func_call.args) if func_call.args else {}
                                            })
                    
                    # Handle tool calls (alternative structure)
                    if hasattr(response, 'tool_call') and response.tool_call:
                        tool_call = response.tool_call
                        if hasattr(tool_call, 'function_calls') and tool_call.function_calls:
                            for fc in tool_call.function_calls:
                                logger.info(f"Tool call: {fc.name} with args: {fc.args}")
                                if self.on_function_call:
                                    await self.on_function_call({
                                        "id": fc.id if hasattr(fc, 'id') else None,
                                        "name": fc.name,
                                        "args": dict(fc.args) if fc.args else {}
                                    })
                    
                except Exception as e:
                    logger.error(f"Error processing response: {e}", exc_info=True)
                    continue
            
            logger.info("Receive loop iterator completed")
                                        
        except asyncio.CancelledError:
            logger.info("Receive loop cancelled")
        except Exception as e:
            if self.is_active:
                logger.error(f"Receive loop failed: {e}", exc_info=True)
            else:
                logger.info(f"Receive loop stopped (session inactive): {e}")
        finally:
            logger.info("Audio receive loop stopped")
    
    async def start_session(self):
        """Start the real-time voice session with continuous bidirectional streaming"""
        try:
            if not GENAI_AVAILABLE:
                logger.error("Google GenAI library not available")
                return False
            
            logger.info("Starting Gemini Live API session...")
            
            # Initialize client
            self.client = genai.Client(api_key=config.ai.gemini_api_key)
            
            # Initialize audio streams
            await self.start_audio_streams()
            
            # Use native audio model for best quality
            model = "gemini-2.5-flash-native-audio-preview-09-2025"
            config_dict = self._get_session_config()
            
            logger.info(f"Connecting to model: {model}")
            logger.info(f"Config: {config_dict}")
            
            # Connect to Live API using proper context manager
            context_manager = self.client.aio.live.connect(model=model, config=config_dict)
            self.session = await context_manager.__aenter__()
            self._context_manager = context_manager
            
            # Wait briefly for connection to stabilize
            await asyncio.sleep(0.5)
            
            self.is_active = True
            logger.success("Live API session connected and ready")
            
            # Start bidirectional streaming tasks (run in background)
            self.send_task = asyncio.create_task(self._send_audio_loop())
            self.receive_task = asyncio.create_task(self._receive_audio_loop())
            
            # Send initial greeting to trigger the conversation
            await asyncio.sleep(0.5)
            logger.info("Sending initial greeting to start conversation")
            await self.session.send_client_content(
                turns=[{"role": "user", "parts": [{"text": "Hello"}]}],
                turn_complete=True
            )
            
            if self.on_state_change:
                await self.on_state_change("active")
            
            logger.info("Real-time voice session fully initialized - listening for audio")
            
            # Add callbacks to monitor task completion
            self.send_task.add_done_callback(lambda t: self._on_task_done("send", t))
            self.receive_task.add_done_callback(lambda t: self._on_task_done("receive", t))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
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
