"""
Windows MCP Server
Provides Model Context Protocol tools for Windows system control, screen visibility, and app management
"""

import asyncio
import json
import platform
import subprocess
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

import pyautogui
import psutil
from pywinauto import Application, Desktop
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool, TextContent
from loguru import logger

# Configure pyautogui safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Create MCP server
mcp = FastMCP("Windows Control Server")


class WindowsInfo:
    """Windows system information and control utilities"""
    
    @staticmethod
    def get_active_windows() -> List[Dict[str, Any]]:
        """Get list of active windows with detailed information"""
        try:
            windows = []
            desktop = Desktop(backend="uia")
            
            for window in desktop.windows():
                if window.is_visible() and window.window_text():
                    try:
                        rect = window.rectangle()
                        windows.append({
                            "title": window.window_text(),
                            "handle": str(window.handle),
                            "class_name": window.class_name(),
                            "process_id": window.process_id(),
                            "visible": window.is_visible(),
                            "minimized": window.is_minimized(),
                            "maximized": window.is_maximized(),
                            "position": {"x": rect.left, "y": rect.top},
                            "size": {"width": rect.width(), "height": rect.height()},
                            "active": window.is_active()
                        })
                    except Exception as e:
                        logger.debug(f"Error getting window info: {e}")
                        continue
            
            return windows
        except Exception as e:
            logger.error(f"Error getting active windows: {e}")
            return []
    
    @staticmethod
    def get_running_processes() -> List[Dict[str, Any]]:
        """Get list of running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "exe": proc.info.get('exe', ''),
                        "cpu_percent": proc.info.get('cpu_percent', 0),
                        "memory_percent": proc.info.get('memory_percent', 0),
                        "status": proc.status()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            logger.error(f"Error getting running processes: {e}")
            return []
    
    @staticmethod
    def get_screen_info() -> Dict[str, Any]:
        """Get screen resolution and display information"""
        try:
            screen_width, screen_height = pyautogui.size()
            return {
                "resolution": {"width": screen_width, "height": screen_height},
                "primary_monitor": {
                    "width": screen_width,
                    "height": screen_height,
                    "position": {"x": 0, "y": 0}
                }
            }
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            return {}


# MCP Tools

@mcp.tool()
def list_active_windows() -> str:
    """
    List all active windows with their details including position, size, and state
    
    Returns:
        JSON string containing array of window information
    """
    try:
        windows = WindowsInfo.get_active_windows()
        return json.dumps(windows, indent=2)
    except Exception as e:
        logger.error(f"Error in list_active_windows: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_running_processes() -> str:
    """
    List all running processes with their resource usage
    
    Returns:
        JSON string containing array of process information
    """
    try:
        processes = WindowsInfo.get_running_processes()
        return json.dumps(processes, indent=2)
    except Exception as e:
        logger.error(f"Error in list_running_processes: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_memory_info() -> str:
    """
    Get system memory (RAM) usage information
    
    Returns:
        JSON string containing memory statistics
    """
    try:
        mem = psutil.virtual_memory()
        return json.dumps({
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent_used": mem.percent,
            "free_gb": round(mem.free / (1024**3), 2)
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in get_memory_info: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_screen_info() -> str:
    """
    Get screen resolution and display information
    
    Returns:
        JSON string containing screen information
    """
    try:
        screen_info = WindowsInfo.get_screen_info()
        return json.dumps(screen_info, indent=2)
    except Exception as e:
        logger.error(f"Error in get_screen_info: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def focus_window(title: str) -> str:
    """
    Focus and bring a window to the front by title
    
    Args:
        title: Window title to focus (supports partial matching and app name aliases)
    
    Returns:
        Success/failure message
    """
    import time
    
    try:
        # App name aliases for better matching
        app_aliases = {
            'telegram': ['telegram', 'telegram desktop', 'telegram.exe'],
            'chrome': ['chrome', 'google chrome', 'chrome.exe'],
            'edge': ['edge', 'microsoft edge', 'msedge.exe'],
            'notepad': ['notepad', 'notepad.exe', 'untitled'],
            'whatsapp': ['whatsapp', 'whatsapp desktop', 'whatsapp.exe'],
            'discord': ['discord', 'discord.exe'],
            'spotify': ['spotify', 'spotify.exe'],
            'vscode': ['visual studio code', 'code.exe', 'vscode'],
            'windsurf': ['windsurf', 'windsurf.exe']
        }
        
        # Get possible titles to match
        title_lower = title.lower()
        possible_titles = [title_lower]
        
        # Add aliases if the title matches an app name
        for app, aliases in app_aliases.items():
            if app in title_lower or title_lower in app:
                possible_titles.extend([alias.lower() for alias in aliases])
        
        # Retry logic for newly opened windows
        max_retries = 5  # Increased retries for better reliability
        retry_delay = 0.3  # Shorter delay for faster response
        
        for attempt in range(max_retries):
            desktop = Desktop(backend="uia")
            windows = desktop.windows()
            
            # Find window with matching title (improved matching logic)
            target_window = None
            best_match_score = 0
            
            for window in windows:
                try:
                    if not window.is_visible():
                        continue
                        
                    window_title = window.window_text().lower()
                    if not window_title:  # Skip windows with no title
                        continue
                    
                    # Calculate match score
                    match_score = 0
                    for possible_title in possible_titles:
                        if possible_title in window_title:
                            match_score = max(match_score, len(possible_title) / len(window_title))
                        elif window_title in possible_title:
                            match_score = max(match_score, len(window_title) / len(possible_title))
                    
                    # Update best match if this is better
                    if match_score > best_match_score:
                        best_match_score = match_score
                        target_window = window
                        
                except Exception as e:
                    logger.debug(f"Error checking window: {e}")
                    continue
            
            if target_window and best_match_score > 0.3:  # Minimum match threshold
                try:
                    if target_window.is_minimized():
                        target_window.restore()
                    target_window.set_focus()
                    return json.dumps({
                        "success": True,
                        "message": f"Focused window: {target_window.window_text()}"
                    })
                except Exception as e:
                    logger.warning(f"Failed to focus window: {e}")
                    continue
            
            # If not found and not last attempt, wait and retry
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        # All retries exhausted - provide helpful debug info
        available_windows = []
        try:
            desktop = Desktop(backend="uia")
            for window in desktop.windows():
                if window.is_visible() and window.window_text():
                    available_windows.append(window.window_text())
        except:
            pass
        
        debug_info = f"Available windows: {', '.join(available_windows[:5])}" if available_windows else "No visible windows found"
        
        return json.dumps({
            "success": False,
            "message": f"No window found matching: {title}. {debug_info}"
        })
            
    except Exception as e:
        logger.error(f"Error focusing window: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def close_application(name: str) -> str:
    """
    Close an application by name or window title
    
    Args:
        name: Application name or window title to close
    
    Returns:
        Success/failure message
    """
    try:
        logger.info(f"Attempting to close application: {name}")
        
        # CRITICAL: Self-protection - never close PRISM itself
        protected_names = ['prism', 'electron', 'python.exe']
        if any(protected in name.lower() for protected in protected_names):
            logger.warning(f"Blocked attempt to close protected process: {name}")
            return json.dumps({
                "success": False,
                "message": f"Cannot close {name} - this is a protected system process"
            })
        
        # Normalize search term - remove common suffixes and extensions
        search_term = name.lower().strip()
        
        # Try to find process by name first
        logger.debug(f"Searching for process matching: {search_term}")
        found_processes = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                
                # Additional protection: check if this is PRISM's own process
                if any(protected in proc_name for protected in protected_names):
                    continue
                
                # Match if search term is in process name OR process name (without .exe) matches search term
                proc_name_base = proc_name.replace('.exe', '').replace('.', '')
                
                if search_term in proc_name or search_term in proc_name_base or proc_name_base.startswith(search_term):
                    found_processes.append(proc)
                    logger.debug(f"Found matching process: {proc.info['name']} (PID: {proc.info['pid']})")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Close all matching processes
        if found_processes:
            closed_names = []
            for proc in found_processes:
                try:
                    proc_name = proc.info['name']
                    pid = proc.info['pid']
                    proc.terminate()
                    closed_names.append(f"{proc_name} (PID: {pid})")
                    logger.info(f"Terminated process: {proc_name} (PID: {pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.warning(f"Could not terminate process {proc.info['name']}: {e}")
            
            if closed_names:
                return json.dumps({
                    "success": True,
                    "message": f"Closed process(es): {', '.join(closed_names)}"
                })
        
        # Try to find window by title
        logger.debug(f"Searching for window matching: {search_term}")
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        
        for window in windows:
            try:
                window_title = window.window_text()
                window_title_lower = window_title.lower()
                
                # Additional protection: check if window title contains PRISM
                if 'prism' in window_title_lower:
                    continue
                
                if window.is_visible() and search_term in window_title_lower:
                    logger.info(f"Found matching window: {window_title}")
                    window.close()
                    return json.dumps({
                        "success": True,
                        "message": f"Closed window: {window_title}"
                    })
            except Exception as e:
                logger.debug(f"Error checking window: {e}")
                continue
        
        logger.warning(f"No application found with name: {name}")
        return json.dumps({
            "success": False,
            "message": f"No application found with name: {name}"
        })
        
    except Exception as e:
        logger.error(f"Error closing application: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def minimize_window(title: str) -> str:
    """
    Minimize a window by title
    
    Args:
        title: Window title to minimize
    
    Returns:
        Success/failure message
    """
    try:
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        
        for window in windows:
            if window.is_visible() and title.lower() in window.window_text().lower():
                window.minimize()
                return json.dumps({
                    "success": True,
                    "message": f"Minimized window: {window.window_text()}"
                })
        
        return json.dumps({
            "success": False,
            "message": f"No window found with title containing: {title}"
        })
        
    except Exception as e:
        logger.error(f"Error minimizing window: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def maximize_window(title: str) -> str:
    """
    Maximize a window by title
    
    Args:
        title: Window title to maximize
    
    Returns:
        Success/failure message
    """
    try:
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        
        for window in windows:
            if window.is_visible() and title.lower() in window.window_text().lower():
                window.maximize()
                return json.dumps({
                    "success": True,
                    "message": f"Maximized window: {window.window_text()}"
                })
        
        return json.dumps({
            "success": False,
            "message": f"No window found with title containing: {title}"
        })
        
    except Exception as e:
        logger.error(f"Error maximizing window: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def click_at_coordinates(x: int, y: int, button: str = "left") -> str:
    """
    Click at specific screen coordinates
    
    Args:
        x: X coordinate
        y: Y coordinate
        button: Mouse button ('left', 'right', 'middle')
    
    Returns:
        Success/failure message
    """
    try:
        if button == "left":
            pyautogui.click(x, y)
        elif button == "right":
            pyautogui.rightClick(x, y)
        elif button == "middle":
            pyautogui.middleClick(x, y)
        else:
            return json.dumps({"success": False, "error": f"Invalid button: {button}"})
        
        return json.dumps({
            "success": True,
            "message": f"Clicked {button} button at coordinates ({x}, {y})"
        })
        
    except Exception as e:
        logger.error(f"Error clicking at coordinates: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def type_text(text: str, interval: float = 0.01) -> str:
    """
    Type text at current cursor position
    
    Args:
        text: Text to type
        interval: Delay between keystrokes (seconds)
    
    Returns:
        Success/failure message
    """
    try:
        pyautogui.write(text, interval=interval)
        return json.dumps({
            "success": True,
            "message": f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}"
        })
        
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def press_key(key: str) -> str:
    """
    Press a keyboard key
    
    Args:
        key: Key to press (e.g., 'enter', 'ctrl+v', 'alt+tab')
    
    Returns:
        Success/failure message
    """
    try:
        pyautogui.press(key)
        return json.dumps({
            "success": True,
            "message": f"Pressed key: {key}"
        })
        
    except Exception as e:
        logger.error(f"Error pressing key: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def hotkey(key_combo: str) -> str:
    """
    Press a hotkey combination
    
    Args:
        key_combo: Key combination (e.g., 'ctrl+c', 'alt+tab', 'ctrl+s')
    
    Returns:
        Success/failure message
    """
    try:
        pyautogui.hotkey(*key_combo.split('+'))
        return json.dumps({
            "success": True,
            "message": f"Pressed hotkey: {key_combo}"
        })
        
    except Exception as e:
        logger.error(f"Error pressing hotkey: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def find_and_click_element(image_path: str, confidence: float = 0.8) -> str:
    """
    Find an element by image and click on it
    
    Args:
        image_path: Path to image file of the element
        confidence: Confidence threshold for matching (0.0 to 1.0)
    
    Returns:
        Success/failure message with coordinates
    """
    try:
        import os
        if not os.path.exists(image_path):
            return json.dumps({"success": False, "error": f"Image file not found: {image_path}"})
        
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            pyautogui.click(center.x, center.y)
            return json.dumps({
                "success": True,
                "message": f"Found and clicked element at ({center.x}, {center.y})",
                "coordinates": {"x": center.x, "y": center.y}
            })
        else:
            return json.dumps({
                "success": False,
                "error": f"Element not found on screen with confidence {confidence}"
            })
            
    except Exception as e:
        logger.error(f"Error finding and clicking element: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def take_screenshot() -> str:
    """
    Take a screenshot of the entire screen
    
    Returns:
        Base64 encoded screenshot image
    """
    try:
        import base64
        from io import BytesIO
        
        screenshot = pyautogui.screenshot()
        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        screenshot_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return json.dumps({
            "success": True,
            "screenshot": screenshot_base64,
            "format": "PNG",
            "message": "Screenshot taken successfully"
        })
        
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
def get_window_elements(title: str) -> str:
    """
    Get UI elements from a window using UI Automation
    
    Args:
        title: Window title to analyze
    
    Returns:
        JSON string containing UI element tree
    """
    try:
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        
        target_window = None
        for window in windows:
            if window.is_visible() and title.lower() in window.window_text().lower():
                target_window = window
                break
        
        if not target_window:
            return json.dumps({
                "success": False,
                "message": f"No window found with title containing: {title}"
            })
        
        def get_element_info(element, depth=0, max_depth=10):
            """Recursively get element information"""
            if depth > max_depth:
                return None
            
            try:
                rect = element.rectangle()
                info = {
                    "name": element.element_info.name,
                    "control_type": element.element_info.control_type,
                    "automation_id": element.element_info.automation_id,
                    "class_name": element.element_info.class_name,
                    "position": {"x": rect.left, "y": rect.top},
                    "size": {"width": rect.width(), "height": rect.height()},
                    "visible": element.is_visible(),
                    "enabled": element.is_enabled()
                }
                
                # Get children
                children = []
                try:
                    for child in element.children():
                        child_info = get_element_info(child, depth + 1, max_depth)
                        if child_info:
                            children.append(child_info)
                except:
                    pass
                
                if children:
                    info["children"] = children
                
                return info
                
            except Exception as e:
                logger.debug(f"Error getting element info: {e}")
                return None
        
        elements = get_element_info(target_window)
        
        return json.dumps({
            "success": True,
            "window_title": target_window.window_text(),
            "elements": elements
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting window elements: {e}")
        return json.dumps({"success": False, "error": str(e)})


# MCP Resources

@mcp.resource("windows://active")
def get_active_windows_resource() -> str:
    """Resource for getting active windows"""
    windows = WindowsInfo.get_active_windows()
    return json.dumps(windows, indent=2)


@mcp.resource("windows://processes")
def get_processes_resource() -> str:
    """Resource for getting running processes"""
    processes = WindowsInfo.get_running_processes()
    return json.dumps(processes, indent=2)


@mcp.resource("windows://screen")
def get_screen_resource() -> str:
    """Resource for getting screen information"""
    screen_info = WindowsInfo.get_screen_info()
    return json.dumps(screen_info, indent=2)


if __name__ == "__main__":
    logger.info("Starting Windows MCP Server...")
    mcp.run()
