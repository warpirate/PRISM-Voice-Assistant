"""
PRISM LLM Integration with Nebius AI Studio
"""

import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from memory import MemoryManager

load_dotenv()
logger = logging.getLogger(__name__)


class PrismLLM:
    """PRISM's AI brain using Nebius AI Studio"""
    
    def __init__(self):
        api_key = os.getenv("NEBIUS_API_KEY")
        if not api_key:
            raise ValueError("NEBIUS_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            base_url="https://api.studio.nebius.com/v1/",
            api_key=api_key
        )
        
        self.model = "meta-llama/Meta-Llama-3.1-70B-Instruct"
        self.memory = MemoryManager()
        
        self.system_prompt = """You are PRISM, a friendly and intelligent Windows voice assistant, similar to JARVIS from Iron Man. You help users with:

1. System Control: Opening applications, managing files, adjusting settings
2. Information: Answering questions, web searches, general knowledge
3. Conversation: Engaging in friendly chitchat with personality

IMPORTANT: Always respond in valid JSON format with this structure:
{
    "action": "system|response|chitchat|search|file",
    "command": "windows command if action is system, otherwise null",
    "text": "friendly response to speak to the user",
    "query": "search terms if action is search, otherwise null",
    "operation": "read|write|append|create|open if action is file, otherwise null",
    "path": "file path for file actions, otherwise null",
    "content": "text content for write/append/create, otherwise null"
}

Guidelines:
- Be conversational, friendly, and occasionally humorous
- Reference past interactions when relevant (memory will be provided)
- Keep responses concise but informative
- For system commands, use Windows-compatible commands
- For search, set "query" to what should be searched
- For file actions, specify operation, absolute path, and content when needed
- Add personality - you're not just a tool, you're a companion

Examples:
User: "Open Notepad"
Response: {"action": "system", "command": "notepad", "text": "Opening Notepad for you!"}

User: "Search latest AI news"
Response: {"action": "search", "command": null, "query": "latest AI news", "text": "Searching for the latest AI news..."}

User: "Create a file notes.txt with hello world"
Response: {"action": "file", "operation": "create", "path": "C:\\Users\\<user>\\Documents\\notes.txt", "content": "hello world", "text": "Creating notes.txt in Documents."}

User: "Tell me a joke"
Response: {"action": "chitchat", "command": null, "text": "Why did the programmer quit his job? Because he didn't get arrays! 😄"}
"""
    
    def query(self, user_input: str) -> dict:
        """
        Query the LLM with user input and return structured response
        
        Args:
            user_input: User's voice command or query
            
        Returns:
            dict: Structured response with action, command, and text
        """
        try:
            # Get relevant memory
            memory_context = self._get_memory_context(user_input)
            
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            if memory_context:
                messages.append({
                    "role": "system",
                    "content": f"Memory Context: {memory_context}"
                })
            
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Call Nebius API
            logger.info(f"Querying LLM with: {user_input}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            logger.debug(f"LLM response: {content}")
            
            result = json.loads(content)
            
            # Validate response structure
            if "text" not in result:
                result["text"] = "I'm not sure how to respond to that."
            if "action" not in result:
                result["action"] = "response"
            if "command" not in result:
                result["command"] = None
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {
                "action": "response",
                "command": None,
                "text": "I had trouble processing that. Could you try again?"
            }
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return {
                "action": "response",
                "command": None,
                "text": "Sorry, I encountered an error. Please try again."
            }
    
    def _get_memory_context(self, user_input: str) -> str:
        """Get relevant memory context for the query"""
        try:
            recent = self.memory.get_recent_interactions(limit=3)
            
            if not recent:
                return ""
            
            context_parts = []
            for interaction in recent:
                context_parts.append(
                    f"Previous: User said '{interaction[1]}', "
                    f"you responded '{interaction[2]}'"
                )
            
            return " | ".join(context_parts)
            
        except Exception as e:
            logger.warning(f"Failed to get memory context: {e}")
            return ""
