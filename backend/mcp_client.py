"""
MCP Client for PRISM
Integrates Model Context Protocol servers with the PRISM assistant
"""

import asyncio
import json
import base64
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from contextlib import AsyncExitStack
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from loguru import logger
import google.generativeai as genai
from PIL import Image
from io import BytesIO


class ExecutionMode(Enum):
    """Execution strategy for MCP operations"""
    MCP_ONLY = "mcp_only"
    VISION_FALLBACK = "vision_fallback"
    PARALLEL = "parallel"


@dataclass
class MCPResult:
    """Result from MCP operation"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None
    fallback_used: bool = False


class PRISMMCPClient:
    """
    MCP client that provides screen visibility, app control, and parallel execution
    Integrates with Gemini for intelligent decision making
    """
    
    def __init__(self, gemini_model: str = "gemini-1.5-flash"):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.gemini_model = gemini_model
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Cache for MCP tools
        self.available_tools: List[Dict[str, Any]] = []
        self.tools_by_name: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.vision_fallback_enabled = True
        self.parallel_execution_enabled = True
        
        logger.info("PRISM MCP Client initialized")
    
    async def initialize(self, server_script_path: str = None):
        """
        Initialize MCP client connection to Windows server
        
        Args:
            server_script_path: Path to MCP server script
        """
        try:
            if server_script_path is None:
                # Use default Windows server
                server_script_path = str(Path(__file__).parent / "mcp_windows_server.py")
            
            logger.info(f"Connecting to MCP server: {server_script_path}")
            
            # Connect to server
            server_params = StdioServerParameters(
                command="python",
                args=[server_script_path],
                env=None
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            await self.session.initialize()
            
            # Discover available tools
            await self._discover_tools()
            
            logger.success(f"MCP Client connected with {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            raise
    
    async def _discover_tools(self):
        """Discover and cache available MCP tools"""
        try:
            response = await self.session.list_tools()
            self.available_tools = []
            self.tools_by_name = {}
            
            for tool in response.tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                self.available_tools.append(tool_info)
                self.tools_by_name[tool.name] = tool_info
            
            logger.info(f"Discovered {len(self.available_tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
    
    async def get_screen_context(self) -> MCPResult:
        """
        Get comprehensive screen context using MCP
        
        Returns:
            MCPResult with screen information
        """
        try:
            # Get screen info
            screen_result = await self.call_tool("get_screen_info")
            if not screen_result.success:
                return screen_result
            
            # Get active windows
            windows_result = await self.call_tool("list_active_windows")
            if not windows_result.success:
                return windows_result
            
            # Get running processes
            processes_result = await self.call_tool("list_running_processes")
            
            screen_data = json.loads(screen_result.data)
            windows_data = json.loads(windows_result.data)
            processes_data = json.loads(processes_result.data) if processes_result.success else []
            
            context = {
                "screen": screen_data,
                "active_windows": windows_data,
                "running_processes": processes_data,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            return MCPResult(
                success=True,
                data=context,
                execution_mode=ExecutionMode.MCP_ONLY
            )
            
        except Exception as e:
            logger.error(f"Error getting screen context: {e}")
            return MCPResult(success=False, error=str(e))
    
    async def analyze_screen_with_vision(self, screenshot_base64: str, question: str) -> MCPResult:
        """
        Analyze screenshot using Gemini Vision
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            question: What to analyze in the screenshot
            
        Returns:
            MCPResult with vision analysis
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(BytesIO(image_data))
            
            # Prepare prompt
            prompt = f"Analyze this screenshot and answer: {question}. Be specific and concise."
            
            # Call Gemini Vision
            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content([prompt, image])
            
            return MCPResult(
                success=True,
                data={
                    "analysis": response.text,
                    "question": question,
                    "model": self.gemini_model
                },
                execution_mode=ExecutionMode.VISION_FALLBACK,
                fallback_used=True
            )
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return MCPResult(success=False, error=str(e))
    
    async def execute_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[MCPResult]:
        """
        Execute multiple MCP tasks in parallel
        
        Args:
            tasks: List of task dictionaries with 'tool' and 'parameters'
            
        Returns:
            List of MCPResults
        """
        if not self.parallel_execution_enabled:
            # Execute sequentially
            results = []
            for task in tasks:
                result = await self.call_tool(task["tool"], **task.get("parameters", {}))
                results.append(result)
            return results
        
        try:
            # Create parallel tasks
            loop = asyncio.get_event_loop()
            
            async def execute_single_task(task):
                return await self.call_tool(task["tool"], **task.get("parameters", {}))
            
            # Execute all tasks in parallel
            results = await asyncio.gather(
                *[execute_single_task(task) for task in tasks],
                return_exceptions=True
            )
            
            # Convert exceptions to error results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(MCPResult(success=False, error=str(result)))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in parallel execution: {e}")
            return [MCPResult(success=False, error=str(e)) for _ in tasks]
    
    async def call_tool(self, tool_name: str, **kwargs) -> MCPResult:
        """
        Call an MCP tool with parameters
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool parameters
            
        Returns:
            MCPResult with tool response
        """
        try:
            if not self.session:
                return MCPResult(success=False, error="MCP session not initialized")
            
            if tool_name not in self.tools_by_name:
                return MCPResult(success=False, error=f"Tool '{tool_name}' not available")
            
            logger.info(f"Calling MCP tool: {tool_name} with params: {kwargs}")
            
            result = await self.session.call_tool(tool_name, kwargs)
            
            # Parse result content
            content = result.content[0] if result.content else None
            if content and hasattr(content, 'text'):
                data = content.text
            else:
                data = str(content)
            
            return MCPResult(
                success=True,
                data=data,
                execution_mode=ExecutionMode.MCP_ONLY
            )
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return MCPResult(success=False, error=str(e))
    
    async def get_contextual_screen_analysis(self) -> MCPResult:
        """
        Get contextual analysis of what the user is actually doing on screen
        
        Returns:
            MCPResult with contextual understanding and actionable insights
        """
        try:
            # Get comprehensive screen context
            screen_context = await self.get_screen_context()
            if not screen_context.success:
                return screen_context
            
            data = screen_context.data
            active_windows = data.get("active_windows", [])
            running_processes = data.get("running_processes", [])
            
            # Analyze user activity context
            context_analysis = {
                "current_activity": "unknown",
                "primary_applications": [],
                "development_environment": False,
                "browser_active": False,
                "communication_apps": [],
                "automation_opportunities": []
            }
            
            # Identify primary applications and user activity
            dev_apps = ["code", "vscode", "windsurf", "pycharm", "intellij", "sublime", "atom"]
            browsers = ["chrome", "firefox", "edge", "safari", "opera"]
            communication = ["slack", "discord", "teams", "zoom", "outlook", "telegram"]
            
            active_apps = [w["title"] for w in active_windows if w.get("active", False)]
            foreground_titles = [w["title"] for w in active_windows if not w.get("minimized", True)]
            
            # Analyze running processes for context
            process_names = [p["name"].lower() for p in running_processes]
            
            # Check for development environment
            if any(dev in " ".join(process_names) for dev in dev_apps):
                context_analysis["development_environment"] = True
                context_analysis["current_activity"] = "coding/development"
                
                # Find specific dev tools
                for proc in running_processes:
                    proc_name = proc["name"].lower()
                    if any(dev in proc_name for dev in dev_apps):
                        context_analysis["primary_applications"].append(proc["name"])
            
            # Check for browser activity
            if any(browser in " ".join(process_names) for browser in browsers):
                context_analysis["browser_active"] = True
                if context_analysis["current_activity"] == "unknown":
                    context_analysis["current_activity"] = "browsing"
                
                for proc in running_processes:
                    proc_name = proc["name"].lower()
                    if any(browser in proc_name for browser in browsers):
                        context_analysis["primary_applications"].append(proc["name"])
            
            # Check for communication apps
            for proc in running_processes:
                proc_name = proc["name"].lower()
                if any(comm in proc_name for comm in communication):
                    context_analysis["communication_apps"].append(proc["name"])
                    if context_analysis["current_activity"] == "unknown":
                        context_analysis["current_activity"] = "communication"
            
            # Identify automation opportunities
            opportunities = []
            
            # Development automation opportunities
            if context_analysis["development_environment"]:
                opportunities.extend([
                    "Write and execute code commands",
                    "Create and edit files programmatically", 
                    "Run build/test commands",
                    "Generate documentation",
                    "Refactor code patterns"
                ])
            
            # Browser automation opportunities  
            if context_analysis["browser_active"]:
                opportunities.extend([
                    "Fill forms automatically",
                    "Navigate to specific URLs",
                    "Extract data from web pages",
                    "Take screenshots of content",
                    "Automate repetitive browsing tasks"
                ])
            
            # Communication automation
            if context_analysis["communication_apps"]:
                opportunities.extend([
                    "Send automated messages",
                    "Schedule meetings",
                    "Extract conversation summaries",
                    "Automate status updates"
                ])
            
            context_analysis["automation_opportunities"] = opportunities
            
            # Generate human-readable summary
            summary = self._generate_activity_summary(context_analysis, active_windows)
            
            result_data = {
                "context": context_analysis,
                "active_windows": active_windows,
                "summary": summary,
                "automation_ready": True
            }
            
            return MCPResult(
                success=True,
                data=result_data,
                execution_mode=ExecutionMode.MCP_ONLY
            )
            
        except Exception as e:
            logger.error(f"Error in contextual screen analysis: {e}")
            return MCPResult(success=False, error=str(e))
    
    def _generate_activity_summary(self, context: Dict[str, Any], windows: List[Dict[str, Any]]) -> str:
        """Generate human-readable summary of user's current activity"""
        
        activity = context.get("current_activity", "unknown")
        apps = context.get("primary_applications", [])
        active_titles = [w["title"] for w in windows if w.get("active", False)]
        
        summaries = {
            "coding/development": f"You're currently coding with {', '.join(apps)}. I can help write code, run commands, or automate development tasks.",
            "browsing": f"You're browsing the web with {', '.join(apps)}. I can help navigate pages, fill forms, or extract information.",
            "communication": f"You're using communication apps: {', '.join(apps)}. I can help send messages or automate communications.",
            "unknown": f"I can see you have {len(windows)} windows open. I can help automate tasks across your applications."
        }
        
        base_summary = summaries.get(activity, summaries["unknown"])
        
        # Add specific window context
        if active_titles:
            base_summary += f"\n\nCurrently focused on: {active_titles[0]}"
        
        # Add automation call to action
        if context.get("automation_opportunities"):
            base_summary += "\n\nI can help you automate tasks like:\n"
            for opportunity in context["automation_opportunities"][:3]:
                base_summary += f"• {opportunity}\n"
        
        return base_summary
    
    async def intelligent_screen_analysis(self, query: str) -> MCPResult:
        """
        Intelligently analyze screen using MCP + Vision fallback
        
        Args:
            query: What the user wants to know about the screen
            
        Returns:
            MCPResult with comprehensive analysis
        """
        try:
            # Step 1: Get structured screen context via MCP
            screen_context = await self.get_screen_context()
            if not screen_context.success:
                return screen_context
            
            # Step 2: Determine if vision analysis is needed
            needs_vision = await self._determine_vision_need(query, screen_context.data)
            
            if needs_vision and self.vision_fallback_enabled:
                # Step 3: Take screenshot and analyze with vision
                screenshot_result = await self.call_tool("take_screenshot")
                if screenshot_result.success:
                    screenshot_data = json.loads(screenshot_result.data)
                    if screenshot_data.get("success"):
                        vision_result = await self.analyze_screen_with_vision(
                            screenshot_data["screenshot"], 
                            query
                        )
                        
                        if vision_result.success:
                            # Combine MCP and Vision results
                            combined_data = {
                                "structured_context": screen_context.data,
                                "vision_analysis": vision_result.data,
                                "query": query,
                                "execution_mode": "hybrid"
                            }
                            
                            return MCPResult(
                                success=True,
                                data=combined_data,
                                execution_mode=ExecutionMode.VISION_FALLBACK,
                                fallback_used=True
                            )
            
            # Return MCP-only result
            return MCPResult(
                success=True,
                data={
                    "structured_context": screen_context.data,
                    "query": query,
                    "execution_mode": "mcp_only"
                },
                execution_mode=ExecutionMode.MCP_ONLY,
                fallback_used=False
            )
            
        except Exception as e:
            logger.error(f"Error in intelligent screen analysis: {e}")
            return MCPResult(success=False, error=str(e))
    
    async def _determine_vision_need(self, query: str, screen_context: Dict[str, Any]) -> bool:
        """
        Use LLM to determine if vision analysis is needed for the query
        
        Args:
            query: User query
            screen_context: Structured screen context from MCP
            
        Returns:
            True if vision analysis is recommended
        """
        try:
            # Simple heuristic-based approach for now
            vision_keywords = [
                "what", "see", "show", "display", "content", "text", "reading",
                "video", "image", "website", "document", "visual", "look"
            ]
            
            query_lower = query.lower()
            return any(keyword in query_lower for keyword in vision_keywords)
            
        except Exception as e:
            logger.error(f"Error determining vision need: {e}")
            return False
    
    async def close_application_smart(self, app_identifier: str) -> MCPResult:
        """
        Intelligently close application using multiple strategies
        
        Args:
            app_identifier: App name, window title, or process name
            
        Returns:
            MCPResult with operation outcome
        """
        try:
            # Try exact match first
            result = await self.call_tool("close_application", name=app_identifier)
            if result.success:
                return result
            
            # Try to find matching window
            windows_result = await self.call_tool("list_active_windows")
            if windows_result.success:
                windows = json.loads(windows_result.data)
                for window in windows:
                    if app_identifier.lower() in window["title"].lower():
                        return await self.call_tool("close_application", name=window["title"])
            
            # Try to find matching process
            processes_result = await self.call_tool("list_running_processes")
            if processes_result.success:
                processes = json.loads(processes_result.data)
                for process in processes:
                    if app_identifier.lower() in process["name"].lower():
                        return await self.call_tool("close_application", name=process["name"])
            
            return MCPResult(
                success=False,
                error=f"Could not find application: {app_identifier}"
            )
            
        except Exception as e:
            logger.error(f"Error in smart application closing: {e}")
            return MCPResult(success=False, error=str(e))
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        return self.available_tools.copy()
    
    async def shutdown(self):
        """Shutdown MCP client"""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
            
            await self.exit_stack.aclose()
            logger.info("MCP Client shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during MCP client shutdown: {e}")


# Global MCP client instance
mcp_client = PRISMMCPClient()
