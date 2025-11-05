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
from backend.mcp_client import PRISMMCPClient, mcp_client
from backend.live_voice import LiveVoiceManager


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
        self.memory = MemorySystem()
        self.websocket = WebSocketBridge()
        
        # Initialize agent system
        self.agent_registry = AgentRegistry()
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.agents_enabled = True  # Toggle for agent-based processing
        
        # Initialize SystemControl with agent coordinator (will be set later)
        self.system_control = SystemControl()
        
        # Initialize MCP client for screen visibility and app control
        self.mcp_client: Optional[PRISMMCPClient] = None
        self.mcp_enabled = True  # Toggle for MCP-based operations
        
        # Initialize Live Voice manager
        self.live_voice: Optional[LiveVoiceManager] = None
        self.live_voice_enabled = False  # Toggle for Live Voice mode
        
        # Event callbacks for UI
        self.state_callbacks: Dict[SystemState, list] = {state: [] for state in SystemState}
        self.message_callback: Optional[Callable] = None
        
        # Conversation context
        self.current_conversation_id: Optional[str] = None
        self.conversation_context: list = []
        
        # System context cache (to avoid redundant MCP calls)
        self._system_context_cache: Optional[Dict[str, Any]] = None
        self._context_cache_time: Optional[datetime] = None
        self._context_cache_ttl: int = 5  # Cache TTL in seconds
        
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
            
            # Initialize MCP client
            if self.mcp_enabled:
                await self._initialize_mcp_client()
            
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
            
            # Shutdown MCP client
            if self.mcp_client:
                await self.mcp_client.shutdown()
            
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
            
            # AI-First Approach: Let LLM decide everything from the start
            logger.info("Using AI-first approach - LLM will decide routing and actions")
            
            # Always start with AI to determine the best approach
            # AI will decide if it needs agents, MCP tools, or can handle directly
            response = await self.ai.process_input(
                user_input=user_input,
                conversation_history=self.conversation_context,
                system_context=await self._get_system_context(include_mcp=False)  # Start lightweight, AI will request MCP if needed
            )
            
            # If the response includes actions, we'll handle the response in _execute_actions
            # to avoid duplicate notifications
            if not response.requires_action or not response.actions:
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
            
            # Handle response (this will handle both text and actions)
            await self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            
            # Provide more specific error messages based on error type
            if "UnicodeEncodeError" in str(e):
                error_message = "I had trouble processing that message due to special characters. Could you try rephrasing?"
            elif "ConnectionError" in str(e) or "websocket" in str(e).lower():
                error_message = "I'm having connection issues. Let me try to reconnect..."
                # Attempt to reconnect WebSocket
                try:
                    await self.websocket._connect_with_retry()
                except:
                    pass
            elif "timeout" in str(e).lower():
                error_message = "That request took too long to process. Please try a simpler command."
            else:
                error_message = "I encountered an error processing your request. Please try again."
            
            await self._deliver_response(error_message)
            self._set_state(SystemState.ERROR)
            
            # Return to idle after brief delay with exponential backoff
            await asyncio.sleep(min(2.0, 0.5 * (getattr(self, '_error_count', 0) + 1)))
            self._error_count = getattr(self, '_error_count', 0) + 1
            if self._error_count > 5:
                self._error_count = 0  # Reset after 5 errors
            
            self._set_state(SystemState.IDLE)

    async def _handle_response(self, response):
        """Handle AI response (text output and/or actions)"""
        try:
            self._set_state(SystemState.RESPONDING)
            
            # Only deliver the text response if there are no actions to execute
            # or if the response text is not just a description of the actions
            if not response.requires_action or not response.actions:
                await self._deliver_response(response.text, wait_for_speech=False)
            
            # Execute actions if required
            if response.requires_action and response.actions:
                await self._execute_actions(response.actions, response.text)
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

    async def _execute_actions(self, actions: list, action_description: str = None):
        """Execute system actions
        
        Args:
            actions: List of actions to execute
            action_description: Optional description of the actions being taken
        """
        if not actions:
            logger.warning("No actions to execute")
            return
        
        self._set_state(SystemState.EXECUTING)
        logger.info(f"Executing {len(actions)} action(s): {[a.get('type') for a in actions]}")
        
        # If we have an action description, deliver it as a response
        if action_description:
            await self._deliver_response(action_description, wait_for_speech=False)
        
        for action in actions:
            try:
                action_type = action.get('type', 'unknown')
                logger.info(f"Executing action: {action_type} with parameters: {action.get('parameters', {})}")
                
                result = await self.system_control.execute_action(action)
                
                logger.info(f"Action result: success={result.get('success')}, message={result.get('message')}")
                
                # Add delays after specific actions to allow UI to respond
                if action_type == 'open_application' and result.get('success', False):
                    logger.debug("Waiting 1.5s for application window to appear...")
                    await asyncio.sleep(1.5)
                elif action_type in ['mcp_type_text', 'mcp_press_key', 'mcp_hotkey']:
                    # Short delay after keyboard actions for UI to process
                    await asyncio.sleep(0.4)
                elif action_type == 'mcp_focus_window':
                    # Delay after focusing window
                    await asyncio.sleep(0.3)
                elif action_type == 'mcp_click':
                    # Delay after clicking
                    await asyncio.sleep(0.3)
                
                # Notify user of action result if requested
                if result.get("notify", False):
                    await self._deliver_response(result.get("message", "Action completed"))
                elif not result.get("success", False):
                    # Always notify on failure with recovery suggestions
                    error_msg = result.get("message", "Action failed")
                    if "window" in error_msg.lower() and "not found" in error_msg.lower():
                        error_msg += ". The application might not be open or the window title might be different."
                    elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                        error_msg += ". You might need to run as administrator or grant permissions."
                    await self._deliver_response(error_msg)
                    
            except Exception as e:
                logger.error(f"Error executing action {action.get('type', 'unknown')}: {e}", exc_info=True)
                
                # Provide more helpful error messages
                error_type = action.get('type', 'unknown')
                if "timeout" in str(e).lower():
                    error_msg = f"The {error_type} action timed out. The system might be busy."
                elif "permission" in str(e).lower() or "access" in str(e).lower():
                    error_msg = f"I don't have permission to perform the {error_type} action."
                elif "not found" in str(e).lower():
                    error_msg = f"I couldn't find the target for the {error_type} action."
                else:
                    error_msg = f"I couldn't complete the {error_type} action: {str(e)}"
                
                await self._deliver_response(error_msg)
                
                # Continue with other actions instead of stopping completely
                continue

    async def _get_system_context(self, force_refresh: bool = False, include_mcp: bool = True) -> Dict[str, Any]:
        """Get current system context for AI processing with intelligent caching"""
        # Check cache validity
        now = datetime.now()
        if not force_refresh and self._system_context_cache and self._context_cache_time:
            cache_age = (now - self._context_cache_time).total_seconds()
            if cache_age < self._context_cache_ttl:
                logger.debug(f"Using cached system context (age: {cache_age:.1f}s)")
                return self._system_context_cache
        
        # Build fresh context
        context = {
            "timestamp": now.isoformat(),
            "state": self.state.value,
            "running_applications": self.system_control.get_running_applications()[:10],
            "current_directory": self.system_control.get_current_directory(),
        }
        
        # Add MCP context only when needed (expensive operation)
        # Skip MCP context for simple conversational tasks to improve performance
        if include_mcp and self.mcp_enabled and self.mcp_client:
            try:
                mcp_context = await self.mcp_client.get_screen_context()
                if mcp_context.success:
                    context["screen_context"] = mcp_context.data
                    context["mcp_available"] = True
                else:
                    context["mcp_available"] = False
                    logger.warning(f"MCP context failed: {mcp_context.error}")
            except Exception as e:
                logger.error(f"Error getting MCP context: {e}")
                context["mcp_available"] = False
        else:
            context["mcp_available"] = False
        
        # Update cache
        self._system_context_cache = context
        self._context_cache_time = now
        
        return context

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
            
            # Create coordinator
            self.agent_coordinator = AgentCoordinator(self.agent_registry)
            
            # Update SystemControl with agent coordinator for delegation
            self.system_control.agent_coordinator = self.agent_coordinator
            
            stats = self.agent_registry.get_statistics()
            logger.success(f"Agent system initialized: {stats['total_agents']} agents registered")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            self.agents_enabled = False
    
    async def _initialize_mcp_client(self):
        """Initialize MCP client for screen visibility and app control"""
        try:
            logger.info("Initializing MCP client...")
            
            # Create MCP client instance
            self.mcp_client = PRISMMCPClient()
            
            # Initialize connection to Windows MCP server
            await self.mcp_client.initialize()
            
            # Update SystemControl with MCP client reference
            self.system_control.mcp_client = self.mcp_client
            
            # Get available tools
            tools = await self.mcp_client.get_available_tools()
            logger.success(f"MCP client initialized with {len(tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {str(e)}")
            self.mcp_enabled = False
    
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
                    'conversation_history': self.conversation_context,
                    'system_context': await self._get_system_context()
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
            'mcp_available': self.mcp_enabled and self.mcp_client is not None,
            'mcp_tools': len(await self.mcp_client.get_available_tools()) if self.mcp_enabled and self.mcp_client else 0
        }

    async def handle_mcp_query(self, query: str) -> Optional[str]:
        """
        Handle MCP-specific queries using LLM for proper intent parsing
        
        Args:
            query: User query about screen, applications, or automation tasks
            
        Returns:
            Response string if handled, None if should fallback to normal processing
        """
        if not self.mcp_enabled or not self.mcp_client:
            return None
        
        try:
            query_lower = query.lower()
            
            # Check if this is a contextual screen query
            screen_keywords = ["what's on my screen", "what is on my screen", "what am i doing", "show me", "screen", "windows", "applications"]
            if any(keyword in query_lower for keyword in screen_keywords):
                logger.info("Handling contextual screen visibility query with MCP")
                
                # Get contextual screen analysis
                result = await self.mcp_client.get_contextual_screen_analysis()
                
                if result.success:
                    data = result.data
                    summary = data.get("summary", "")
                    
                    # Format contextual response
                    response = f"{summary}\n\n"
                    
                    # Add specific window details if requested
                    if "details" in query_lower or "more" in query_lower:
                        active_windows = data.get("active_windows", [])
                        if active_windows:
                            response += "**Active Windows Details:**\n"
                            for window in active_windows[:5]:
                                title = window.get("title", "Unknown")
                                size = f"{window.get('size', {}).get('width', 0)}x{window.get('size', {}).get('height', 0)}"
                                response += f"• {title} ({size})\n"
                    
                    return response
                else:
                    logger.error(f"MCP contextual analysis failed: {result.error}")
                    return None
            
            # Check if this is a PURE app control query - USE LLM FOR PROPER PARSING
            # Only handle if it's JUST app control, not multi-task queries
            app_control_keywords = ["close", "minimize", "maximize", "focus", "switch to"]
            multi_task_indicators = ["and", "then", "also", "how much", "tell me", "let me know", "show me"]
            
            is_app_control = any(keyword in query_lower for keyword in app_control_keywords)
            is_multi_task = any(indicator in query_lower for indicator in multi_task_indicators)
            
            if is_app_control and not is_multi_task:
                logger.info("Handling pure app control query with MCP - using LLM for intent parsing")
                
                # Use AI engine to properly parse the intent
                intent_data = await self.ai.parse_app_control_intent(query)
                
                if not intent_data or intent_data.get('confidence', 0) < 0.6:
                    logger.warning(f"Low confidence in app control intent: {intent_data}")
                    return None
                
                action = intent_data.get('action')  # close, minimize, maximize, focus
                app_name = intent_data.get('app_name')
                
                if not app_name:
                    logger.warning("Could not extract app name from query")
                    return None
                
                # Normalize app name - remove "app", "browser", "window" suffixes
                app_name_normalized = app_name.lower()
                for suffix in [' app', ' browser', ' window', ' application']:
                    app_name_normalized = app_name_normalized.replace(suffix, '')
                app_name_normalized = app_name_normalized.strip()
                
                # CRITICAL: Self-protection - never close PRISM itself
                if any(prism_name in app_name_normalized for prism_name in ['prism', 'electron']):
                    logger.warning(f"Blocked attempt to close PRISM itself via '{app_name}'")
                    return "I can't close myself - that would terminate our conversation. Did you mean a different application?"
                
                # Execute the action with normalized name
                if action == "close":
                    result = await self.mcp_client.close_application_smart(app_name_normalized)
                    if result.success:
                        return f"Successfully closed {app_name}"
                    else:
                        return f"Couldn't close {app_name}: {result.error}"
                
                elif action == "focus" or action == "switch":
                    result = await self.mcp_client.call_tool("focus_window", title=app_name_normalized)
                    if result.success:
                        return f"Switched to {app_name}"
                    else:
                        return f"Couldn't find window: {app_name}"
                
                elif action == "minimize":
                    result = await self.mcp_client.call_tool("minimize_window", title=app_name_normalized)
                    if result.success:
                        return f"Minimized {app_name}"
                    else:
                        return f"Couldn't minimize {app_name}"
                
                elif action == "maximize":
                    result = await self.mcp_client.call_tool("maximize_window", title=app_name_normalized)
                    if result.success:
                        return f"Maximized {app_name}"
                    else:
                        return f"Couldn't maximize {app_name}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling MCP query: {e}", exc_info=True)
            return None
    
    # ==================== Context Management ====================
    
    # Removed manual conversational detection - AI handles all routing decisions

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
