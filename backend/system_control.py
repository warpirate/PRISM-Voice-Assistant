"""
System Control Module
Handles application management, file operations, and system commands
"""

import os
import subprocess
import psutil
import platform
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import shutil
from fuzzywuzzy import fuzz, process


class SystemControl:
    """
    Manages system-level operations:
    - Application launching and management
    - File system operations
    - System commands
    """

    def __init__(self, mcp_client=None):
        self.system = platform.system()
        self.current_dir = Path.home()
        self.mcp_client = mcp_client
        
        # Scan installed applications at startup
        logger.info("Scanning installed applications...")
        self.installed_apps = self.scan_installed_apps()
        self.app_aliases = self.get_app_aliases()
        logger.success(f"Scanned {len(self.installed_apps)} installed applications")
        
        # Legacy application name mappings (kept for backward compatibility)
        self.app_mappings = {
            # Browsers
            "chrome": "chrome.exe" if self.system == "Windows" else "google-chrome",
            "firefox": "firefox.exe" if self.system == "Windows" else "firefox",
            "edge": "msedge.exe" if self.system == "Windows" else "microsoft-edge",
            
            # Productivity
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "code": "code.exe" if self.system == "Windows" else "code",
            "vscode": "code.exe" if self.system == "Windows" else "code",
            
            # File managers
            "explorer": "explorer.exe",
            "files": "explorer.exe",
            
            # Communication
            "discord": "Discord.exe" if self.system == "Windows" else "discord",
            "slack": "slack.exe" if self.system == "Windows" else "slack",
            "teams": "Teams.exe" if self.system == "Windows" else "teams",
            "whatsapp": "WhatsApp.exe" if self.system == "Windows" else "whatsapp",
            
            # Office
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
        }

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a system action
        Returns result dictionary with success status and optional message
        """
        action_type = action.get("type")
        parameters = action.get("parameters", {})
        
        logger.info(f"Executing action: {action_type}")
        
        try:
            if action_type == "open_application":
                return await self.open_application(parameters.get("name"))
            
            elif action_type == "close_application":
                return await self.close_application(parameters.get("name"))
            
            elif action_type == "open_file":
                return await self.open_file(parameters.get("path"))
            
            elif action_type == "search_files":
                return await self.search_files(
                    parameters.get("query"),
                    parameters.get("location", str(self.current_dir))
                )
            
            elif action_type == "create_file":
                return await self.create_file(
                    parameters.get("path"),
                    parameters.get("content", "")
                )
            
            elif action_type == "web_search":
                return await self.web_search(parameters.get("query"))
            
            elif action_type == "system_command":
                return await self.execute_command(parameters.get("command"))
            
            elif action_type == "get_memory_info":
                return await self.get_memory_info()
            
            elif action_type == "mcp_focus_window":
                return await self.mcp_focus_window(parameters.get("title"))
            
            elif action_type == "mcp_hotkey":
                return await self.mcp_hotkey(parameters.get("keys"))
            
            elif action_type == "mcp_type_text":
                return await self.mcp_type_text(parameters.get("text"))
            
            elif action_type == "mcp_press_key":
                return await self.mcp_press_key(parameters.get("key"))
            
            elif action_type == "mcp_click":
                return await self.mcp_click(parameters.get("x"), parameters.get("y"))
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}"
                }
                
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    def scan_installed_apps(self) -> Dict[str, str]:
        """Scan for installed applications on the system."""
        apps = {}
        
        try:
            if self.system == "Windows":
                # Scan common Windows application paths
                paths_to_scan = [
                    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
                    r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
                    r"C:\Program Files",
                    r"C:\Program Files (x86)",
                ]
                
                # Replace %USERNAME% with actual username
                username = os.getenv('USERNAME')
                if username:
                    paths_to_scan = [path.replace('%USERNAME%', username) for path in paths_to_scan]
                
                for path in paths_to_scan:
                    try:
                        if os.path.exists(path):
                            apps.update(self._scan_windows_path(path))
                    except (PermissionError, OSError) as e:
                        logger.debug(f"Could not scan path {path}: {e}")
                        continue
                        
                # Add built-in Windows commands
                apps.update({
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe", 
                    "paint": "mspaint.exe",
                    "task manager": "taskmgr.exe",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe",
                    "powershell": "powershell.exe",
                    "registry editor": "regedit.exe",
                    "control panel": "control.exe",
                    "settings": "ms-settings:",
                    "store": "ms-windows-store:",
                    "terminal": "wt.exe",
                    "windows terminal": "wt.exe",
                })
                
            elif self.system == "Darwin":  # macOS
                try:
                    # Scan Applications folder
                    apps_path = "/Applications"
                    if os.path.exists(apps_path):
                        for app in os.listdir(apps_path):
                            if app.endswith(".app"):
                                app_name = app.replace(".app", "").lower()
                                apps[app_name] = f"open -a '{app_name.title()}'"
                        
                    # Add common macOS commands
                    apps.update({
                        "textedit": "open -a TextEdit",
                        "calculator": "open -a Calculator",
                        "safari": "open -a Safari",
                        "finder": "open -a Finder",
                        "terminal": "open -a Terminal",
                    })
                except (PermissionError, OSError) as e:
                    logger.debug(f"Could not scan macOS applications: {e}")
            
            elif self.system == "Linux":
                try:
                    # Scan for .desktop files
                    desktop_paths = [
                        "/usr/share/applications",
                        "/usr/local/share/applications",
                        os.path.expanduser("~/.local/share/applications")
                    ]
                    
                    for path in desktop_paths:
                        try:
                            if os.path.exists(path):
                                apps.update(self._scan_linux_desktop_files(path))
                        except (PermissionError, OSError) as e:
                            logger.debug(f"Could not scan Linux desktop path {path}: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Could not scan Linux applications: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during app scanning: {e}")
        
        return apps
    
    def _scan_windows_path(self, path: str) -> Dict[str, str]:
        """Scan Windows path for applications."""
        apps = {}
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".lnk"):
                        # Extract app name from shortcut
                        app_name = file.replace(".lnk", "").lower()
                        # Try to resolve the shortcut
                        try:
                            import win32com.client
                            shell = win32com.client.Dispatch("WScript.Shell")
                            shortcut = shell.CreateShortCut(os.path.join(root, file))
                            target_path = shortcut.Targetpath
                            if target_path and os.path.exists(target_path):
                                apps[app_name] = f'"{target_path}"'
                        except ImportError:
                            # Fallback: just use the name
                            apps[app_name] = f"start {app_name}"
                    elif file.endswith(".exe"):
                        app_name = file.replace(".exe", "").lower()
                        apps[app_name] = f'"{os.path.join(root, file)}"'
        except PermissionError:
            pass
        return apps
    
    def _scan_linux_desktop_files(self, path: str) -> Dict[str, str]:
        """Scan Linux .desktop files for applications."""
        apps = {}
        try:
            for file in os.listdir(path):
                if file.endswith(".desktop"):
                    try:
                        with open(os.path.join(path, file), 'r') as f:
                            content = f.read()
                            # Extract app name and exec command
                            name = None
                            exec_cmd = None
                            for line in content.split('\n'):
                                if line.startswith('Name='):
                                    name = line.split('=', 1)[1].strip().lower()
                                elif line.startswith('Exec='):
                                    exec_cmd = line.split('=', 1)[1].strip().split()[0]
                            if name and exec_cmd:
                                apps[name] = exec_cmd
                    except:
                        continue
        except PermissionError:
            pass
        return apps
    
    def get_app_aliases(self) -> Dict[str, List[str]]:
        """Get common aliases for applications."""
        return {
            "chrome": ["google chrome", "browser", "web browser", "chrome browser"],
            "firefox": ["mozilla firefox", "ff", "firefox browser"],
            "edge": ["microsoft edge", "ms edge", "edge browser"],
            "vs code": ["visual studio code", "vscode", "code editor", "code"],
            "notepad": ["text editor", "notepad++", "notepad plus plus"],
            "calculator": ["calc", "calc.exe"],
            "spotify": ["music player", "spotify music"],
            "discord": ["discord chat", "discord app"],
            "slack": ["slack chat", "slack workspace"],
            "word": ["microsoft word", "ms word", "word processor"],
            "excel": ["microsoft excel", "ms excel", "spreadsheet"],
            "powerpoint": ["microsoft powerpoint", "ms powerpoint", "presentation"],
            "photoshop": ["adobe photoshop", "photo editor", "ps"],
            "illustrator": ["adobe illustrator", "vector editor", "ai"],
        }
    
    def find_best_app_match(self, user_input: str) -> Tuple[Optional[str], Optional[str], int]:
        """Find the best matching application using fuzzy search."""
        user_input_clean = user_input.lower().strip()
        
        # Create a list of all possible app names and their commands
        all_apps = {}
        for app_name, command in self.installed_apps.items():
            all_apps[app_name] = command
            
        # Add aliases to the search pool
        for canonical_name, aliases in self.app_aliases.items():
            if canonical_name in self.installed_apps:
                for alias in aliases:
                    all_apps[alias] = self.installed_apps[canonical_name]
        
        # Use fuzzy matching to find the best match
        best_match = process.extractOne(user_input_clean, list(all_apps.keys()), scorer=fuzz.ratio)
        
        if best_match and best_match[1] >= 60:  # 60% similarity threshold
            matched_name = best_match[0]
            command = all_apps[matched_name]
            
            # Find the canonical name for display
            canonical_name = matched_name
            for app_name in self.installed_apps:
                if matched_name == app_name or matched_name in self.app_aliases.get(app_name, []):
                    canonical_name = app_name
                    break
                    
            return canonical_name, command, best_match[1]
        
        return None, None, 0

    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application by name with fuzzy matching and typo tolerance."""
        if not app_name:
            return {"success": False, "message": "I need an application name to open something for you."}
        
        original_name = app_name
        logger.info(f"Opening application: '{original_name}'")
        
        try:
            # Use fuzzy matching to find the best match
            canonical_name, command, confidence = self.find_best_app_match(app_name)
            
            if canonical_name and command:
                logger.info(f"Matched '{original_name}' to '{canonical_name}' (confidence: {confidence}%)")
                logger.info(f"Executing command: {command}")
                
                # Handle different command types
                if command.startswith('"') and command.endswith('"'):
                    # Direct path execution
                    subprocess.Popen(command.strip('"'), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif command.startswith('open -a'):
                    # macOS open command
                    subprocess.Popen(command, shell=True)
                elif command.startswith('start'):
                    # Windows start command
                    subprocess.Popen(command, shell=True)
                elif ":" in command and not command.lower().endswith(".exe"):
                    # URI scheme (ms-settings:, mailto:, etc.)
                    if self.system == "Windows":
                        os.startfile(command)
                    else:
                        subprocess.Popen([command], shell=True)
                else:
                    # Regular command - try multiple methods with better Windows handling
                    if self.system == "Windows":
                        # Try multiple Windows execution methods
                        success = False
                        try:
                            # Method 1: Try os.startfile first
                            os.startfile(command)
                            success = True
                        except Exception as e1:
                            logger.debug(f"os.startfile failed: {e1}")
                            try:
                                # Method 2: Try shutil.which to find full path
                                full_path = shutil.which(command)
                                if full_path:
                                    subprocess.Popen([full_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    success = True
                                else:
                                    # Method 3: Try System32 for built-in commands
                                    if command.endswith('.exe'):
                                        sys32_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", command)
                                        if os.path.exists(sys32_path):
                                            subprocess.Popen([sys32_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                            success = True
                                    else:
                                        # Method 4: Try with .exe extension
                                        exe_command = command if command.endswith('.exe') else f"{command}.exe"
                                        sys32_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", exe_command)
                                        if os.path.exists(sys32_path):
                                            subprocess.Popen([sys32_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                            success = True
                            except Exception as e2:
                                logger.debug(f"System32 execution failed: {e2}")
                                try:
                                    # Method 5: Fallback to shell execution
                                    subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    success = True
                                except Exception as e3:
                                    logger.debug(f"Shell execution failed: {e3}")
                        
                        if not success:
                            raise Exception(f"Failed to execute command: {command}")
                    else:
                        # macOS/Linux
                        try:
                            subprocess.Popen(command.split(), shell=False)
                        except:
                            subprocess.Popen(command, shell=True)
                
                return {
                    "success": True,
                    "notify": True,
                    "message": f"I've opened {canonical_name.title()} for you."
                }
            
            # If no good match found, suggest alternatives
            suggestions = process.extract(app_name.lower(), list(self.installed_apps.keys()), limit=5)
            suggestion_text = ", ".join([sug[0].title() for sug in suggestions if sug[1] >= 40])
            
            return {
                "success": False,
                "notify": True,
                "message": f"I couldn't find '{original_name}'. Did you mean one of these: {suggestion_text}?"
            }
            
        except Exception as e:
            logger.error(f"Could not open '{original_name}': {e}", exc_info=True)
            return {
                "success": False,
                "notify": True,
                "message": f"I'm having trouble opening {original_name}. Please try again."
            }
    
    def _resolve_app_name(self, app_name: str) -> str:
        """Resolve app name to executable, handling variations"""
        # Remove common words
        app_name = app_name.replace("microsoft", "").replace("ms", "").strip()
        
        # Direct mapping check
        if app_name in self.app_mappings:
            return self.app_mappings[app_name]
        
        # Common variations
        variations = {
            "paint": "mspaint.exe",
            "ms paint": "mspaint.exe",
            "mspaint": "mspaint.exe",
            "word pad": "wordpad.exe",
            "wordpad": "wordpad.exe",
            "snipping tool": "SnippingTool.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "command prompt": "cmd.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "terminal": "wt.exe",
            "windows terminal": "wt.exe",
            "settings": "ms-settings:",
            "store": "ms-windows-store:",
        }
        
        if app_name in variations:
            return variations[app_name]
        
        # Try with .exe extension
        if not app_name.endswith('.exe'):
            return f"{app_name}.exe"
        
        return app_name

    async def open_file(self, file_path: str) -> Dict[str, Any]:
        """Open a file or folder"""
        if not file_path:
            return {"success": False, "message": "No file path provided"}
        
        path = Path(file_path).expanduser()
        
        if not path.exists():
            # Try to find the file
            found_path = await self._find_file(path.name)
            if found_path:
                path = found_path
            else:
                return {
                    "success": False,
                    "notify": True,
                    "message": f"I couldn't find the file: {file_path}"
                }
        
        logger.info(f"Opening file: {path}")
        
        try:
            if self.system == "Windows":
                os.startfile(path)
            elif self.system == "Darwin":  # macOS
                subprocess.run(["open", str(path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(path)])
            
            return {
                "success": True,
                "notify": True,
                "message": f"I've opened {path.name} for you."
            }
            
        except Exception as e:
            logger.error(f"Could not open file: {e}")
            return {"success": False, "message": str(e)}

    async def search_files(self, query: str, location: str = None) -> Dict[str, Any]:
        """Search for files matching query"""
        if not query:
            return {"success": False, "message": "I need something to search for."}
        
        search_dir = Path(location) if location else self.current_dir
        logger.info(f"Searching for '{query}' in {search_dir}")
        
        try:
            results = []
            for path in search_dir.rglob(f"*{query}*"):
                if len(results) >= 10:  # Limit results
                    break
                results.append(str(path))
            
            if results:
                result_text = "\n".join(results[:5])
                return {
                    "success": True,
                    "notify": True,
                    "message": f"I found {len(results)} files for you:\n{result_text}",
                    "results": results
                }
            else:
                return {
                    "success": True,
                    "notify": True,
                    "message": f"I couldn't find any files matching '{query}'"
                }
                
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {"success": False, "message": str(e)}

    async def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file"""
        if not file_path:
            return {"success": False, "message": "I need a file path to create a file."}
        
        path = Path(file_path).expanduser()
        logger.info(f"Creating file: {path}")
        
        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            path.write_text(content)
            
            return {
                "success": True,
                "notify": True,
                "message": f"I've created the file {path.name} for you."
            }
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return {"success": False, "message": str(e)}

    async def web_search(self, query: str) -> Dict[str, Any]:
        """Open web browser with search query"""
        if not query:
            return {"success": False, "message": "I need something to search for."}
        
        logger.info(f"Performing web search: {query}")
        
        try:
            import webbrowser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            return {
                "success": True,
                "notify": True,
                "message": f"I'm searching for: {query}"
            }
            
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return {"success": False, "message": str(e)}

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command (with safety checks)"""
        if not command:
            return {"success": False, "message": "I need a command to execute."}
        
        # Safety check - block dangerous commands
        dangerous_keywords = ["rm -rf", "del /f", "format", "shutdown"]
        if any(keyword in command.lower() for keyword in dangerous_keywords):
            return {
                "success": False,
                "message": "I can't execute that command for safety reasons."
            }
        
        logger.info(f"Executing command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout if result.stdout else result.stderr
            
            return {
                "success": result.returncode == 0,
                "notify": True,
                "message": output[:200],  # First 200 chars
                "output": output
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Command timed out"}
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "message": str(e)}

    async def _find_file(self, filename: str) -> Optional[Path]:
        """Search for a file in common locations"""
        search_locations = [
            self.current_dir,
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop"
        ]
        
        for location in search_locations:
            for path in location.rglob(filename):
                return path
        
        return None

    def get_current_directory(self) -> str:
        """Get current working directory"""
        return str(self.current_dir)

    def get_running_applications(self) -> List[str]:
        """Get list of currently running applications"""
        try:
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    app_name = proc.info['name']
                    if app_name and app_name not in apps:
                        apps.append(app_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return apps[:20]  # Return first 20
        except Exception as e:
            logger.error(f"Error getting running applications: {e}")
            return []

    async def close_application(self, app_name: str) -> Dict[str, Any]:
        """
        Close an application using MCP
        """
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": True}
            
            # Normalize app name
            app_name_normalized = app_name.lower().strip()
            for suffix in [' app', ' browser', ' window', ' application']:
                app_name_normalized = app_name_normalized.replace(suffix, '')
            app_name_normalized = app_name_normalized.strip()
            
            result = await self.mcp_client.close_application_smart(app_name_normalized)
            
            if result.success:
                return {
                    "success": True,
                    "message": f"Closed {app_name}",
                    "notify": True
                }
            else:
                return {
                    "success": False,
                    "message": result.error or f"Could not close {app_name}",
                    "notify": True
                }
        except Exception as e:
            logger.error(f"Error closing application {app_name}: {e}")
            return {
                "success": False,
                "message": f"Error closing {app_name}: {str(e)}",
                "notify": True
            }
    
    async def get_memory_info(self) -> Dict[str, Any]:
        """
        Get system memory information using MCP
        """
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": False}
            
            import json
            
            result = await self.mcp_client.call_tool("get_memory_info")
            
            if result.success:
                mem_data = json.loads(result.data)
                return {
                    "success": True,
                    "message": f"RAM: {mem_data['used_gb']:.1f}GB used / {mem_data['total_gb']:.1f}GB total ({mem_data['percent_used']:.1f}% used)",
                    "data": mem_data,
                    "notify": False
                }
            else:
                return {
                    "success": False,
                    "message": "Could not retrieve memory information",
                    "notify": False
                }
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "notify": False
            }
    
    async def mcp_focus_window(self, title: str) -> Dict[str, Any]:
        """Focus a window by title using MCP"""
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": False}
            
            import json
            
            result = await self.mcp_client.call_tool("focus_window", title=title)
            
            if result.success and result.data:
                response = json.loads(result.data)
                if response.get("success"):
                    return {"success": True, "message": response.get("message", f"Focused {title}"), "notify": False}
                else:
                    return {"success": False, "message": response.get("message", f"Could not focus {title}"), "notify": False}
            else:
                return {"success": False, "message": result.error or f"Could not focus {title}", "notify": False}
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return {"success": False, "message": str(e), "notify": False}
    
    async def mcp_hotkey(self, keys: str) -> Dict[str, Any]:
        """Press hotkey combination using MCP"""
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": False}
            
            import json
            
            result = await self.mcp_client.call_tool("hotkey", key_combo=keys)
            
            if result.success and result.data:
                response = json.loads(result.data)
                if response.get("success"):
                    return {"success": True, "message": response.get("message", f"Pressed {keys}"), "notify": False}
                else:
                    return {"success": False, "message": response.get("message", f"Could not press {keys}"), "notify": False}
            else:
                return {"success": False, "message": result.error or f"Could not press {keys}", "notify": False}
        except Exception as e:
            logger.error(f"Error pressing hotkey: {e}")
            return {"success": False, "message": str(e), "notify": False}
    
    async def mcp_type_text(self, text: str) -> Dict[str, Any]:
        """Type text using MCP"""
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": False}
            
            import json
            
            result = await self.mcp_client.call_tool("type_text", text=text)
            
            if result.success and result.data:
                response = json.loads(result.data)
                if response.get("success"):
                    return {"success": True, "message": response.get("message", "Typed text"), "notify": False}
                else:
                    return {"success": False, "message": response.get("message", "Could not type text"), "notify": False}
            else:
                return {"success": False, "message": result.error or "Could not type text", "notify": False}
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return {"success": False, "message": str(e), "notify": False}
    
    async def mcp_press_key(self, key: str) -> Dict[str, Any]:
        """Press a single key using MCP"""
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": False}
            
            import json
            
            result = await self.mcp_client.call_tool("press_key", key=key)
            
            if result.success and result.data:
                response = json.loads(result.data)
                if response.get("success"):
                    return {"success": True, "message": response.get("message", f"Pressed {key}"), "notify": False}
                else:
                    return {"success": False, "message": response.get("message", f"Could not press {key}"), "notify": False}
            else:
                return {"success": False, "message": result.error or f"Could not press {key}", "notify": False}
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return {"success": False, "message": str(e), "notify": False}
    
    async def mcp_click(self, x: int, y: int) -> Dict[str, Any]:
        """Click at coordinates using MCP"""
        try:
            if not self.mcp_client:
                return {"success": False, "message": "MCP client not available", "notify": False}
            
            import json
            
            result = await self.mcp_client.call_tool("click_at_coordinates", x=x, y=y)
            
            if result.success and result.data:
                response = json.loads(result.data)
                if response.get("success"):
                    return {"success": True, "message": response.get("message", f"Clicked at ({x}, {y})"), "notify": False}
                else:
                    return {"success": False, "message": response.get("message", "Could not click"), "notify": False}
            else:
                return {"success": False, "message": result.error or "Could not click", "notify": False}
        except Exception as e:
            logger.error(f"Error clicking: {e}")
            return {"success": False, "message": str(e), "notify": False}

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
