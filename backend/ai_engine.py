"""
AI Engine
Language understanding, response generation, and action processing
"""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import re
from loguru import logger

from backend.config import config

# Import AI providers
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")


class ActionType(Enum):
    """Types of actions that can be executed"""
    OPEN_APPLICATION = "open_application"
    OPEN_FILE = "open_file"
    SEARCH_FILES = "search_files"
    CREATE_FILE = "create_file"
    WEB_SEARCH = "web_search"
    SYSTEM_COMMAND = "system_command"
    INFORMATION_QUERY = "information_query"


@dataclass
class AIResponse:
    """Structured AI response"""
    text: str
    requires_action: bool = False
    actions: List[Dict[str, Any]] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []


class AIEngine:
    """
    Central AI engine for natural language understanding,
    response generation, and action extraction
    """

    def __init__(self):
        self.initialized = False
        self.model = None
        self.provider = config.ai.provider
        
        # System prompt that defines PRISM's personality and capabilities
        self.system_prompt = """You are PRISM, a personal AI assistant. You are friendly, efficient, and get things done.

        **Your Role**: You coordinate between direct system actions and specialized agents. You decide what to do based on the user's request.

        **Decision Making**:
        - Conversations/questions → Respond naturally
        - File operations → Delegate to PersonalFileAgent
        - Web operations → Delegate to PersonalWebAgent
        - Productivity tasks → Delegate to PersonalProductivityAgent
        - System control → Use direct actions

        **Specialized Agents Available**:

        **PersonalFileAgent** (file_management):
        - "search_files": Find files by name/type/location
        - "open_file": Find and open files (movies, documents, music, etc.)
        - "delete_file": Delete specific files by name/type
        - "organize_downloads": Clean up downloads folder
        - "backup": Backup files/folders
        - "cleanup": Remove files older than X days
        Parameters: search_term, location, file_type, path

        **PersonalWebAgent** (web_operations):
        - "research": Research topics online and return information
        - "web_search": Search the web and return actual results/information
        - "monitor": Monitor websites for changes
        - "save_content": Save web content locally

        **PersonalProductivityAgent** (productivity):
        - "start_focus_session": Begin focus/work session
        - "track_habit": Track habit completion
        - "suggest_break": Suggest break times
        - "get_stats": Show productivity statistics

        **CRITICAL: Agent vs Direct Action Decision**:
        
        **Use PersonalWebAgent for**: Information gathering, research, getting search results
        - "search for cyclone updates" → PersonalWebAgent returns actual information
        - "research AI trends" → PersonalWebAgent returns research data
        - "find news about..." → PersonalWebAgent returns news results
        
        **Use Direct System Actions for**: Opening applications, browser control
        - "open chrome" → Direct system action to launch browser
        - "open firefox" → Direct system action to launch browser
        - "close browser" → Direct system action
        
        **Agent Call Format**:
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalWebAgent", "task": "web_search", "params": {"query": "your search query"}}}
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalFileAgent", "task": "open_file", "params": {"search_term": "movie_name", "file_type": "video"}}}

        **Direct System Actions**:
        - open_application: {"name": "app_name"}
        - close_application: {"name": "app_name"}
        - mcp_focus_window: {"title": "window_title"}
        - mcp_type_text: {"text": "text to type"}
        - mcp_click: {"x": 100, "y": 200}
        - mcp_hotkey: {"keys": "ctrl+c"}
        - get_memory_info: {}

        **Examples**:
        User: "search for cyclone updates in andhra pradesh" (wants information)
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalWebAgent", "task": "web_search", "params": {"query": "cyclone updates andhra pradesh"}}}

        User: "kindly search for the cyclone updates in the andhra pradesh and let me know" (wants information)
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalWebAgent", "task": "web_search", "params": {"query": "cyclone updates andhra pradesh"}}}

        User: "open chrome" (wants to launch browser)
        ACTION: {"type": "open_application", "parameters": {"name": "chrome"}}

        User: "open chrome and search for weather" (wants browser opened)
        ACTION: {"type": "open_application", "parameters": {"name": "chrome"}}

        User: "find my movies" (file operation)
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalFileAgent", "task": "search_files", "params": {"file_type": "video"}}}

        User: "research artificial intelligence" (wants information)
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalWebAgent", "task": "research", "params": {"topic": "artificial intelligence"}}}

        User: "start a focus session" (productivity task)
        ACTION: {"type": "agent_call", "parameters": {"agent": "PersonalProductivityAgent", "task": "start_focus_session", "params": {"duration": 25}}}

        **Key Principles**:
        1. Understand user intent, not just literal words
        2. Be proactive - don't ask for details when agents can find them
        3. Use agents for their specialties (files, web, productivity)
        4. Use direct actions for immediate system control
        5. Support both English and Telugu naturally
        6. Think intelligently about what users actually want
        7. PersonalWebAgent returns information - use for research/search queries
        8. Direct system actions control applications - use for "open/close app"

        **Action Format**: ACTION: {"type": "action_type", "parameters": {...}}
        """

    async def initialize(self):
        """Initialize AI provider"""
        if self.initialized:
            return
        
        logger.info(f"Initializing AI engine (provider: {self.provider})...")
        
        try:
            if self.provider == "gemini":
                if not GEMINI_AVAILABLE:
                    raise ImportError("Google Generative AI library not available")
                if not config.ai.gemini_api_key:
                    raise ValueError("Gemini API key not configured")
                
                genai.configure(api_key=config.ai.gemini_api_key)
                
                # Configure safety settings to allow all content
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
                
                self.model = genai.GenerativeModel(
                    model_name=config.ai.model,
                    generation_config={
                        "temperature": config.ai.temperature,
                        "max_output_tokens": config.ai.max_tokens,
                    },
                    safety_settings=safety_settings
                )
                logger.success("Gemini initialized with safety filters disabled")
                
            else:
                logger.warning(f"Unknown AI provider: {self.provider}, using fallback")
                self.provider = "fallback"
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing AI engine: {e}")
            logger.info("Falling back to rule-based responses")
            self.provider = "fallback"
            self.initialized = True

    async def process_input(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]] = None,
        system_context: Dict[str, Any] = None
    ) -> AIResponse:
        """
        Process user input and generate response with potential actions
        """
        logger.info(f"Processing input: {user_input}")
        
        try:
            # Build context
            context = self._build_context(system_context)
            
            # Get AI response
            if self.provider == "gemini":
                response = await self._process_gemini(user_input, conversation_history, context)
            else:
                response = await self._process_fallback(user_input)
            
            # Extract actions from response
            response = self._extract_actions(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return AIResponse(
                text="I encountered an error processing your request. Could you rephrase that?",
                requires_action=False
            )

    async def _process_gemini(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        context: str
    ) -> AIResponse:
        """Process input using Google Gemini"""
        # Build full prompt with system context and conversation history
        full_prompt = f"{self.system_prompt}\n\n{context}\n\n"
        
        # Add conversation history
        if conversation_history:
            full_prompt += "Previous conversation:\n"
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    full_prompt += f"User: {content}\n"
                elif role == 'assistant':
                    full_prompt += f"Assistant: {content}\n"
            full_prompt += "\n"
        
        # Add current input
        full_prompt += f"User: {user_input}\nAssistant:"
        
        # Call Gemini API
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.generate_content(full_prompt)
        )
        
        # Handle multi-part responses
        try:
            text = response.text
        except Exception as e:
            logger.warning(f"Could not access response.text: {e}, using parts")
            # Fallback to parts
            text = ""
            if response.candidates and len(response.candidates) > 0:
                parts = response.candidates[0].content.parts
                text = "".join([part.text for part in parts if hasattr(part, 'text')])
        
        return AIResponse(text=text)

    async def _process_fallback(self, user_input: str) -> AIResponse:
        """Fallback rule-based processing"""
        user_input_lower = user_input.lower()
        
        # Simple pattern matching for common requests
        if any(word in user_input_lower for word in ["open", "launch", "start"]):
            # Extract application name
            for word in ["open", "launch", "start"]:
                if word in user_input_lower:
                    app_name = user_input_lower.split(word)[-1].strip()
                    return AIResponse(
                        text=f"Opening {app_name}...",
                        requires_action=True,
                        actions=[{
                            "type": ActionType.OPEN_APPLICATION.value,
                            "parameters": {"name": app_name}
                        }]
                    )
        
        elif any(word in user_input_lower for word in ["search", "find", "look for"]):
            query = user_input_lower.split("for")[-1].strip() if "for" in user_input_lower else user_input
            return AIResponse(
                text=f"Searching for: {query}",
                requires_action=True,
                actions=[{
                    "type": ActionType.WEB_SEARCH.value,
                    "parameters": {"query": query}
                }]
            )
        
        elif any(word in user_input_lower for word in ["create", "make", "new"]):
            return AIResponse(
                text="I can help you create files. What would you like to create?",
                requires_action=False
            )
        
        else:
            return AIResponse(
                text="I'm listening. How can I help you? I can open applications, search for information, manage files, and more.",
                requires_action=False
            )

    def _build_context(self, system_context: Optional[Dict[str, Any]]) -> str:
        """Build context string from system information"""
        if not system_context:
            return ""
        
        context_parts = ["Current system context:"]
        
        if "current_directory" in system_context:
            context_parts.append(f"Working directory: {system_context['current_directory']}")
        
        if "running_applications" in system_context:
            apps = system_context["running_applications"]
            if apps:
                context_parts.append(f"Running applications: {', '.join(apps[:5])}")
        
        return "\n".join(context_parts)

    def _extract_actions(self, response: AIResponse) -> AIResponse:
        """Extract actions from AI response text"""
        # Collect all ACTION blocks to remove, then remove them all at once
        action_keyword = "ACTION:"
        decoder = json.JSONDecoder()
        blocks_to_remove = []  # List of (start_idx, end_idx) tuples
        
        search_start = 0
        while True:
            # Locate the next ACTION: token
            idx = response.text.find(action_keyword, search_start)
            if idx == -1:
                break
            
            # Find the first opening brace after ACTION:
            brace_idx = response.text.find('{', idx)
            if brace_idx == -1:
                # No JSON object – move past this token
                search_start = idx + len(action_keyword)
                continue

            # Attempt to decode a JSON object starting at brace_idx
            substring = response.text[brace_idx:]
            try:
                action_obj, end_pos = decoder.raw_decode(substring)
                response.requires_action = True
                response.actions.append(action_obj)
                logger.info(f"Extracted action from ACTION tag: {action_obj}")
                
                # Mark this block for removal (from ACTION: to end of JSON)
                blocks_to_remove.append((idx, brace_idx + end_pos))
                search_start = brace_idx + end_pos
                
            except json.JSONDecodeError as e:
                # Try to balance braces heuristically
                open_braces = substring.count('{')
                close_braces = substring.count('}')
                if open_braces > close_braces:
                    needed = open_braces - close_braces
                    balanced_substring = substring + ('}' * needed)
                    try:
                        action_obj, end_pos = decoder.raw_decode(balanced_substring)
                        response.requires_action = True
                        response.actions.append(action_obj)
                        logger.info(f"Extracted action (after balancing braces): {action_obj}")
                        
                        # Mark for removal
                        end_pos_original = min(len(substring), end_pos)
                        blocks_to_remove.append((idx, brace_idx + end_pos_original))
                        search_start = brace_idx + end_pos_original
                        continue
                    except json.JSONDecodeError:
                        pass
                
                # Manual fallback for simple patterns
                logger.warning(f"Could not parse action JSON: {substring[:100]}...")
                type_match = re.search(r'"type"\s*:\s*"([^"]+)"', substring[:200])
                name_match = re.search(r'"name"\s*:\s*"([^"]+)"', substring[:200])
                
                if type_match and name_match:
                    manual_action = {
                        "type": type_match.group(1),
                        "parameters": {"name": name_match.group(1)}
                    }
                    response.requires_action = True
                    response.actions.append(manual_action)
                    logger.info(f"Manually extracted action: {manual_action}")
                
                # Move past this failed attempt
                search_start = brace_idx + 1
        
        # Remove all ACTION blocks from text (in reverse order to maintain indices)
        for start_idx, end_idx in reversed(blocks_to_remove):
            response.text = response.text[:start_idx] + response.text[end_idx:]
        
        # Clean up extra whitespace
        response.text = response.text.strip()
        
        # Fallback: Parse natural language for common actions if no ACTION tag found
        if not response.actions:
            text_lower = response.text.lower()
            original_text = response.text
            
            # Check for application opening - use multi-word app names
            open_patterns = [
                (r'(?:open|opening|launch|launching|start|starting)\s+([A-Z][A-Za-z\s]+?)(?:\s+for you|\s+right|\.|$)', 'open_application'),
                (r'(?:i\'ll|i will|let me)\s+open\s+([A-Z][A-Za-z\s]+?)(?:\s+for you|\s+right|\.|$)', 'open_application'),
            ]
            
            for pattern, action_type in open_patterns:
                match = re.search(pattern, original_text)
                if match:
                    app_name = match.group(1).strip()
                    logger.info(f"Extracted action from natural language: open '{app_name}'")
                    response.requires_action = True
                    response.actions.append({
                        "type": action_type,
                        "parameters": {"name": app_name}
                    })
                    break
        
        return response

    async def parse_user_intent(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse user input to understand intent and extract structured parameters for agents
        
        Returns:
            Dict with:
            - agent_type: Which agent should handle this
            - task_type: Specific task for the agent
            - parameters: Structured parameters extracted from user input
            - confidence: How confident the LLM is about this interpretation
        """
        logger.info(f"Parsing user intent: {user_input}")
        
        # Build a prompt specifically for intent parsing
        intent_prompt = f"""Parse: "{user_input}"

Understand the user's actual intent, not just literal words.

When user asks about "movies" or "videos" or "films" → they want video files, not files named "movie"
When user asks about "music" or "songs" → they want audio files, not files named "music"  
When user asks about "documents" or "files" → they want document files
When user asks about "pictures" or "photos" → they want image files

For file operations:
- "delete [files]" or "remove [files]" → task_type: "delete_file" (delete specific files)
- "cleanup old files" or "remove old files" → task_type: "cleanup" (delete by age)
- "search/find [files]" → task_type: "search_files"
- "open/play [file]" → task_type: "open_file"

For file searches, use smart parameters:
- If asking about movies/videos → search_term: "", file_type: "video" (search all video files)
- If asking about music/audio → search_term: "", file_type: "audio" (search all audio files)
- If asking about specific file → search_term: "actual_filename", file_type: relevant_type

Return JSON:
- agent_type: file_management, web_operations, productivity, system_control, conversational
- task_type: search_files, open_file, delete_file, cleanup, organize_downloads, web_search, etc.
- parameters: smart extracted params
- confidence: 0.0-1.0

JSON only:
"""
        
        try:
            if self.provider == "gemini" and self.model:
                # Get LLM response
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(intent_prompt)
                )
                
                # Handle multi-part responses
                try:
                    response_text = response.text.strip()
                except Exception as e:
                    logger.warning(f"Could not access response.text: {e}, using parts")
                    # Fallback to parts
                    response_text = ""
                    if response.candidates and len(response.candidates) > 0:
                        parts = response.candidates[0].content.parts
                        response_text = "".join([part.text for part in parts if hasattr(part, 'text')]).strip()
                    
                    # If still empty, check for safety ratings or blocked content
                    if not response_text:
                        if hasattr(response, 'prompt_feedback'):
                            logger.error(f"Response blocked by safety filters: {response.prompt_feedback}")
                        logger.warning("Empty response from LLM, using fallback parsing")
                        return self._fallback_intent_parsing(user_input)
                
                logger.info(f"LLM intent response: {response_text}")
                
                # Extract JSON from response
                # Sometimes LLM wraps JSON in markdown code blocks
                if "```json" in response_text:
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                elif "```" in response_text:
                    json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                # Parse JSON
                intent_data = json.loads(response_text)
                logger.info(f"Parsed intent: {intent_data}")
                return intent_data
                
            else:
                # Fallback: Simple keyword-based parsing
                return self._fallback_intent_parsing(user_input)
                
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            # Return fallback
            return self._fallback_intent_parsing(user_input)
    
    def _fallback_intent_parsing(self, user_input: str) -> Dict[str, Any]:
        """Fallback intent parsing using keywords"""
        user_lower = user_input.lower()
        
        # Open/play file pattern
        if any(word in user_lower for word in ['open', 'play', 'launch']) and not any(word in user_lower for word in ['application', 'app', 'program']):
            # Extract search term
            for phrase in ['open the', 'open', 'play the', 'play', 'launch']:
                if phrase in user_lower:
                    remainder = user_input.lower().replace(phrase, '').strip()
                    
                    # Extract location
                    location = None
                    if 'downloads' in remainder or 'from downloads' in remainder:
                        location = 'downloads'
                        remainder = remainder.replace('from downloads', '').replace('in downloads', '').replace('downloads', '').strip()
                    elif 'documents' in remainder or 'from documents' in remainder:
                        location = 'documents'
                        remainder = remainder.replace('from documents', '').replace('in documents', '').replace('documents', '').strip()
                    
                    # Extract file type
                    file_type = None
                    if any(word in remainder for word in ['movie', 'video', 'mp4', 'mkv']):
                        file_type = 'video'
                    elif any(word in remainder for word in ['pdf', 'document', 'doc']):
                        file_type = 'document'
                    elif any(word in remainder for word in ['image', 'photo', 'picture', 'jpg', 'png']):
                        file_type = 'image'
                    
                    # Clean up search term
                    search_term = remainder.replace('movie', '').replace('video', '').replace('folder', '').replace('from', '').strip()
                    
                    return {
                        'agent_type': 'file_management',
                        'task_type': 'open_file',
                        'parameters': {
                            'search_term': search_term,
                            'location': location,
                            'file_type': file_type
                        },
                        'confidence': 0.8
                    }
        
        # File search pattern
        if 'search' in user_lower or 'find' in user_lower:
            # Extract search term
            for phrase in ['search for', 'find', 'look for']:
                if phrase in user_lower:
                    remainder = user_input.lower().replace(phrase, '').strip()
                    
                    # Extract location
                    location = None
                    if 'downloads' in remainder:
                        location = 'downloads'
                        remainder = remainder.replace('in my downloads folder', '').replace('downloads', '').strip()
                    elif 'documents' in remainder:
                        location = 'documents'
                        remainder = remainder.replace('in my documents', '').replace('documents', '').strip()
                    
                    # Extract file type
                    file_type = None
                    if any(word in remainder for word in ['movie', 'video', 'mp4', 'mkv']):
                        file_type = 'video'
                    elif any(word in remainder for word in ['pdf', 'document', 'doc']):
                        file_type = 'document'
                    elif any(word in remainder for word in ['image', 'photo', 'picture', 'jpg', 'png']):
                        file_type = 'image'
                    
                    # Clean up search term
                    search_term = remainder.replace('movie', '').replace('video', '').replace('folder', '').replace('in my', '').strip()
                    
                    return {
                        'agent_type': 'file_management',
                        'task_type': 'search_files',
                        'parameters': {
                            'search_term': search_term,
                            'location': location,
                            'file_type': file_type
                        },
                        'confidence': 0.7
                    }
        
        # Organize downloads
        if 'organize' in user_lower and 'download' in user_lower:
            return {
                'agent_type': 'file_management',
                'task_type': 'organize_downloads',
                'parameters': {},
                'confidence': 0.9
            }
        
        # Web search
        if 'search' in user_lower and ('web' in user_lower or 'google' in user_lower or 'internet' in user_lower):
            query = user_input
            for phrase in ['search for', 'search', 'google', 'look up']:
                query = query.replace(phrase, '').strip()
            
            return {
                'agent_type': 'web_operations',
                'task_type': 'web_search',
                'parameters': {'query': query},
                'confidence': 0.8
            }
        
        # Default: conversational
        return {
            'agent_type': 'conversational',
            'task_type': 'chat',
            'parameters': {'message': user_input},
            'confidence': 0.5
        }
    
    async def parse_app_control_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse app control commands (close, minimize, maximize, focus) using LLM
        
        Returns:
            Dict with:
            - action: The action to perform (close, minimize, maximize, focus)
            - app_name: The application name to target
            - confidence: Confidence level (0.0 to 1.0)
        """
        logger.info(f"Parsing app control intent: {user_input}")
        
        # Build a prompt specifically for app control parsing
        intent_prompt = f"""Parse app control: "{user_input}"

Return JSON with:
- action: close, minimize, maximize, or focus
- app_name: exact app name mentioned
- confidence: 0.0-1.0

JSON only:
"""
        
        try:
            if self.provider == "gemini" and self.model:
                # Get LLM response
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(intent_prompt)
                )
                
                # Handle multi-part responses
                try:
                    response_text = response.text.strip()
                except Exception as e:
                    logger.warning(f"Could not access response.text: {e}, using parts")
                    response_text = ""
                    if response.candidates and len(response.candidates) > 0:
                        parts = response.candidates[0].content.parts
                        response_text = "".join([part.text for part in parts if hasattr(part, 'text')]).strip()
                    
                    if not response_text:
                        logger.warning("Empty response from LLM, using fallback parsing")
                        return self._fallback_app_control_parsing(user_input)
                
                logger.info(f"LLM app control response: {response_text}")
                
                # Extract JSON from response
                if "```json" in response_text:
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                elif "```" in response_text:
                    json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                # Parse JSON
                intent_data = json.loads(response_text)
                logger.info(f"Parsed app control intent: {intent_data}")
                return intent_data
                
            else:
                # Fallback: Simple keyword-based parsing
                return self._fallback_app_control_parsing(user_input)
                
        except Exception as e:
            logger.error(f"Error parsing app control intent: {e}")
            return self._fallback_app_control_parsing(user_input)
    
    def _fallback_app_control_parsing(self, user_input: str) -> Dict[str, Any]:
        """Fallback app control parsing using keywords"""
        user_lower = user_input.lower()
        
        # Determine action
        action = None
        if 'close' in user_lower:
            action = 'close'
        elif 'minimize' in user_lower:
            action = 'minimize'
        elif 'maximize' in user_lower:
            action = 'maximize'
        elif 'focus' in user_lower or 'switch to' in user_lower:
            action = 'focus'
        
        if not action:
            return {'action': None, 'app_name': None, 'confidence': 0.0}
        
        # Extract app name - take words after the action keyword
        words = user_input.split()
        app_name = None
        
        for i, word in enumerate(words):
            if word.lower() in ['close', 'minimize', 'maximize', 'focus', 'switch']:
                # Take remaining words as app name
                if i + 1 < len(words):
                    # Skip "to" if present
                    start_idx = i + 2 if i + 1 < len(words) and words[i + 1].lower() == 'to' else i + 1
                    if start_idx < len(words):
                        app_name = ' '.join(words[start_idx:])
                        break
        
        # Clean up common words
        if app_name:
            app_name = app_name.replace('the ', '').strip()
        
        return {
            'action': action,
            'app_name': app_name,
            'confidence': 0.7 if app_name else 0.3
        }

    async def shutdown(self):
        """Shutdown AI engine"""
        logger.info("Shutting down AI engine...")
        self.initialized = False
