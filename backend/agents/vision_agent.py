"""
Vision Agent - Computer Vision for UI Understanding
Enables PRISM to see and interact with UI elements autonomously
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from PIL import Image, ImageDraw
import io
import base64
import json

from backend.agents.base_agent import BaseAgent, AgentCapability, AgentResult

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available for vision")

try:
    from mss import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    logger.warning("mss not available for screenshots")


class VisionAgent(BaseAgent):
    """
    Agent that uses computer vision to understand and interact with UI elements.
    
    Capabilities:
    - Take screenshots
    - Identify UI elements (buttons, text fields, etc.)
    - Find clickable coordinates for elements
    - Verify UI state
    - Navigate applications visually
    """
    
    def __init__(self, gemini_api_key: str = None):
        super().__init__(
            name="VisionAgent",
            description="Computer vision agent for autonomous UI interaction",
            capabilities=[AgentCapability.SYSTEM_CONTROL]
        )
        self.gemini_api_key = gemini_api_key
        self.vision_model = None
        self.last_screenshot = None
        self.ui_element_cache = {}
        
    async def initialize(self) -> bool:
        """Initialize vision model"""
        try:
            if not GEMINI_AVAILABLE:
                logger.warning("Gemini not available, vision features limited")
                return True
                
            if not self.gemini_api_key:
                logger.warning("No Gemini API key, vision features limited")
                return True
            
            # Initialize Gemini with vision capabilities
            genai.configure(api_key=self.gemini_api_key)
            
            # Use Gemini 2.0 Flash for vision (supports image input)
            self.vision_model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                generation_config={
                    "temperature": 0.1,  # Low temperature for precise UI understanding
                    "max_output_tokens": 2048,
                }
            )
            
            logger.success("VisionAgent initialized with Gemini vision model")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing VisionAgent: {e}")
            return False
    
    async def execute(self, task: str, parameters: Dict[str, Any]) -> AgentResult:
        """Execute vision-based tasks"""
        try:
            if task == "find_ui_element":
                return await self._find_ui_element(parameters)
            elif task == "click_element":
                return await self._click_element(parameters)
            elif task == "verify_ui_state":
                return await self._verify_ui_state(parameters)
            elif task == "navigate_to_element":
                return await self._navigate_to_element(parameters)
            elif task == "take_screenshot":
                return await self._take_screenshot(parameters)
            else:
                return AgentResult(
                    success=False,
                    message=f"Unknown vision task: {task}",
                    data={}
                )
                
        except Exception as e:
            logger.error(f"VisionAgent error executing {task}: {e}", exc_info=True)
            return AgentResult(
                success=False,
                message=f"Vision task failed: {str(e)}",
                data={}
            )
    
    async def _take_screenshot(self, parameters: Dict[str, Any]) -> AgentResult:
        """Take a screenshot of the current screen"""
        if not MSS_AVAILABLE:
            return AgentResult(
                success=False,
                message="Screenshot library not available",
                data={}
            )
        
        try:
            with mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                
                # Store for later use
                self.last_screenshot = img
                
                # Optionally save to file
                if parameters.get("save_path"):
                    img.save(parameters["save_path"])
                
                return AgentResult(
                    success=True,
                    message="Screenshot captured",
                    data={
                        "width": img.width,
                        "height": img.height,
                        "image": img
                    }
                )
                
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return AgentResult(
                success=False,
                message=f"Failed to capture screenshot: {str(e)}",
                data={}
            )
    
    async def _find_ui_element(self, parameters: Dict[str, Any]) -> AgentResult:
        """
        Find a UI element on screen using vision model
        
        Parameters:
            element_description: Natural language description of element to find
            window_title: Optional window to focus on
        """
        element_desc = parameters.get("element_description", "")
        
        if not element_desc:
            return AgentResult(
                success=False,
                message="No element description provided",
                data={}
            )
        
        # Take screenshot
        screenshot_result = await self._take_screenshot({})
        if not screenshot_result.success:
            return screenshot_result
        
        img = screenshot_result.data["image"]
        
        # Use vision model to find element
        if self.vision_model:
            try:
                # Convert image to bytes for Gemini
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Create prompt for element detection
                prompt = f"""Analyze this screenshot and find the UI element: "{element_desc}"

Respond with a JSON object containing:
1. "found": true/false - whether the element was found
2. "x": approximate X coordinate (0-{img.width})
3. "y": approximate Y coordinate (0-{img.height})
4. "confidence": 0.0-1.0 confidence score
5. "description": brief description of what you found
6. "type": element type (button, text_field, search_box, etc.)

