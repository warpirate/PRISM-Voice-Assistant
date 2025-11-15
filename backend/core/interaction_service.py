"""
Interaction Service
Handles user input processing, AI coordination, and response delivery
"""

import asyncio
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from loguru import logger

from backend.ai_engine import AIEngine
from backend.memory_system import MemorySystem
from backend.voice_pipeline import VoicePipeline
from backend.system_control import SystemControl
from backend.config import config


class InteractionService:
    """
    Handles the core interaction flow:
    - Text/voice input processing
    - AI coordination
    - Memory management
    - Action execution
    - Response delivery
    """

    def __init__(
        self,
        ai_engine: AIEngine,
        memory_system: MemorySystem,
        voice_pipeline: VoicePipeline,
        system_control: SystemControl,
        ui_message_sender: Callable[[Dict[str, Any]], None]
    ):
        self.ai = ai_engine
        self.memory = memory_system
        self.voice = voice_pipeline
        self.system_control = system_control
        self.send_ui_message = ui_message_sender
        
        # Processing state
        self.processing_lock = asyncio.Lock()
        
        # Conversation context
        self.conversation_context: List[Dict[str, str]] = []
        self.current_conversation_id: Optional[str] = None
        
        # System context cache
        self._system_context_cache: Optional[Dict[str, Any]] = None
        self._context_cache_time: Optional[datetime] = None
        self._context_cache_ttl: int = 5  # Cache TTL in seconds
        
        logger.info("InteractionService initialized")

    async def process_text_input(self, text: str) -> None:
        """Process text input directly (without voice)"""
        logger.info(f"Processing text input: {text}")
        
        # Check if already processing
        if self.processing_lock.locked():
            logger.warning("Already processing a message, queuing this one")
            self.send_ui_message({
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

    async def process_voice_input(self, text: str) -> None:
        """Process voice input from speech recognition"""
        if not text:
            logger.warning("Empty text received from speech recognition")
            self.send_ui_message({
                "type": "listening_timeout",
                "message": "No speech detected",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        logger.info(f"Speech recognized: {text}")
        await self._process_user_input(text, input_method="voice")

    async def _process_user_input(self, user_input: str, input_method: str = "voice"):
        """
        Process user input through the AI engine and execute actions
        """
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
            self.send_ui_message({
                "type": "user_message",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # AI-First Approach: Let LLM decide everything from the start
            logger.info("Using AI-first approach - LLM will decide routing and actions")
            
            # Always start with AI to determine the best approach
            # AI will decide if it needs agents or can handle directly
            response = await self.ai.process_input(
                user_input=user_input,
                conversation_history=self.conversation_context,
                system_context=await self._get_system_context()  # Start lightweight
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
            elif "timeout" in str(e).lower():
                error_message = "That request took too long to process. Please try a simpler command."
            else:
                error_message = "I encountered an error processing your request. Please try again."
            
            await self._deliver_response(error_message)

    async def _handle_response(self, response):
        """Handle AI response (text output and/or actions)"""
        try:
            # Only deliver the text response if there are no actions to execute
            # or if the response text is not just a description of the actions
            if not response.requires_action or not response.actions:
                await self._deliver_response(response.text, wait_for_speech=False)
            
            # Execute actions if required
            if response.requires_action and response.actions:
                await self._execute_actions(response.actions, response.text)
        finally:
            # Always return to idle handled by coordinator
            pass

    async def _deliver_response(self, text: str, wait_for_speech: bool = True):
        """Deliver response through voice and UI"""
        # Send to UI
        self.send_ui_message({
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

    async def _execute_actions(self, actions: list, action_description: str = None, max_iterations: int = 10):
        """Execute system actions with iterative tool calling support"""
        if not actions:
            logger.warning("No actions to execute")
            return
        
        logger.info(f"Executing {len(actions)} action(s): {[a.get('type') for a in actions]}")
        
        # If we have an action description, deliver it as a response
        if action_description:
            await self._deliver_response(action_description, wait_for_speech=False)
        
        iteration = 0
        current_actions = actions
        last_state_result = None
        
        while current_actions and iteration < max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}: Executing {len(current_actions)} action(s)")
            
            next_actions = []
            state_captured = False
            
            for action in current_actions:
                try:
                    action_type = action.get('type', 'unknown')
                    logger.info(f"Executing action: {action_type} with parameters: {action.get('parameters', {})}")
                    
                    result = await self.system_control.execute_action(action)
                    
                    logger.info(f"Action result: success={result.get('success')}, message={result.get('message')}")
                    
                    # Add delays after specific actions to allow UI to respond
                    if action_type in ['open_application', 'click_coordinates', 'type_text'] and result.get('success', False):
                        logger.debug("Waiting 1.5s for application window to appear...")
                        await asyncio.sleep(1.5)
                    
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
            
            # If we captured state and there are no explicit next actions, 
            # check if we should continue iterating based on the task
            if state_captured and not next_actions:
                # Check if the original user request suggests a multi-step task
                # by looking at the conversation context
                if self.conversation_context:
                    last_user_message = None
                    for msg in reversed(self.conversation_context):
                        if msg.get('role') == 'user':
                            last_user_message = msg.get('content', '')
                            break
                    
                    # If the task involves complex operations (like "send message", "download app", etc.)
                    # and we just captured state, let AI decide next steps
                    if last_user_message and any(keyword in last_user_message.lower() for keyword in 
                        ['send', 'download', 'install', 'open and', 'find', 'search', 'click', 'type']):
                        logger.info("Complex task detected with state captured, asking AI for next steps")
                        
                        # Create a continuation prompt
                        # Truncate state result if too long, but keep important parts
                        state_text = str(last_state_result) if last_state_result else "State captured"
                        if len(state_text) > 3000:
                            # Keep first 2000 chars and last 1000 chars
                            state_text = state_text[:2000] + "\n... [truncated] ...\n" + state_text[-1000:]
                        
                        continuation_prompt = f"""Based on the current desktop state, continue completing the user's request: "{last_user_message}"

Current desktop state:
{state_text}

Analyze the current state carefully and generate the next actions needed to complete this task. Use available system tools for interaction."""
                        
                        # Get AI response for next actions
                        ai_response = await self.ai.process_input(
                            continuation_prompt,
                            conversation_history=self.conversation_context,
                            system_context=await self._get_system_context()
                        )
                        
                        if ai_response.requires_action and ai_response.actions:
                            logger.info(f"AI generated {len(ai_response.actions)} next actions")
                            next_actions = ai_response.actions
                            # Add response to context
                            self.conversation_context.append({
                                "role": "assistant",
                                "content": ai_response.text
                            })
            
            # Update current actions for next iteration
            current_actions = next_actions
            
            # If no more actions, we're done
            if not current_actions:
                logger.info(f"Task completed after {iteration} iteration(s)")
                break
        
        if iteration >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations}), stopping execution")

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
            "running_applications": self.system_control.get_running_applications()[:10],
            "current_directory": self.system_control.get_current_directory(),
        }
        
        # Update cache
        self._system_context_cache = context
        self._context_cache_time = now
        
        return context

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
