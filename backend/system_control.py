"""
System Control Module
Handles application management, file operations, and system commands
"""

import os
import subprocess
import psutil
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
import shutil


class SystemControl:
    """
    Manages system-level operations:
    - Application launching and management
    - File system operations
    - System commands
    """

    def __init__(self):
        self.system = platform.system()
        self.current_dir = Path.home()
        
        # Application name mappings (common apps)
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

    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application by name"""
        if not app_name:
            return {"success": False, "message": "No application name provided"}
        
        original_name = app_name
        app_name_lower = app_name.lower().strip()
        logger.info(f"Opening application: '{original_name}' (normalized: '{app_name_lower}')")
        
        try:
            # Try to find the best match for the app
            executable = self._resolve_app_name(app_name_lower)
            
            logger.info(f"Resolved '{original_name}' to executable: '{executable}'")
            
            if self.system == "Windows":
                # 1) URI scheme (ms-settings:, mailto:, etc.)
                if ":" in executable and not executable.lower().endswith(".exe"):
                    try:
                        os.startfile(executable)
                        started = True
                    except OSError:
                        started = False
                else:
                    # 2) Try os.startfile first – this leverages ShellExecute search logic
                    try:
                        os.startfile(executable)
                        started = True
                    except OSError:
                        # 3) Explicit path resolution fallback
                        exec_path = shutil.which(executable) or executable
                        if not os.path.isabs(exec_path):
                            # Try System32
                            sys32 = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", executable)
                            exec_path = sys32 if os.path.exists(sys32) else exec_path
                        try:
                            subprocess.Popen([exec_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            started = True
                        except Exception:
                            started = False
                
            else:
                # macOS/Linux
                try:
                    proc = subprocess.Popen([executable])
                    started = proc.poll() is None
                except FileNotFoundError:
                    started = False
            
            if started:
                return {
                    "success": True,
                    "notify": True,
                    "message": f"Opened {original_name}"
                }
            else:
                raise FileNotFoundError(f"Executable not found or failed to launch: {executable}")
            
        except Exception as e:
            logger.error(f"Could not open '{original_name}': {e}", exc_info=True)
            return {
                "success": False,
                "notify": True,
                "message": f"Could not open {original_name}. Make sure it's installed."
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
                    "message": f"File not found: {file_path}"
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
                "message": f"Opened {path.name}"
            }
            
        except Exception as e:
            logger.error(f"Could not open file: {e}")
            return {"success": False, "message": str(e)}

    async def search_files(self, query: str, location: str = None) -> Dict[str, Any]:
        """Search for files matching query"""
        if not query:
            return {"success": False, "message": "No search query provided"}
        
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
                    "message": f"Found {len(results)} files:\n{result_text}",
                    "results": results
                }
            else:
                return {
                    "success": True,
                    "notify": True,
                    "message": f"No files found matching '{query}'"
                }
                
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {"success": False, "message": str(e)}

    async def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file"""
        if not file_path:
            return {"success": False, "message": "No file path provided"}
        
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
                "message": f"Created file: {path.name}"
            }
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return {"success": False, "message": str(e)}

    async def web_search(self, query: str) -> Dict[str, Any]:
        """Open web browser with search query"""
        if not query:
            return {"success": False, "message": "No search query provided"}
        
        logger.info(f"Performing web search: {query}")
        
        try:
            import webbrowser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            return {
                "success": True,
                "notify": True,
                "message": f"Searching for: {query}"
            }
            
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return {"success": False, "message": str(e)}

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command (with safety checks)"""
        if not command:
            return {"success": False, "message": "No command provided"}
        
        # Safety check - block dangerous commands
        dangerous_keywords = ["rm -rf", "del /f", "format", "shutdown"]
        if any(keyword in command.lower() for keyword in dangerous_keywords):
            return {
                "success": False,
                "message": "Command blocked for safety reasons"
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