Example response:
{{
  "found": true,
  "x": 450,
  "y": 300,
  "confidence": 0.95,
  "description": "Message input field at bottom of chat window",
  "type": "text_field"
}}

Respond ONLY with the JSON object, no other text."""

                # Call vision model
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.vision_model.generate_content([prompt, img_byte_arr])
                )
                
                # Parse response
                response_text = response.text.strip()
                
                # Extract JSON
                if "```json" in response_text:
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                elif "```" in response_text:
                    import re
                    json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                result_data = json.loads(response_text)
                
                if result_data.get("found"):
                    logger.success(f"Found UI element: {result_data.get('description')}")
                    return AgentResult(
                        success=True,
                        message=f"Found: {result_data.get('description')}",
                        data=result_data
                    )
                else:
                    return AgentResult(
                        success=False,
                        message=f"Could not find element: {element_desc}",
                        data=result_data
                    )
                    
            except Exception as e:
                logger.error(f"Vision model error: {e}")
                return AgentResult(
                    success=False,
                    message=f"Vision analysis failed: {str(e)}",
                    data={}
                )
        else:
            return AgentResult(
                success=False,
                message="Vision model not available",
                data={}
            )
    
    async def _click_element(self, parameters: Dict[str, Any]) -> AgentResult:
        """
        Find and click a UI element
        
        Parameters:
            element_description: What to click
            verify: Whether to verify click succeeded
        """
        # First find the element
        find_result = await self._find_ui_element(parameters)
        
        if not find_result.success:
            return find_result
        
        # Get coordinates
        x = find_result.data.get("x")
        y = find_result.data.get("y")
        
        if x is None or y is None:
            return AgentResult(
                success=False,
                message="No coordinates found for element",
                data={}
            )
        
        # Click at coordinates using MCP
        from backend.mcp_client import MCPClient
        # This would need to be injected or accessed via coordinator
        # For now, return coordinates for coordinator to handle
        
        return AgentResult(
            success=True,
            message=f"Element located at ({x}, {y})",
            data={
                "action": "click",
                "x": x,
                "y": y,
                "element": find_result.data
            }
        )
    
    async def _verify_ui_state(self, parameters: Dict[str, Any]) -> AgentResult:
        """
        Verify the current UI state matches expectations
        
        Parameters:
            expected_state: Description of expected UI state
        """
        expected = parameters.get("expected_state", "")
        
        if not expected:
            return AgentResult(
                success=False,
                message="No expected state provided",
                data={}
            )
        
        # Take screenshot
        screenshot_result = await self._take_screenshot({})
        if not screenshot_result.success:
            return screenshot_result
        
        img = screenshot_result.data["image"]
        
        if self.vision_model:
            try:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                prompt = f"""Analyze this screenshot and verify if the UI state matches: "{expected}"

Respond with a JSON object:
{{
  "matches": true/false,
  "confidence": 0.0-1.0,
  "current_state": "description of what you see",
  "differences": "what doesn't match (if any)"
}}

Respond ONLY with JSON, no other text."""

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.vision_model.generate_content([prompt, img_byte_arr])
                )
                
                response_text = response.text.strip()
                
                # Extract JSON
                if "```json" in response_text:
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                result_data = json.loads(response_text)
                
                return AgentResult(
                    success=result_data.get("matches", False),
                    message=result_data.get("current_state", "State verified"),
                    data=result_data
                )
                
            except Exception as e:
                logger.error(f"UI verification error: {e}")
                return AgentResult(
                    success=False,
                    message=f"Verification failed: {str(e)}",
                    data={}
                )
        else:
            return AgentResult(
                success=False,
                message="Vision model not available",
                data={}
            )
    
    async def _navigate_to_element(self, parameters: Dict[str, Any]) -> AgentResult:
        """
        Navigate to a UI element through a series of steps
        
        Parameters:
            target_element: Final element to reach
            steps: Optional list of intermediate steps
        """
        target = parameters.get("target_element", "")
        steps = parameters.get("steps", [])
        
        results = []
        
        # Execute each step
        for step in steps:
            result = await self._click_element({"element_description": step})
            results.append(result)
            
            if not result.success:
                return AgentResult(
                    success=False,
                    message=f"Navigation failed at step: {step}",
                    data={"completed_steps": results}
                )
            
            # Small delay between steps
            await asyncio.sleep(0.5)
        
        # Final target
        final_result = await self._click_element({"element_description": target})
        results.append(final_result)
        
        return AgentResult(
            success=final_result.success,
            message=f"Navigation completed to: {target}",
            data={"all_steps": results}
        )
    
    async def shutdown(self) -> bool:
        """Cleanup vision resources"""
        self.last_screenshot = None
        self.ui_element_cache.clear()
        return True
