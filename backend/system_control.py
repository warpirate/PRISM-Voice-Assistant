"""
System control module for executing Windows commands
"""

import subprocess
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemController:
    """Handles system-level operations on Windows"""
    
    def __init__(self):
        self.command_map = {
            # Applications
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
            "vscode": "code",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            
            # Folders
            "documents": str(Path.home() / "Documents"),
            "downloads": str(Path.home() / "Downloads"),
            "desktop": str(Path.home() / "Desktop"),
            "pictures": str(Path.home() / "Pictures"),
            "music": str(Path.home() / "Music"),
            "videos": str(Path.home() / "Videos"),
        }
    
    def execute(self, command: str) -> bool:
        """
        Execute a system command
        
        Args:
            command: Command to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize command
            command_lower = command.lower().strip()
            
            # Check if it's a mapped command
            if command_lower in self.command_map:
                target = self.command_map[command_lower]
                
                # Check if it's a folder path
                if os.path.isdir(target):
                    return self._open_folder(target)
                else:
                    return self._run_application(target)
            
            # Try to execute as-is
            return self._run_command(command)
            
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {e}")
            return False
    
    def _run_application(self, app_path: str) -> bool:
        """Run an application"""
        try:
            subprocess.Popen(app_path, shell=True)
            logger.info(f"Launched application: {app_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch {app_path}: {e}")
            return False
    
    def _open_folder(self, folder_path: str) -> bool:
        """Open a folder in Explorer"""
        try:
            subprocess.Popen(f'explorer "{folder_path}"', shell=True)
            logger.info(f"Opened folder: {folder_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to open folder {folder_path}: {e}")
            return False
    
    def _run_command(self, command: str) -> bool:
        """Run a raw command"""
        try:
            subprocess.Popen(command, shell=True)
            logger.info(f"Executed command: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
            return False
    
    def get_system_info(self) -> dict:
        """Get basic system information"""
        try:
            info = {
                "os": os.name,
                "user": os.getlogin(),
                "home": str(Path.home()),
                "cwd": os.getcwd()
            }
            return info
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}
    
    def list_running_processes(self) -> list:
        """List running processes (simplified)"""
        try:
            result = subprocess.run(
                ["tasklist"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')[3:]  # Skip header
                processes = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            processes.append(parts[0])
                return processes
            return []
        except Exception as e:
            logger.error(f"Failed to list processes: {e}")
            return []
