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
from backend.agents import (
    AgentRegistry,
    AgentCoordinator,
    PersonalFileAgent,
    PersonalWebAgent,
    PersonalProductivityAgent
)
from backend.live_voice import LiveVoiceManager
from backend.core.interaction_service import InteractionService


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
        self.memory = MemorySystem()
        self.websocket = WebSocketBridge()
        self.system_control = SystemControl()
        
        # Initialize interaction service (core business logic)
        self.interaction_service: Optional[InteractionService] = None
        
        # Initialize agent system
        self.agent_registry = AgentRegistry()
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.agents_enabled = True  # Toggle for agent-based processing
        
        # Initialize Live Voice manager
        self.live_voice: Optional[LiveVoiceManager] = None
        self.live_voice_enabled = False  # Toggle for Live Voice mode
        
        # Event callbacks for UI
        self.state_callbacks: Dict[SystemState, list] = {state: [] for state in SystemState}
        self.message_callback: Optional[Callable] = None
        
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
            
            # Initialize agent system
            await self._initialize_agents()
            
            # Initialize interaction service
            self.interaction_service = InteractionService(
                ai_engine=self.ai,
                memory_system=self.memory,
                voice_pipeline=self.voice,
                system_control=self.system_control,
                ui_message_sender=self._send_message
            )
            
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
            # Shutdown agents first
            if self.agent_registry:
                await self.agent_registry.shutdown_all()
            
            
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
        self._set_state(SystemState.PROCESSING)
        
        try:
            await self.interaction_service.process_text_input(text)
        except Exception as e:
            logger.error(f"Error in process_text_input: {e}", exc_info=True)
            self._set_state(SystemState.ERROR)
            # Return to idle after brief delay
            await asyncio.sleep(1.0)
        finally:
            self._set_state(SystemState.IDLE)

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
                self.interaction_service.clear_conversation_context()
                self._send_message({
                    "type": "conversation_cleared",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "get_history":
                history = await self.interaction_service.get_conversation_history()
                self._send_message({
                    "type": "conversation_history",
                    "history": history
                })
            
            elif msg_type == "get_agent_status":
                status = await self.get_agent_status()
                self._send_message({
                    "type": "agent_status",
                    "status": status
                })
            
            elif msg_type == "toggle_live_voice":
                enabled = message.get("enabled", False)
                await self.toggle_live_voice(enabled)
            
            elif msg_type == "ping":
                self._send_message({"type": "pong"})
            
            
            else:
                logger.warning(f"Unknown message type from UI: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling UI message: {e}", exc_info=True)
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
        logger.info(f"Speech recognized: {text}")
        self._set_state(SystemState.PROCESSING)
        
        try:
            await self.interaction_service.process_voice_input(text)
        except Exception as e:
            logger.error(f"Error processing voice input: {e}", exc_info=True)
            self._set_state(SystemState.ERROR)
            await asyncio.sleep(1.0)
        finally:
            self._set_state(SystemState.IDLE)

    async def _on_audio_level(self, level: float):
        """Handle audio level updates for visualization"""
        # Send to UI for waveform visualization
        if self.message_callback:
            self.message_callback({
                "type": "audio_level",
                "level": level
            })


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

    # ==================== Agent System Methods ====================
    
    async def _initialize_agents(self):
        """Initialize and register all personal agents"""
        try:
            logger.info("Initializing agent system...")
            
            # Create agents
            file_agent = PersonalFileAgent()
            web_agent = PersonalWebAgent()
            productivity_agent = PersonalProductivityAgent()
            
            # Register agents
            await self.agent_registry.register(file_agent)
            await self.agent_registry.register(web_agent)
            await self.agent_registry.register(productivity_agent)
            
            # Create coordinator with reference to self
            self.agent_coordinator = AgentCoordinator(self.agent_registry, main_coordinator=self)
            
            # Update SystemControl with agent coordinator for delegation
            self.system_control.agent_coordinator = self.agent_coordinator
            
            stats = self.agent_registry.get_statistics()
            logger.success(f"Agent system initialized: {stats['total_agents']} agents registered")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            self.agents_enabled = False
    
    async def _try_agent_execution(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Try to execute task using agent system
        
        Returns:
            Dict with result if agent handled it, None if should fallback to LLM
        """
        if not self.agents_enabled or not self.agent_coordinator:
            return None
        
        try:
            # Step 1: Use AI engine to parse user intent (no expensive context needed)
            logger.info("Parsing user intent with LLM...")
            intent_data = await self.ai.parse_user_intent(
                user_input,
                context=None  # Intent parsing doesn't need full system context
            )
            
            logger.info(f"Parsed intent: agent_type={intent_data.get('agent_type')}, task={intent_data.get('task_type')}, params={intent_data.get('parameters')}")
            
            # If confidence is too low or it's conversational, fallback to LLM
            if intent_data.get('confidence', 0) < 0.5 or intent_data.get('agent_type') == 'conversational':
                logger.info(f"Low confidence ({intent_data.get('confidence')}) or conversational task, using LLM")
                return None
            
            # Step 2: Let agent coordinator execute with parsed intent
            response = await self.agent_coordinator.execute_task_with_intent(
                intent_data=intent_data,
                context={
                    'conversation_history': self.interaction_service.conversation_context,
                    'system_context': await self.interaction_service._get_system_context()
                }
            )
            
            if response.is_success():
                logger.info(f"Task handled by agent: {response.agent_name}")
                return {
                    'handled': True,
                    'agent_name': response.agent_name,
                    'response': response
                }
            else:
                logger.info(f"Agent execution failed, falling back to LLM: {response.error}")
                return None
                
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}")
            return None
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        if not self.agent_registry:
            return {'enabled': False}
        
        health = await self.agent_registry.health_check_all()
        stats = self.agent_registry.get_statistics()
        
        return {
            'enabled': self.agents_enabled,
            'statistics': stats,
            'health': health,
        }

    # ==================== Context Management ====================
    
    # Context management moved to InteractionService
    
    # ==================== Live Voice Methods ====================
    
    async def toggle_live_voice(self, enabled: bool):
        """Toggle Live Voice mode on/off"""
        try:
            if enabled:
                await self.start_live_voice()
            else:
                await self.stop_live_voice()
        except Exception as e:
            logger.error(f"Error toggling Live Voice: {e}", exc_info=True)
            self._send_message({
                "type": "live_voice_error",
                "message": str(e)
            })
    
    async def start_live_voice(self):
        """Start Live Voice mode"""
        if self.live_voice_enabled:
            logger.warning("Live Voice already active")
            return
        
        try:
            logger.info("Starting Live Voice mode...")
            
            # Initialize Live Voice manager if not already done
            if not self.live_voice:
                api_key = config.ai.gemini_api_key
                if not api_key:
                    raise ValueError("Gemini API key not configured")
                
                self.live_voice = LiveVoiceManager(api_key)
                
                # Set up callbacks
                self.live_voice.on_state_change = self._on_live_voice_state_change
                self.live_voice.on_audio_level = self._on_audio_level
                self.live_voice.on_error = self._on_live_voice_error
            
            # Start Live Voice session
            system_instruction = "You are PRISM, a friendly AI assistant. Be helpful and conversational."
            await self.live_voice.start_live_mode(system_instruction)
            
            self.live_voice_enabled = True
            
            # Notify UI
            self._send_message({
                "type": "live_voice_started",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.success("Live Voice mode started")
            
        except Exception as e:
            logger.error(f"Failed to start Live Voice: {e}", exc_info=True)
            self.live_voice_enabled = False
            raise
    
    async def stop_live_voice(self):
        """Stop Live Voice mode"""
        if not self.live_voice_enabled:
            return
        
        try:
            logger.info("Stopping Live Voice mode...")
            
            if self.live_voice:
                await self.live_voice.stop_live_mode()
            
            self.live_voice_enabled = False
            
            # Notify UI
            self._send_message({
                "type": "live_voice_stopped",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.success("Live Voice mode stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Live Voice: {e}", exc_info=True)
    
    def _on_live_voice_state_change(self, state: str):
        """Handle Live Voice state changes"""
        logger.debug(f"Live Voice state: {state}")
        
        # Map Live Voice states to system states
        state_map = {
            "listening": SystemState.LISTENING,
            "responding": SystemState.RESPONDING,
            "idle": SystemState.IDLE
        }
        
        system_state = state_map.get(state, SystemState.IDLE)
        self._set_state(system_state)
    
    def _on_live_voice_error(self, error: str):
        """Handle Live Voice errors"""
        logger.error(f"Live Voice error: {error}")
        self._send_message({
            "type": "live_voice_error",
            "message": error
        })


# Global coordinator instance
coordinator = PRISMCoordinator()
