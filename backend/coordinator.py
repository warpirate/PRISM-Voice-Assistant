"""
Central Coordination Hub
Main orchestrator for all PRISM subsystems
"""

import asyncio
import signal
from enum import Enum
from typing import Optional, Callable, Dict, Any
from loguru import logger
from datetime import datetime

from backend.config import config
from backend.voice_pipeline import VoicePipeline
from backend.ai_engine import AIEngine
from backend.system_control import SystemControl
from backend.memory_system import MemorySystem
from backend.websocket_bridge import WebSocketBridge
from backend.realtime_voice import RealtimeVoiceSession


class SystemState(Enum):
    """System operational states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    EXECUTING = "executing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class PRISMCoordinator:
    """
    Central coordination hub that manages all PRISM components
    and handles communication between modules
    """

    def __init__(self):
        self.state = SystemState.IDLE
        self.running = False
        self.processing_lock = asyncio.Lock()  # Prevent concurrent processing
        
        # Initialize subsystems
        self.voice = VoicePipeline()
        self.ai = AIEngine()
        self.system_control = SystemControl()
        self.memory = MemorySystem()
        self.websocket = WebSocketBridge()
        self.realtime_voice: Optional[RealtimeVoiceSession] = None
        
        # Voice mode
        self.realtime_mode = False  # Toggle between traditional and real-time voice
        
        # Event callbacks for UI
        self.state_callbacks: Dict[SystemState, list] = {state: [] for state in SystemState}
        self.message_callback: Optional[Callable] = None
        
        # Conversation context
        self.current_conversation_id: Optional[str] = None
        self.conversation_context: list = []
        
        logger.info("PRISM Coordinator initialized")

    async def start(self):
        """Start all subsystems and begin operation"""
        logger.info("Starting PRISM system...")
        self.running = True
        
        try:
            # Initialize all subsystems
            await self.voice.initialize()
            await self.ai.initialize()
            await self.memory.initialize()
            await self.websocket.start()
            
            # Register callbacks
            self.voice.on_wake_word = self._on_wake_word_detected
            self.voice.on_speech_recognized = self._on_speech_recognized
            self.voice.on_audio_level = self._on_audio_level
            self.websocket.register_callback(self._handle_ui_message)
            
            # Manual activation only - no wake word detection
            self._set_state(SystemState.IDLE)
            logger.success("PRISM system started successfully")
            
            # Keep running
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Error starting PRISM: {e}")
            self._set_state(SystemState.ERROR)
            raise

    async def _main_loop(self):
        """Main event loop"""
        while self.running:
            await asyncio.sleep(0.1)

    async def shutdown(self):
        """Gracefully shutdown all subsystems"""
        logger.info("Shutting down PRISM system...")
        self.running = False
        self._set_state(SystemState.SHUTDOWN)
        
        try:
            await self.voice.shutdown()
            await self.ai.shutdown()
            await self.memory.shutdown()
            await self.websocket.shutdown()
            logger.success("PRISM shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    # ==================== Activation Methods ====================

    async def activate_voice(self):
        """Manually activate voice input"""
        logger.info("Voice activation triggered manually")
        await self._on_wake_word_detected()

    async def process_text_input(self, text: str):
        """Process text input directly (without voice)"""
        logger.info(f"Processing text input: {text}")
        
        # Check if already processing
        if self.processing_lock.locked():
            logger.warning("Already processing a message, queuing this one")
            # Queue it for later or notify user
            self._send_message({
                "type": "info",
                "message": "Please wait, still processing previous request..."
            })
            return
        
        logger.info(f"Acquiring processing lock...")
        async with self.processing_lock:
            logger.info(f"Processing lock acquired, processing input: {text}")
            try:
                await self._process_user_input(text, input_method="text")
                logger.info(f"Completed processing input: {text}")
            except Exception as e:
                logger.error(f"Error in process_text_input: {e}", exc_info=True)
                raise
            finally:
                logger.info(f"Processing lock released for: {text}")

    async def execute_hotkey_action(self, hotkey: str):
        """Handle keyboard shortcut activation"""
        logger.info(f"Hotkey activated: {hotkey}")
        if hotkey == config.ui.activation_hotkey:
            await self.activate_voice()

    async def _handle_ui_message(self, message: Dict[str, Any]):
        """Handle messages from UI via WebSocket"""
        msg_type = message.get("type")
        logger.info(f"Received UI message: {msg_type} - {message}")
        
        try:
            if msg_type == "activate_voice":
                await self.activate_voice()
            
            elif msg_type == "process_text":
                text = message.get("text")
                if text:
                    logger.info(f"Forwarding text to AI: {text}")
                    await self.process_text_input(text)
                else:
                    logger.warning("Received empty text in process_text message")
            
            elif msg_type == "clear_conversation":
                self.clear_conversation_context()
                self._send_message({
                    "type": "conversation_cleared",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "get_history":
                history = await self.get_conversation_history()
                self._send_message({
                    "type": "conversation_history",
                    "history": history
                })
            
            elif msg_type == "ping":
                self._send_message({"type": "pong"})
            
            elif msg_type == "toggle_realtime_voice":
                await self.toggle_realtime_voice()
            
            else:
                logger.warning(f"Unknown message type from UI: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling UI message: {e}", exc_info=True)
            self._send_message({
                "type": "error",
                "message": str(e)
            })

    # ==================== Real-time Voice Methods ====================
    
    async def toggle_realtime_voice(self):
        """Toggle real-time voice conversation mode"""
        if self.realtime_mode:
            await self.stop_realtime_voice()
        else:
            await self.start_realtime_voice()
    
    async def start_realtime_voice(self):
        """Start real-time voice conversation with Gemini Live API"""
        if self.realtime_mode:
            logger.warning("Real-time voice already active")
            return
        
        try:
            logger.info("Starting real-time voice mode...")
            
            # Create new session
            self.realtime_voice = RealtimeVoiceSession()
            
            # Set up callbacks
            self.realtime_voice.on_text_received = self._on_realtime_text_received
            self.realtime_voice.on_user_speech = self._on_realtime_user_speech
            self.realtime_voice.on_function_call = self._on_realtime_function_call
            self.realtime_voice.on_state_change = self._on_realtime_state_change
            
            # Start session
            success = await self.realtime_voice.start_session()
            
            if success:
                self.realtime_mode = True
                self._set_state(SystemState.LISTENING)
                
                self._send_message({
                    "type": "realtime_voice_started",
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.success("Real-time voice mode started - continuous streaming active")
            else:
                self._send_message({
                    "type": "error",
                    "message": "Failed to initialize real-time voice session"
                })
            
        except Exception as e:
            logger.error(f"Failed to start real-time voice: {e}", exc_info=True)
            self._send_message({
                "type": "error",
                "message": f"Failed to start real-time voice: {str(e)}"
            })
    
    async def stop_realtime_voice(self):
        """Stop real-time voice conversation"""
        if not self.realtime_mode or not self.realtime_voice:
            return
        
        try:
            logger.info("Stopping real-time voice mode...")
            
            await self.realtime_voice.stop_session()
            self.realtime_voice = None
            self.realtime_mode = False
            
            self._set_state(SystemState.IDLE)
            
            self._send_message({
                "type": "realtime_voice_stopped",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.success("Real-time voice mode stopped")
            
        except Exception as e:
            logger.error(f"Error stopping real-time voice: {e}", exc_info=True)
    
    async def _on_realtime_user_speech(self, text: str):
        """Handle user speech transcription from real-time voice"""
        logger.info(f"User said: {text}")
        
        self._send_message({
            "type": "user_message",
            "content": text,
            "timestamp": datetime.now().isoformat(),
            "realtime": True
        })
    
    async def _on_realtime_text_received(self, text: str):
        """Handle assistant text response from real-time voice"""
        logger.info(f"Assistant said: {text}")
        
        self._send_message({
            "type": "assistant_message",
            "content": text,
            "timestamp": datetime.now().isoformat(),
            "realtime": True
        })
    
    async def _on_realtime_function_call(self, function_call: Dict[str, Any]):
        """Handle function call from real-time voice"""
        logger.info(f"Function call received: {function_call}")
        
        try:
            func_id = function_call.get("id")
            func_name = function_call.get("name")
            func_args = function_call.get("args", {})
            
            if not func_id:
                logger.error("Function call missing ID - cannot send response")
                return
            
            # Map function calls to action format
            action = {
                "type": func_name,
                "parameters": func_args
            }
            
            logger.info(f"Executing action from real-time voice: {action}")
            
            # Execute the action
            result = await self.system_control.execute_action(action)
            
            logger.info(f"Action result: {result}")
            
            # Send result back to Gemini session
            if self.realtime_voice:
                response_data = {
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "result": "ok" if result.get("success", False) else "error"
                }
                await self.realtime_voice.send_function_response(func_id, func_name, response_data)
            
            # Notify UI if action failed
            if not result.get("success", False):
                self._send_message({
                    "type": "error",
                    "message": result.get("message", "Action failed"),
                    "realtime": True
                })
            
        except Exception as e:
            logger.error(f"Error executing function call: {e}", exc_info=True)
            
            # Send error response back to Gemini
            if self.realtime_voice and func_id:
                await self.realtime_voice.send_function_response(
                    func_id,
                    func_name,
                    {"success": False, "error": str(e), "result": "error"}
                )
            
            self._send_message({
                "type": "error",
                "message": f"Failed to execute action: {str(e)}",
                "realtime": True
            })
    
    async def _on_realtime_state_change(self, state: str):
        """Handle real-time voice state changes"""
        logger.info(f"Real-time voice state: {state}")
        
        if state == "active":
            self._set_state(SystemState.LISTENING)
        elif state == "inactive":
            self._set_state(SystemState.IDLE)

    # ==================== Voice Event Handlers ====================

    async def _on_wake_word_detected(self):
        """Handle wake word detection"""
        logger.info("Wake word detected!")
        self._set_state(SystemState.LISTENING)
        
        # Notify UI
        self._send_message({
            "type": "listening_started",
            "timestamp": datetime.now().isoformat()
        })
        
        # Play activation sound (non-blocking)
        if config.voice.enable_voice_feedback:
            asyncio.create_task(self.voice.play_activation_sound())
        
        # Start listening for command
        await self.voice.start_listening()

    async def _on_speech_recognized(self, text: str):
        """Handle recognized speech"""
        if not text:
            logger.warning("Empty text received from speech recognition")
            self._set_state(SystemState.IDLE)
            self._send_message({
                "type": "listening_timeout",
                "message": "No speech detected",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        logger.info(f"Speech recognized: {text}")
        await self._process_user_input(text, input_method="voice")

    async def _on_audio_level(self, level: float):
        """Handle audio level updates for visualization"""
        # Send to UI for waveform visualization
        if self.message_callback:
            self.message_callback({
                "type": "audio_level",
                "level": level
            })

    # ==================== Core Processing ====================

    async def _process_user_input(self, user_input: str, input_method: str = "voice"):
        """
        Process user input through the AI engine and execute actions
        """
        self._set_state(SystemState.PROCESSING)
        
        try:
            # Store user message
            if config.privacy.store_conversations:
                await self.memory.store_interaction({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat(),
                    "input_method": input_method
                })
            
            # Add to conversation context
            self.conversation_context.append({
                "role": "user",
                "content": user_input
            })
            
            # Send to UI
            self._send_message({
                "type": "user_message",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # Get AI response
            response = await self.ai.process_input(
                user_input=user_input,
                conversation_history=self.conversation_context,
                system_context=await self._get_system_context()
            )
            
            # Add response to context
            self.conversation_context.append({
                "role": "assistant",
                "content": response.text
            })
            
            # Trim context to prevent unbounded growth
            self._trim_conversation_context()
            
            # Store assistant response
            if config.privacy.store_conversations:
                await self.memory.store_interaction({
                    "role": "assistant",
                    "content": response.text,
                    "timestamp": datetime.now().isoformat(),
                    "requires_action": response.requires_action
                })
            
            # Handle response
            await self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            error_message = "I encountered an error processing your request. Please try again."
            await self._deliver_response(error_message)
            self._set_state(SystemState.ERROR)
            # Return to idle after brief delay
            await asyncio.sleep(2)
            self._set_state(SystemState.IDLE)

    async def _handle_response(self, response):
        """Handle AI response (text output and/or actions)"""
        try:
            self._set_state(SystemState.RESPONDING)
            
            # Deliver text response (non-blocking voice)
            await self._deliver_response(response.text, wait_for_speech=False)
            
            # Execute actions if required
            if response.requires_action and response.actions:
                await self._execute_actions(response.actions)
        finally:
            # Always return to idle, even if there's an error
            self._set_state(SystemState.IDLE)

    async def _deliver_response(self, text: str, wait_for_speech: bool = True):
        """Deliver response through voice and UI"""
        # Send to UI
        self._send_message({
            "type": "assistant_message",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Speak response if voice feedback enabled
        if config.voice.enable_voice_feedback:
            if wait_for_speech:
                await self.voice.speak(text)
            else:
                # Fire and forget - don't block action execution
                asyncio.create_task(self.voice.speak(text))

    async def _execute_actions(self, actions: list):
        """Execute system actions"""
        if not actions:
            logger.warning("No actions to execute")
            return
        
        self._set_state(SystemState.EXECUTING)
        logger.info(f"Executing {len(actions)} action(s): {[a.get('type') for a in actions]}")
        
        for action in actions:
            try:
                action_type = action.get('type', 'unknown')
                logger.info(f"Executing action: {action_type} with parameters: {action.get('parameters', {})}")
                
                result = await self.system_control.execute_action(action)
                
                logger.info(f"Action result: success={result.get('success')}, message={result.get('message')}")
                
                # Notify user of action result if requested
                if result.get("notify", False):
                    await self._deliver_response(result.get("message", "Action completed"))
                elif not result.get("success", False):
                    # Always notify on failure
                    await self._deliver_response(result.get("message", "Action failed"))
                    
            except Exception as e:
                logger.error(f"Error executing action {action.get('type', 'unknown')}: {e}", exc_info=True)
                await self._deliver_response(f"I couldn't complete that action: {str(e)}")

    async def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context for AI"""
        return {
            "current_directory": self.system_control.get_current_directory(),
            "running_applications": self.system_control.get_running_applications(),
            "system_info": self.system_control.get_system_info(),
            "recent_memory": await self.memory.get_recent_interactions(limit=5)
        }

    # ==================== State Management ====================

    def _set_state(self, new_state: SystemState):
        """Update system state and notify callbacks"""
        old_state = self.state
        self.state = new_state
        logger.debug(f"State transition: {old_state.value} -> {new_state.value}")
        
        # Trigger callbacks
        for callback in self.state_callbacks.get(new_state, []):
            try:
                callback(new_state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
        
        # Send to UI
        self._send_message({
            "type": "state_change",
            "state": new_state.value,
            "timestamp": datetime.now().isoformat()
        })

    def register_state_callback(self, state: SystemState, callback: Callable):
        """Register callback for state changes"""
        self.state_callbacks[state].append(callback)

    def register_message_callback(self, callback: Callable):
        """Register callback for messages to UI"""
        self.message_callback = callback

    def _send_message(self, message: Dict[str, Any]):
        """Send message to UI"""
        # Send via WebSocket
        asyncio.create_task(self.websocket.send_to_ui(message))
        
        # Also call legacy callback if set
        if self.message_callback:
            try:
                self.message_callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")

    # ==================== Context Management ====================

    def clear_conversation_context(self):
        """Clear current conversation context"""
        self.conversation_context = []
        self.current_conversation_id = None
        logger.info("Conversation context cleared")
    
    def _trim_conversation_context(self, max_messages: int = 20):
        """Trim conversation context to prevent unbounded growth"""
        if len(self.conversation_context) > max_messages:
            # Keep the most recent messages
            self.conversation_context = self.conversation_context[-max_messages:]
            logger.debug(f"Trimmed conversation context to {max_messages} messages")

    async def get_conversation_history(self, limit: int = 20):
        """Get recent conversation history"""
        return await self.memory.get_recent_interactions(limit=limit)


# Global coordinator instance
coordinator = PRISMCoordinator()
