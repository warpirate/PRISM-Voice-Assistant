"""
Test InteractionService
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.interaction_service import InteractionService
from backend.ai_engine import AIResponse


class TestInteractionService:
    """Test the core interaction flow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_ai = Mock()
        self.mock_memory = Mock()
        self.mock_voice = Mock()
        self.mock_system_control = Mock()
        self.mock_ui_sender = Mock()
        
        # Mock system control methods
        self.mock_system_control.get_running_applications = Mock(return_value=["notepad.exe", "chrome.exe"])
        self.mock_system_control.get_current_directory = Mock(return_value="C:\\Users\\Test")
        
        # Mock voice methods
        self.mock_voice.speak = AsyncMock()
        
        # Create service
        self.service = InteractionService(
            ai_engine=self.mock_ai,
            memory_system=self.mock_memory,
            voice_pipeline=self.mock_voice,
            system_control=self.mock_system_control,
            ui_message_sender=self.mock_ui_sender
        )
    
    async def test_process_text_input_simple_response(self):
        """Test processing text input with simple AI response"""
        # Mock AI response
        self.mock_ai.process_input = AsyncMock(return_value=AIResponse(
            text="Hello! How can I help you?",
            requires_action=False
        ))
        
        # Mock memory operations
        self.mock_memory.store_interaction = AsyncMock()
        
        # Process input
        await self.service.process_text_input("Hello")
        
        # Verify AI was called
        self.mock_ai.process_input.assert_called_once()
        
        # Verify UI messages were sent
        assert self.mock_ui_sender.call_count >= 2  # user message + assistant message
        
        # Check user message was sent
        user_message_call = self.mock_ui_sender.call_args_list[0]
        assert user_message_call[0][0]["type"] == "user_message"
        assert user_message_call[0][0]["content"] == "Hello"
        
        # Check assistant message was sent
        assistant_message_call = self.mock_ui_sender.call_args_list[1]
        assert assistant_message_call[0][0]["type"] == "assistant_message"
        assert assistant_message_call[0][0]["content"] == "Hello! How can I help you?"
    
    async def test_process_text_input_with_actions(self):
        """Test processing text input that requires actions"""
        # Mock AI response with actions
        self.mock_ai.process_input = AsyncMock(return_value=AIResponse(
            text="Opening Notepad...",
            requires_action=True,
            actions=[{
                "type": "open_application",
                "parameters": {"name": "Notepad"}
            }]
        ))
        
        # Mock system control
        self.mock_system_control.execute_action = AsyncMock(return_value={
            "success": True,
            "message": "Notepad opened successfully"
        })
        
        # Mock memory operations
        self.mock_memory.store_interaction = AsyncMock()
        
        # Process input
        await self.service.process_text_input("Open Notepad")
        
        # Verify action was executed
        self.mock_system_control.execute_action.assert_called_once()
        action_call = self.mock_system_control.execute_action.call_args[0][0]
        assert action_call["type"] == "open_application"
        assert action_call["parameters"]["name"] == "Notepad"
    
    async def test_conversation_context_management(self):
        """Test conversation context is maintained"""
        # Mock AI response
        self.mock_ai.process_input = AsyncMock(return_value=AIResponse(
            text="I understand.",
            requires_action=False
        ))
        
        # Mock memory operations
        self.mock_memory.store_interaction = AsyncMock()
        
        # Process first input
        await self.service.process_text_input("Remember my name is John")
        
        # Check conversation context
        assert len(self.service.conversation_context) == 2  # user + assistant
        assert self.service.conversation_context[0]["role"] == "user"
        assert self.service.conversation_context[0]["content"] == "Remember my name is John"
        assert self.service.conversation_context[1]["role"] == "assistant"
        assert self.service.conversation_context[1]["content"] == "I understand."
        
        # Process second input
        await self.service.process_text_input("What's my name?")
        
        # Verify AI was called with conversation history
        ai_call = self.mock_ai.process_input.call_args_list[1]
        conversation_history = ai_call[1]["conversation_history"]
        assert len(conversation_history) >= 2
    
    def test_clear_conversation_context(self):
        """Test clearing conversation context"""
        # Add some context
        self.service.conversation_context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        # Clear context
        self.service.clear_conversation_context()
        
        # Verify context is cleared
        assert len(self.service.conversation_context) == 0
        assert self.service.current_conversation_id is None


if __name__ == "__main__":
    # Simple test runner
    async def run_tests():
        test = TestInteractionService()
        
        # Test simple response
        test.setup_method()
        await test.test_process_text_input_simple_response()
        print("✓ Simple response test passed")
        
        # Test with actions
        test.setup_method()
        await test.test_process_text_input_with_actions()
        print("✓ Actions test passed")
        
        # Test conversation context
        test.setup_method()
        await test.test_conversation_context_management()
        print("✓ Conversation context test passed")
        
        # Test clear context
        test.setup_method()
        test.test_clear_conversation_context()
        print("✓ Clear context test passed")
        
        print("\nAll tests passed! ✓")
    
    asyncio.run(run_tests())
