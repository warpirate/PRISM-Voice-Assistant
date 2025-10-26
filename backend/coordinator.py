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
        
        # Initialize subsystems
        self.voice = VoicePipeline()
        self.ai = AIEngine()
        self.system_control = SystemControl()
        self.memory = MemorySystem()
        self.websocket = WebSocketBridge()
        
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
        await self._process_user_input(text, input_method="text")

    async def execute_hotkey_action(self, hotkey: str):
        """Handle keyboard shortcut activation"""
        logger.info(f"Hotkey activated: {hotkey}")
        if hotkey == config.ui.activation_hotkey:
            await self.activate_voice()

    async def _handle_ui_message(self, message: Dict[str, Any]):
        """Handle messages from UI via WebSocket"""
        msg_type = message.get("type")
        
        try:
            if msg_type == "activate_voice":
                await self.activate_voice()
            
            elif msg_type == "process_text":
                text = message.get("text")
                if text:
                    await self.process_text_input(text)
            
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
            
            else:
                logger.warning(f"Unknown message type from UI: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling UI message: {e}")
            self._send_message({
                "type": "error",
                "message": str(e)
            })

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
            logger.error(f"Error processing input: {e}")
            error_message = "I encountered an error processing your request. Please try again."
            await self._deliver_response(error_message)
            self._set_state(SystemState.ERROR)

    async def _handle_response(self, response):
        """Handle AI response (text output and/or actions)"""
        self._set_state(SystemState.RESPONDING)
        
        # Deliver text response
        await self._deliver_response(response.text)
        
        # Execute actions if required
        if response.requires_action and response.actions:
            await self._execute_actions(response.actions)
        
        # Return to idle
        self._set_state(SystemState.IDLE)

    async def _deliver_response(self, text: str):
        """Deliver response through voice and UI"""
        # Send to UI
        self._send_message({
            "type": "assistant_message",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Speak response if voice feedback enabled
        if config.voice.enable_voice_feedback:
            await self.voice.speak(text)

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
                
                # Notify user of action result
                if result.get("notify", False):
                    await self._deliver_response(result.get("message", "Action completed"))
                    
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

    async def get_conversation_history(self, limit: int = 20):
        """Get recent conversation history"""
        return await self.memory.get_recent_interactions(limit=limit)


# Global coordinator instance
coordinator = PRISMCoordinator()
