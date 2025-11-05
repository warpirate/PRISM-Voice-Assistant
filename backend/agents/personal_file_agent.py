"""
Personal File Agent
Handles file organization, search, backup, and management
"""

import os
import shutil
import glob
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from backend.agents.base_agent import BaseAgent, AgentCapability
from backend.agents.agent_response import AgentResponse, ResponseStatus


class PersonalFileAgent(BaseAgent):
    """
    Agent for personal file management
    
    Capabilities:
    - Auto-organize downloads folder
    - Natural language file search
    - Smart backup system
    - Old file cleanup
    - File categorization
    """
    
    # File categories and extensions
    CATEGORIES = {
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.odt', '.rtf'],
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
        'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'code': ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css'],
        'spreadsheets': ['.xlsx', '.xls', '.csv', '.ods'],
        'presentations': ['.ppt', '.pptx', '.odp']
    }
    
    def __init__(self):
        super().__init__(
            name="PersonalFileAgent",
            capabilities=[AgentCapability.FILE_MANAGEMENT, AgentCapability.SYSTEM_CONTROL]
        )
        
        # Default directories
        self.downloads_dir = Path.home() / "Downloads"
        self.backup_dir = Path.home() / "PRISM_Backups"
        self.organized_dir = self.downloads_dir / "Organized"
    
    async def initialize(self) -> bool:
        """Initialize file agent"""
        try:
            # Create necessary directories
            self.backup_dir.mkdir(exist_ok=True)
            self.organized_dir.mkdir(exist_ok=True)
            
            for category in self.CATEGORIES.keys():
                (self.organized_dir / category).mkdir(exist_ok=True)
            
            logger.info(f"PersonalFileAgent initialized with backup dir: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"PersonalFileAgent initialization failed: {str(e)}")
            return False
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute file management task
        
        Supported tasks:
        - "organize_downloads" or "organize downloads"
        - "search_files" with parameters or "search for [filename/pattern]"
        - "backup" with parameters or "backup [path]"
        - "cleanup" or "cleanup old files"
        
        Context can contain:
        - task_type: Specific task type (search_files, organize_downloads, etc.)
        - parameters: Structured parameters from LLM intent parsing
        """
        # Check if we have structured parameters from intent parsing
        if context and 'task_type' in context and 'parameters' in context:
            task_type = context['task_type']
            parameters = context['parameters']
            
            logger.info(f"Executing structured task: {task_type} with params: {parameters}")
            
            try:
                if task_type == 'organize_downloads':
                    return await self._organize_downloads()
                
                elif task_type == 'search_files':
                    # Extract parameters
                    search_term = parameters.get('search_term', '')
                    location = parameters.get('location')
                    file_type = parameters.get('file_type')
                    
                    return await self._search_files(
                        search_term=search_term,
                        location=location,
                        file_type=file_type
                    )
                
                elif task_type == 'open_file':
                    # Extract parameters
                    search_term = parameters.get('search_term', '')
                    location = parameters.get('location')
                    file_type = parameters.get('file_type')
                    path = parameters.get('path')  # Direct path if provided
                    
                    return await self._open_file(
                        search_term=search_term,
                        location=location,
                        file_type=file_type,
                        path=path
                    )
                
                elif task_type == 'backup':
                    path = parameters.get('path')
                    return await self._backup_files(path)
                
                elif task_type == 'cleanup':
                    days = parameters.get('days', 90)
                    return await self._cleanup_old_files(days)
                
                elif task_type == 'delete_file':
                    # Delete specific files by search term
                    search_term = parameters.get('search_term', '')
                    location = parameters.get('location')
                    file_type = parameters.get('file_type')
                    
                    return await self._delete_files(
                        search_term=search_term,
                        location=location,
                        file_type=file_type
                    )
                
                elif task_type == 'run_command':
                    # Execute command prompt commands
                    command = parameters.get('command', '')
                    working_dir = parameters.get('working_dir')
                    
                    return await self._run_command(
                        command=command,
                        working_dir=working_dir
                    )
                
                else:
                    return AgentResponse.failure(
                        message=f"Unknown task type: {task_type}",
                        agent_name=self.name,
                        error="Task type not recognized"
                    )
            
            except Exception as e:
                logger.error(f"File agent execution error: {str(e)}")
                return AgentResponse.failure(
                    message=f"File operation failed: {str(e)}",
                    agent_name=self.name,
                    error=str(e)
                )
        
        # Fallback: Legacy text-based parsing
        task_lower = task.lower()
        
        try:
            if 'organize' in task_lower and 'download' in task_lower:
                return await self._organize_downloads()
            
            elif 'search' in task_lower or 'find' in task_lower:
                # Extract search term
                search_term = task_lower.replace('search for', '').replace('find', '').strip()
                return await self._search_files(search_term)
            
            elif 'backup' in task_lower:
                # Extract path from task
                path = self._extract_path(task)
                return await self._backup_files(path)
            
            elif 'cleanup' in task_lower or 'clean' in task_lower:
                days = self._extract_days(task, default=90)
                return await self._cleanup_old_files(days)
            
            else:
                return AgentResponse.failure(
                    message=f"Unknown file operation: {task}",
                    agent_name=self.name,
                    error="Task not recognized"
                )
                
        except Exception as e:
            logger.error(f"File agent execution error: {str(e)}")
            return AgentResponse.failure(
                message=f"File operation failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _organize_downloads(self) -> AgentResponse:
        """Auto-organize files in downloads folder"""
        organized_count = 0
        files_moved = []
        
        try:
            # Get all files in downloads (not in subdirectories)
            files = [f for f in self.downloads_dir.iterdir() if f.is_file()]
            
            for file_path in files:
                # Determine category
                category = self._categorize_file(file_path)
                
                if category:
                    # Move to organized folder
                    dest_dir = self.organized_dir / category
                    dest_path = dest_dir / file_path.name
                    
                    # Handle name conflicts
                    if dest_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dest_path = dest_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                    
                    shutil.move(str(file_path), str(dest_path))
                    organized_count += 1
                    files_moved.append(f"{file_path.name} → {category}/")
            
            return AgentResponse.success(
                message=f"Organized {organized_count} files from Downloads",
                agent_name=self.name,
                data={
                    'organized_count': organized_count,
                    'files_moved': files_moved[:10]  # Limit to first 10
                },
                actions_taken=[f"Organized {organized_count} files"],
                suggestions=["Keep downloads folder tidy by running this regularly"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to organize downloads: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    def _normalize_for_search(self, text: str) -> str:
        """Normalize text for fuzzy matching - remove spaces, punctuation, convert to lowercase"""
        import re
        # Remove all punctuation and spaces, convert to lowercase
        normalized = re.sub(r'[^\w]', '', text.lower())
        return normalized
    
    def _matches_search_term(self, filename: str, search_term: str) -> bool:
        """Check if filename matches search term using fuzzy matching"""
        if not search_term:
            return True
        
        # Normalize both strings
        normalized_filename = self._normalize_for_search(filename)
        normalized_search = self._normalize_for_search(search_term)
        
        # Simple substring match after normalization
        if normalized_search in normalized_filename:
            return True
        
        # Also check if all words from search term appear in filename
        search_words = [self._normalize_for_search(word) for word in search_term.split()]
        if search_words:
            # Check if all search words appear in filename (in any order)
            for word in search_words:
                if word and word not in normalized_filename:
                    return False
            return True
        
        return False
    
    async def _search_files(
        self,
        search_term: Optional[str] = None,
        location: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> AgentResponse:
        """
        Search for files matching pattern, or list all files if no search term
        Uses Windows Search Index for instant results (falls back to direct search)
        
        Args:
            search_term: Keywords to search for in filename (None = list all files)
            location: Where to search (downloads, documents, desktop, or None for all)
            file_type: Type of file (video, document, image, or None for all)
        """
        matches = []
        
        # Smart handling: if search_term is generic like "movie", "video", "music", etc.
        # treat it as a file type search instead of literal filename search
        generic_terms = {
            'movie': 'video', 'movies': 'video', 'film': 'video', 'films': 'video', 'video': 'video', 'videos': 'video',
            'music': 'audio', 'song': 'audio', 'songs': 'audio', 'audio': 'audio',
            'picture': 'image', 'pictures': 'image', 'photo': 'image', 'photos': 'image', 'image': 'image', 'images': 'image',
            'document': 'document', 'documents': 'document', 'doc': 'document', 'docs': 'document'
        }
        
        if search_term and search_term.lower() in generic_terms:
            # Convert generic term to file type search
            original_term = search_term
            if not file_type:  # Only if file_type wasn't already specified
                file_type = generic_terms[search_term.lower()]
            search_term = ""  # Search all files of this type
            logger.info(f"Converted generic search '{original_term}' to file_type '{file_type}' search")
        
        is_listing = search_term is None or search_term == ""
        
        # For searches AND listings, try fast search methods
        # Even for listing, use DIR to get all files recursively
        if search_term or is_listing:
            # Try Windows Search first (only for searches with term)
            if search_term and not is_listing:
                try:
                    windows_results = await self._windows_search(
                        search_term=search_term,
                        location=location,
                        file_type=file_type
                    )
                    if windows_results is not None and windows_results.data.get('matches'):
                        # Windows Search succeeded and found files
                        return windows_results
                except Exception as e:
                    logger.warning(f"Windows Search failed: {e}")
            
            # Fallback to dir command (much faster than rglob)
            # Use for both searches and listings
            try:
                dir_results = await self._dir_search(
                    search_term=search_term if not is_listing else "*",
                    location=location,
                    file_type=file_type
                )
                if dir_results is not None:
                    return dir_results
            except Exception as e:
                logger.warning(f"DIR search failed: {e}")
                # Fall through to direct search
        
        try:
            # Determine search locations based on location parameter
            if location:
                # Parse location - handle both simple paths and subdirectories
                location_lower = location.lower()
                
                # Try to build the path intelligently
                if '/' in location_lower or '\\' in location_lower:
                    # It's a path like "downloads/telegram desktop folder"
                    parts = location_lower.replace('\\', '/').split('/')
                    
                    # Start with base directory
                    base_map = {
                        'downloads': Path.home() / "Downloads",
                        'documents': Path.home() / "Documents",
                        'desktop': Path.home() / "Desktop",
                    }
                    
                    base_dir = base_map.get(parts[0].strip())
                    if base_dir:
                        # Build full path with subdirectories
                        full_path = base_dir
                        for part in parts[1:]:
                            # Handle "folder" suffix like "telegram desktop folder"
                            part_clean = part.strip().replace(' folder', '').replace('folder', '').strip()
                            if part_clean:
                                full_path = full_path / part_clean
                        
                        # Try to find matching subdirectory (case-insensitive)
                        if base_dir.exists():
                            # Look for matching subdirectory
                            try:
                                for subdir in base_dir.iterdir():
                                    if subdir.is_dir():
                                        # Case-insensitive match
                                        target_name = ' '.join(parts[1:]).replace(' folder', '').strip()
                                        if subdir.name.lower() == target_name.lower():
                                            full_path = subdir
                                            break
                            except PermissionError:
                                pass
                        
                        search_locations = [full_path] if full_path else []
                    else:
                        search_locations = []
                else:
                    # Simple location like "downloads"
                    location_map = {
                        'downloads': Path.home() / "Downloads",
                        'documents': Path.home() / "Documents",
                        'desktop': Path.home() / "Desktop",
                    }
                    search_locations = [location_map.get(location_lower)]
                
                # Filter out None values
                search_locations = [loc for loc in search_locations if loc is not None]
            else:
                # Search in common directories, including media-specific locations
                search_locations = [
                    Path.home() / "Downloads",
                    Path.home() / "Documents", 
                    Path.home() / "Desktop",
                    Path.home() / "Videos",
                    Path.home() / "Music",
                    Path.home() / "Pictures",
                ]
            
            # Determine file extensions to look for based on file_type
            target_extensions = None
            if file_type:
                type_map = {
                    'video': self.CATEGORIES.get('videos', []),
                    'document': self.CATEGORIES.get('documents', []) + self.CATEGORIES.get('spreadsheets', []) + self.CATEGORIES.get('presentations', []),
                    'image': self.CATEGORIES.get('images', []),
                    'audio': self.CATEGORIES.get('audio', []),
                    'code': self.CATEGORIES.get('code', []),
                    'archive': self.CATEGORIES.get('archives', []),
                    'application': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'],
                    'app': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'],
                }
                target_extensions = type_map.get(file_type.lower())
            
            action = "Listing all files" if is_listing else f"Searching for '{search_term}'"
            logger.info(f"{action} in {[str(loc) for loc in search_locations]}, file_type={file_type}")
            
            for location_path in search_locations:
                if not location_path or not location_path.exists():
                    logger.warning(f"Location does not exist: {location_path}")
                    continue
                
                # List files (with limited depth for listing mode)
                try:
                    if is_listing:
                        # For listing, only go 1 level deep to avoid too many results
                        for file_path in location_path.iterdir():
                            if not file_path.is_file():
                                continue
                            
                            # Check file type if specified
                            if target_extensions:
                                if file_path.suffix.lower() not in target_extensions:
                                    continue
                            
                            matches.append({
                                'name': file_path.name,
                                'path': str(file_path),
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                            
                            # Limit results for performance
                            if len(matches) >= 100:
                                break
                    else:
                        # For searching, use recursive search
                        for file_path in location_path.rglob('*'):
                            if not file_path.is_file():
                                continue
                            
                            # Check if search term matches using fuzzy matching
                            if search_term and not self._matches_search_term(file_path.name, search_term):
                                continue
                            
                            # Check file type if specified
                            if target_extensions:
                                if file_path.suffix.lower() not in target_extensions:
                                    continue
                            
                            matches.append({
                                'name': file_path.name,
                                'path': str(file_path),
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                            
                            # Limit results for performance
                            if len(matches) >= 50:
                                break
                            
                except PermissionError:
                    logger.warning(f"Permission denied accessing {location_path}")
                    continue
                except Exception as e:
                    logger.warning(f"Error searching {location_path}: {e}", exc_info=True)
                    continue
                
                if len(matches) >= (100 if is_listing else 50):
                    break
            
            # Build response message
            if matches:
                location_str = f" in {location}" if location else ""
                file_type_str = f" ({file_type} files)" if file_type else ""
                
                if is_listing:
                    message = f"Found {len(matches)} file(s){location_str}{file_type_str}"
                else:
                    message = f"Found {len(matches)} file(s) matching '{search_term}'{location_str}{file_type_str}"
                
                # List first few matches in message
                if len(matches) <= 10:
                    file_list = "\n".join([f"• {m['name']}" for m in matches])
                    message += f":\n{file_list}"
                else:
                    file_list = "\n".join([f"• {m['name']}" for m in matches[:10]])
                    message += f":\n{file_list}\n... and {len(matches) - 10} more"
            else:
                location_str = f" in {location}" if location else ""
                file_type_str = f" ({file_type} files)" if file_type else ""
                
                if is_listing:
                    message = f"No files found{location_str}{file_type_str}"
                else:
                    message = f"No files found matching '{search_term}'{location_str}{file_type_str}"
            
            return AgentResponse.success(
                message=message,
                agent_name=self.name,
                data={
                    'matches': matches,
                    'search_term': search_term,
                    'location': location,
                    'file_type': file_type,
                    'is_listing': is_listing,
                    'truncated': len(matches) >= (100 if is_listing else 50)
                },
                actions_taken=[f"{action}{location_str}{file_type_str}"]
            )
            
        except Exception as e:
            logger.error(f"File search error: {e}", exc_info=True)
            return AgentResponse.failure(
                message=f"File search failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _backup_files(self, source_path: Optional[str] = None) -> AgentResponse:
        """Backup files to backup directory"""
        if not source_path:
            source_path = str(Path.home() / "Documents")
        
        source = Path(source_path)
        if not source.exists():
            return AgentResponse.failure(
                message=f"Source path does not exist: {source_path}",
                agent_name=self.name,
                error="Invalid source path"
            )
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source.name}_backup_{timestamp}"
            dest = self.backup_dir / backup_name
            
            if source.is_file():
                shutil.copy2(str(source), str(dest))
                size = source.stat().st_size
            else:
                shutil.copytree(str(source), str(dest))
                size = sum(f.stat().st_size for f in dest.rglob('*') if f.is_file())
            
            return AgentResponse.success(
                message=f"Backed up {source.name} to {backup_name}",
                agent_name=self.name,
                data={
                    'source': str(source),
                    'destination': str(dest),
                    'size_bytes': size,
                    'timestamp': timestamp
                },
                actions_taken=[f"Created backup of {source.name}"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Backup failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _cleanup_old_files(self, days: int = 90) -> AgentResponse:
        """Delete old files from downloads"""
        deleted_count = 0
        deleted_files = []
        threshold = datetime.now() - timedelta(days=days)
        
        try:
            files = [f for f in self.downloads_dir.iterdir() if f.is_file()]
            
            for file_path in files:
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if modified_time < threshold:
                    file_path.unlink()
                    deleted_count += 1
                    deleted_files.append(file_path.name)
            
            return AgentResponse.success(
                message=f"Deleted {deleted_count} files older than {days} days",
                agent_name=self.name,
                data={
                    'deleted_count': deleted_count,
                    'days_threshold': days,
                    'files': deleted_files[:10]
                },
                actions_taken=[f"Cleaned up {deleted_count} old files"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Cleanup failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _delete_files(
        self,
        search_term: Optional[str] = None,
        location: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> AgentResponse:
        """
        Delete files matching search criteria
        
        Args:
            search_term: Keywords to search for in filename
            location: Where to search (downloads, documents, desktop, or None for all)
            file_type: Type of file (video, document, image, or None for all)
        """
        try:
            # First search for the files
            search_result = await self._search_files(
                search_term=search_term,
                location=location,
                file_type=file_type
            )
            
            if not search_result.is_success():
                return search_result
            
            matches = search_result.data.get('matches', [])
            
            if not matches:
                location_str = f" in {location}" if location else ""
                file_type_str = f" ({file_type} files)" if file_type else ""
                return AgentResponse.failure(
                    message=f"No files found matching '{search_term}'{location_str}{file_type_str}",
                    agent_name=self.name,
                    error="No matching files found"
                )
            
            # Delete the files
            deleted_count = 0
            deleted_files = []
            failed_files = []
            
            for file_match in matches:
                try:
                    file_path = Path(file_match['path'])
                    if file_path.exists():
                        file_path.unlink()
                        deleted_count += 1
                        deleted_files.append(file_path.name)
                    else:
                        failed_files.append(file_path.name)
                except Exception as e:
                    logger.warning(f"Failed to delete {file_match.get('name', 'unknown')}: {e}")
                    failed_files.append(file_match.get('name', 'unknown'))
            
            # Build response message
            message = f"Deleted {deleted_count} file(s)"
            if deleted_files:
                if len(deleted_files) <= 5:
                    message += f": {', '.join(deleted_files)}"
                else:
                    message += f": {', '.join(deleted_files[:5])} and {len(deleted_files) - 5} more"
            
            if failed_files:
                message += f". Failed to delete {len(failed_files)} file(s)"
            
            return AgentResponse.success(
                message=message,
                agent_name=self.name,
                data={
                    'deleted_count': deleted_count,
                    'deleted_files': deleted_files,
                    'failed_files': failed_files,
                    'total_found': len(matches)
                },
                actions_taken=[f"Deleted {deleted_count} file(s)"]
            )
            
        except Exception as e:
            logger.error(f"Error deleting files: {e}", exc_info=True)
            return AgentResponse.failure(
                message=f"Failed to delete files: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _open_file(
        self,
        search_term: Optional[str] = None,
        location: Optional[str] = None,
        file_type: Optional[str] = None,
        path: Optional[str] = None
    ) -> AgentResponse:
        """
        Open a file by searching for it or using direct path
        
        Args:
            search_term: Keywords to search for in filename
            location: Where to search (downloads, documents, desktop)
            file_type: Type of file (video, document, image)
            path: Direct file path (if known)
        """
        try:
            # If direct path provided, just open it
            if path:
                file_path = Path(path)
                if not file_path.exists():
                    return AgentResponse.failure(
                        message=f"File not found: {path}",
                        agent_name=self.name,
                        error="File does not exist"
                    )
                
                # Open the file
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Windows":
                    os.startfile(str(file_path))
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", str(file_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(file_path)])
                
                return AgentResponse.success(
                    message=f"Opened {file_path.name}",
                    agent_name=self.name,
                    data={'path': str(file_path), 'name': file_path.name},
                    actions_taken=[f"Opened file: {file_path.name}"]
                )
            
            # Otherwise, search for the file first
            search_result = await self._search_files(
                search_term=search_term,
                location=location,
                file_type=file_type
            )
            
            if not search_result.is_success():
                return search_result
            
            matches = search_result.data.get('matches', [])
            
            if not matches:
                location_str = f" in {location}" if location else ""
                file_type_str = f" ({file_type} files)" if file_type else ""
                return AgentResponse.failure(
                    message=f"No files found matching '{search_term}'{location_str}{file_type_str}",
                    agent_name=self.name,
                    error="No matching files found"
                )
            
            # If multiple matches, open the most recent one
            if len(matches) > 1:
                # Sort by modified time (most recent first)
                matches.sort(key=lambda x: x['modified'], reverse=True)
                logger.info(f"Found {len(matches)} matches, opening most recent: {matches[0]['name']}")
            
            # Open the first (or only) match
            file_to_open = Path(matches[0]['path'])
            
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(str(file_to_open))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(file_to_open)])
            else:  # Linux
                subprocess.run(["xdg-open", str(file_to_open)])
            
            message = f"Opened {file_to_open.name}"
            if len(matches) > 1:
                message += f" (found {len(matches)} matches, opened most recent)"
            
            return AgentResponse.success(
                message=message,
                agent_name=self.name,
                data={
                    'path': str(file_to_open),
                    'name': file_to_open.name,
                    'total_matches': len(matches),
                    'all_matches': matches[:5]  # Include first 5 for reference
                },
                actions_taken=[f"Opened file: {file_to_open.name}"]
            )
            
        except Exception as e:
            logger.error(f"Error opening file: {e}", exc_info=True)
            return AgentResponse.failure(
                message=f"Failed to open file: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _windows_search(
        self,
        search_term: str,
        location: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> Optional[AgentResponse]:
        """
        Use Windows Search Index for instant file search
        This is MUCH faster than recursive directory scanning
        
        Returns:
            AgentResponse if successful, None if Windows Search not available
        """
        try:
            import win32com.client
            
            # Build search scope
            search_locations = []
            if location:
                # Parse location to get actual path
                location_lower = location.lower()
                
                if '/' in location_lower or '\\' in location_lower:
                    parts = location_lower.replace('\\', '/').split('/')
                    base_map = {
                        'downloads': Path.home() / "Downloads",
                        'documents': Path.home() / "Documents",
                        'desktop': Path.home() / "Desktop",
                    }
                    base_dir = base_map.get(parts[0].strip())
                    if base_dir:
                        full_path = base_dir
                        for part in parts[1:]:
                            part_clean = part.strip().replace(' folder', '').replace('folder', '').strip()
                            if part_clean:
                                full_path = full_path / part_clean
                        
                        # Try to find actual directory
                        if base_dir.exists():
                            try:
                                for subdir in base_dir.iterdir():
                                    if subdir.is_dir():
                                        target_name = ' '.join(parts[1:]).replace(' folder', '').strip()
                                        if subdir.name.lower() == target_name.lower():
                                            full_path = subdir
                                            break
                            except:
                                pass
                        search_locations = [str(full_path)]
                else:
                    location_map = {
                        'downloads': str(Path.home() / "Downloads"),
                        'documents': str(Path.home() / "Documents"),
                        'desktop': str(Path.home() / "Desktop"),
                    }
                    loc = location_map.get(location_lower)
                    if loc:
                        search_locations = [loc]
            else:
                # Search common locations
                search_locations = [
                    str(Path.home() / "Downloads"),
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Desktop"),
                ]
            
            # Build file extension filter
            extension_filter = ""
            if file_type:
                type_map = {
                    'video': self.CATEGORIES.get('videos', []),
                    'document': self.CATEGORIES.get('documents', []) + self.CATEGORIES.get('spreadsheets', []) + self.CATEGORIES.get('presentations', []),
                    'image': self.CATEGORIES.get('images', []),
                    'audio': self.CATEGORIES.get('audio', []),
                    'code': self.CATEGORIES.get('code', []),
                    'archive': self.CATEGORIES.get('archives', []),
                    'application': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'],
                    'app': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'],
                }
                extensions = type_map.get(file_type.lower(), [])
                if extensions:
                    # Build extension filter like ".mp4 OR .mkv OR .avi"
                    ext_filters = [f"System.FileExtension:={ext}" for ext in extensions]
                    extension_filter = " OR ".join(ext_filters)
            
            # Create Windows Search connection
            conn = win32com.client.Dispatch("ADODB.Connection")
            rs = win32com.client.Dispatch("ADODB.Recordset")
            
            conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
            
            matches = []
            for search_loc in search_locations:
                # Build SQL query for Windows Search
                # Convert path to proper format with forward slashes
                search_path = search_loc.replace('\\', '/')
                
                # Build WHERE clause with proper SCOPE syntax
                where_parts = [
                    f"SCOPE='file:///{search_path}'",
                    f"System.FileName LIKE '%{search_term}%'"
                ]
                if extension_filter:
                    where_parts.append(f"({extension_filter})")
                
                where_clause = " AND ".join(where_parts)
                
                query = f"""
                    SELECT TOP 50
                        System.ItemPathDisplay,
                        System.FileName,
                        System.Size,
                        System.DateModified
                    FROM SystemIndex
                    WHERE {where_clause}
                    ORDER BY System.DateModified DESC
                """
                
                logger.info(f"Windows Search query for '{search_term}' in {search_loc}")
                
                try:
                    rs.Open(query, conn)
                    
                    # Fetch results
                    count = 0
                    while not rs.EOF and count < 50:
                        try:
                            file_path = rs.Fields("System.ItemPathDisplay").Value
                            file_name = rs.Fields("System.FileName").Value
                            file_size = rs.Fields("System.Size").Value or 0
                            date_modified = rs.Fields("System.DateModified").Value
                            
                            if file_path and file_name:
                                matches.append({
                                    'name': file_name,
                                    'path': file_path,
                                    'size': file_size,
                                    'modified': date_modified.isoformat() if date_modified else datetime.now().isoformat()
                                })
                                count += 1
                        except Exception as e:
                            logger.warning(f"Error reading record: {e}")
                        
                        rs.MoveNext()
                    
                    rs.Close()
                except Exception as e:
                    logger.warning(f"Error searching location {search_loc}: {e}")
            
            conn.Close()
            
            # Build response
            location_str = f" in {location}" if location else ""
            file_type_str = f" ({file_type} files)" if file_type else ""
            
            if matches:
                message = f"Found {len(matches)} file(s) matching '{search_term}'{location_str}{file_type_str}"
                
                if len(matches) <= 10:
                    file_list = "\n".join([f"• {m['name']}" for m in matches])
                    message += f":\n{file_list}"
                else:
                    file_list = "\n".join([f"• {m['name']}" for m in matches[:10]])
                    message += f":\n{file_list}\n... and {len(matches) - 10} more"
            else:
                message = f"No files found matching '{search_term}'{location_str}{file_type_str}"
            
            logger.info(f"Windows Search found {len(matches)} matches in {len(search_locations)} locations")
            
            return AgentResponse.success(
                message=message,
                agent_name=self.name,
                data={
                    'matches': matches,
                    'search_term': search_term,
                    'location': location,
                    'file_type': file_type,
                    'search_method': 'windows_search',
                    'truncated': len(matches) >= 50
                },
                actions_taken=[f"Searched using Windows Search Index"]
            )
            
        except ImportError:
            logger.warning("pywin32 not available, cannot use Windows Search")
            return None
        except Exception as e:
            logger.error(f"Windows Search error: {e}", exc_info=True)
            return None
    
    async def _dir_search(
        self,
        search_term: str,
        location: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> Optional[AgentResponse]:
        """
        Use Windows DIR command for fast file search
        Fallback when Windows Search Index fails
        
        Returns:
            AgentResponse if successful, None if failed
        """
        try:
            import subprocess
            
            # Build search locations
            search_locations = []
            if location:
                location_lower = location.lower()
                
                if '/' in location_lower or '\\' in location_lower:
                    parts = location_lower.replace('\\', '/').split('/')
                    base_map = {
                        'downloads': Path.home() / "Downloads",
                        'documents': Path.home() / "Documents",
                        'desktop': Path.home() / "Desktop",
                    }
                    base_dir = base_map.get(parts[0].strip())
                    if base_dir:
                        full_path = base_dir
                        for part in parts[1:]:
                            part_clean = part.strip().replace(' folder', '').replace('folder', '').strip()
                            if part_clean:
                                full_path = full_path / part_clean
                        
                        if base_dir.exists():
                            try:
                                for subdir in base_dir.iterdir():
                                    if subdir.is_dir():
                                        target_name = ' '.join(parts[1:]).replace(' folder', '').strip()
                                        if subdir.name.lower() == target_name.lower():
                                            full_path = subdir
                                            break
                            except:
                                pass
                        search_locations = [full_path]
                else:
                    location_map = {
                        'downloads': Path.home() / "Downloads",
                        'documents': Path.home() / "Documents",
                        'desktop': Path.home() / "Desktop",
                    }
                    loc = location_map.get(location_lower)
                    if loc:
                        search_locations = [loc]
            else:
                search_locations = [
                    Path.home() / "Downloads",
                    Path.home() / "Documents",
                    Path.home() / "Desktop",
                ]
            
            # Build file extension pattern
            extension_pattern = "*"
            if file_type:
                type_map = {
                    'video': self.CATEGORIES.get('videos', []),
                    'document': self.CATEGORIES.get('documents', []) + self.CATEGORIES.get('spreadsheets', []) + self.CATEGORIES.get('presentations', []),
                    'image': self.CATEGORIES.get('images', []),
                    'audio': self.CATEGORIES.get('audio', []),
                    'code': self.CATEGORIES.get('code', []),
                    'archive': self.CATEGORIES.get('archives', []),
                }
                extensions = type_map.get(file_type.lower(), [])
                # For now, search all files and filter later
                # DIR doesn't support multiple extension patterns easily
            
            matches = []
            for search_loc in search_locations:
                if not search_loc.exists():
                    continue
                
                # Use dir /s /b /a-d to recursively search (exclude directories)
                # Use *.* pattern and filter with fuzzy matching for better results
                search_pattern = "*.*"  # Get all files, filter with fuzzy matching
                
                logger.info(f"DIR searching for '{search_term or '*.*'}' in {search_loc}")
                
                try:
                    result = subprocess.run(
                        ['cmd', '/c', 'dir', '/s', '/b', '/a-d', search_pattern],
                        cwd=str(search_loc),
                        capture_output=True,
                        text=True,
                        timeout=15,  # 15 second timeout
                        errors='ignore'  # Handle encoding issues
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        lines = result.stdout.strip().split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            try:
                                file_path = Path(line)
                                if not file_path.is_file():
                                    continue
                                
                                # Filter by search term using fuzzy matching
                                if search_term and search_term != "*":
                                    if not self._matches_search_term(file_path.name, search_term):
                                        continue
                                
                                # Filter by file type if specified
                                if file_type:
                                    type_map = {
                                        'video': self.CATEGORIES.get('videos', []),
                                        'document': self.CATEGORIES.get('documents', []) + self.CATEGORIES.get('spreadsheets', []) + self.CATEGORIES.get('presentations', []),
                                        'image': self.CATEGORIES.get('images', []),
                                        'audio': self.CATEGORIES.get('audio', []),
                                        'code': self.CATEGORIES.get('code', []),
                                        'archive': self.CATEGORIES.get('archives', []),
                                        'application': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'],
                                        'app': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'],
                                    }
                                    extensions = type_map.get(file_type.lower(), [])
                                    if extensions and file_path.suffix.lower() not in extensions:
                                        continue
                                
                                matches.append({
                                    'name': file_path.name,
                                    'path': str(file_path),
                                    'size': file_path.stat().st_size,
                                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                                })
                                
                                if len(matches) >= 50:
                                    break
                            except Exception as e:
                                logger.debug(f"Error processing line '{line}': {e}")
                                continue
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"DIR search timed out for {search_loc}")
                except Exception as e:
                    logger.warning(f"DIR search error for {search_loc}: {e}")
                
                if len(matches) >= 50:
                    break
            
            # Build response
            location_str = f" in {location}" if location else ""
            file_type_str = f" ({file_type} files)" if file_type else ""
            
            # Determine if this was a listing or search
            is_listing_mode = search_term == "*"
            
            if matches:
                if is_listing_mode:
                    message = f"Found {len(matches)} file(s){location_str}{file_type_str}"
                else:
                    message = f"Found {len(matches)} file(s) matching '{search_term}'{location_str}{file_type_str}"
                
                if len(matches) <= 10:
                    file_list = "\n".join([f"• {m['name']}" for m in matches])
                    message += f":\n{file_list}"
                else:
                    file_list = "\n".join([f"• {m['name']}" for m in matches[:10]])
                    message += f":\n{file_list}\n... and {len(matches) - 10} more"
            else:
                if is_listing_mode:
                    message = f"No files found{location_str}{file_type_str}"
                else:
                    message = f"No files found matching '{search_term}'{location_str}{file_type_str}"
            
            logger.info(f"DIR search found {len(matches)} matches")
            
            return AgentResponse.success(
                message=message,
                agent_name=self.name,
                data={
                    'matches': matches,
                    'search_term': search_term if not is_listing_mode else None,
                    'location': location,
                    'file_type': file_type,
                    'is_listing': is_listing_mode,
                    'search_method': 'dir_command',
                    'truncated': len(matches) >= 50
                },
                actions_taken=[f"Searched using DIR command"]
            )
            
        except Exception as e:
            logger.error(f"DIR search error: {e}", exc_info=True)
            return None
    
    async def _run_command(
        self,
        command: str,
        working_dir: Optional[str] = None
    ) -> AgentResponse:
        """
        Execute a command prompt command
        
        Args:
            command: Command to execute
            working_dir: Working directory for the command
        """
        try:
            import subprocess
            import platform
            
            if not command:
                return AgentResponse.failure(
                    message="No command provided",
                    agent_name=self.name,
                    error="Empty command"
                )
            
            # Set working directory
            cwd = None
            if working_dir:
                cwd = Path(working_dir)
                if not cwd.exists():
                    return AgentResponse.failure(
                        message=f"Working directory does not exist: {working_dir}",
                        agent_name=self.name,
                        error="Invalid working directory"
                    )
                cwd = str(cwd)
            
            logger.info(f"Executing command: {command} (cwd: {cwd})")
            
            # Execute command
            system = platform.system()
            if system == "Windows":
                # Use cmd.exe on Windows
                result = subprocess.run(
                    ['cmd', '/c', command],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
            else:
                # Use shell on Unix-like systems
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            # Get output
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                message = f"Command executed successfully"
                if output:
                    # Limit output length
                    if len(output) > 500:
                        output_preview = output[:500] + "... (truncated)"
                    else:
                        output_preview = output
                    message += f"\n\nOutput:\n{output_preview}"
                
                return AgentResponse.success(
                    message=message,
                    agent_name=self.name,
                    data={
                        'command': command,
                        'output': output,
                        'exit_code': result.returncode,
                        'working_dir': cwd
                    },
                    actions_taken=[f"Executed command: {command}"]
                )
            else:
                return AgentResponse.failure(
                    message=f"Command failed with exit code {result.returncode}\n\nError:\n{error if error else 'No error message'}",
                    agent_name=self.name,
                    error=error or "Command failed"
                )
            
        except subprocess.TimeoutExpired:
            return AgentResponse.failure(
                message=f"Command timed out after 30 seconds",
                agent_name=self.name,
                error="Timeout"
            )
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return AgentResponse.failure(
                message=f"Failed to execute command: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    def _categorize_file(self, file_path: Path) -> Optional[str]:
        """Determine file category based on extension"""
        ext = file_path.suffix.lower()
        
        for category, extensions in self.CATEGORIES.items():
            if ext in extensions:
                return category
        
        return None
    
    def _extract_path(self, task: str) -> Optional[str]:
        """Extract file path from task string"""
        # Simple extraction - look for quoted paths
        import re
        match = re.search(r'["\']([^"\']+)["\']', task)
        if match:
            return match.group(1)
        return None
    
    def _extract_days(self, task: str, default: int = 90) -> int:
        """Extract number of days from task string"""
        import re
        match = re.search(r'(\d+)\s*days?', task.lower())
        if match:
            return int(match.group(1))
        return default
    
    async def shutdown(self) -> bool:
        """Cleanup and shutdown"""
        logger.info("PersonalFileAgent shutting down")
        return True
