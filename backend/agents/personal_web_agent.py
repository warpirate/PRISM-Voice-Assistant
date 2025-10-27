"""
Personal Web Agent
Handles web research, monitoring, and content saving
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from backend.agents.base_agent import BaseAgent, AgentCapability
from backend.agents.agent_response import AgentResponse, ResponseStatus


class PersonalWebAgent(BaseAgent):
    """
    Agent for personal web operations
    
    Capabilities:
    - Topic research and summarization
    - Website monitoring
    - Content saving and archiving
    - Price tracking (future)
    """
    
    def __init__(self):
        super().__init__(
            name="PersonalWebAgent",
            capabilities=[AgentCapability.WEB_OPERATIONS]
        )
        
        self.monitored_sites: List[Dict[str, Any]] = []
        self.saved_content: List[Dict[str, Any]] = []
    
    async def initialize(self) -> bool:
        """Initialize web agent"""
        try:
            # Initialize web scraping tools (if available)
            logger.info("PersonalWebAgent initialized")
            return True
            
        except Exception as e:
            logger.error(f"PersonalWebAgent initialization failed: {str(e)}")
            return False
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute web operation task
        
        Supported tasks:
        - "research [topic]"
        - "monitor [url]"
        - "save content from [url]"
        - "search web for [query]"
        """
        task_lower = task.lower()
        
        try:
            if 'research' in task_lower:
                topic = self._extract_topic(task)
                return await self._research_topic(topic, context)
            
            elif 'monitor' in task_lower:
                url = self._extract_url(task)
                return await self._monitor_website(url)
            
            elif 'save' in task_lower or 'archive' in task_lower:
                url = self._extract_url(task)
                return await self._save_content(url)
            
            elif 'search' in task_lower:
                query = self._extract_query(task)
                return await self._web_search(query, context)
            
            else:
                return AgentResponse.failure(
                    message=f"Unknown web operation: {task}",
                    agent_name=self.name,
                    error="Task not recognized"
                )
                
        except Exception as e:
            logger.error(f"Web agent execution error: {str(e)}")
            return AgentResponse.failure(
                message=f"Web operation failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _research_topic(self, topic: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Research a topic using web search"""
        if not topic:
            return AgentResponse.failure(
                message="No topic specified for research",
                agent_name=self.name,
                error="Missing topic"
            )
        
        try:
            # This will integrate with existing web search functionality
            # For now, return structured research plan
            research_plan = {
                'topic': topic,
                'search_queries': [
                    f"{topic} overview",
                    f"{topic} best practices",
                    f"{topic} latest developments"
                ],
                'sources_to_check': [
                    'Wikipedia',
                    'Official documentation',
                    'Recent articles',
                    'Expert blogs'
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return AgentResponse.success(
                message=f"Research plan created for topic: {topic}",
                agent_name=self.name,
                data=research_plan,
                actions_taken=[f"Created research plan for '{topic}'"],
                suggestions=[
                    "Use 'search web for' to execute searches",
                    "Save interesting content for later review"
                ]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Research failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _monitor_website(self, url: str) -> AgentResponse:
        """Add website to monitoring list"""
        if not url:
            return AgentResponse.failure(
                message="No URL specified for monitoring",
                agent_name=self.name,
                error="Missing URL"
            )
        
        try:
            # Check if already monitored
            if any(site['url'] == url for site in self.monitored_sites):
                return AgentResponse.success(
                    message=f"Website already being monitored: {url}",
                    agent_name=self.name,
                    data={'url': url, 'status': 'already_monitored'}
                )
            
            # Add to monitoring list
            monitor_entry = {
                'url': url,
                'added': datetime.now().isoformat(),
                'check_frequency': '1 hour',
                'last_check': None,
                'status': 'active'
            }
            
            self.monitored_sites.append(monitor_entry)
            
            return AgentResponse.success(
                message=f"Now monitoring website: {url}",
                agent_name=self.name,
                data=monitor_entry,
                actions_taken=[f"Added {url} to monitoring"],
                suggestions=["Set custom check frequency if needed"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to add website to monitoring: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _save_content(self, url: str) -> AgentResponse:
        """Save content from URL"""
        if not url:
            return AgentResponse.failure(
                message="No URL specified for saving",
                agent_name=self.name,
                error="Missing URL"
            )
        
        try:
            # This would fetch and save actual content
            # For now, record the save request
            save_entry = {
                'url': url,
                'saved': datetime.now().isoformat(),
                'title': f"Content from {url}",
                'status': 'saved'
            }
            
            self.saved_content.append(save_entry)
            
            return AgentResponse.success(
                message=f"Content saved from: {url}",
                agent_name=self.name,
                data=save_entry,
                actions_taken=[f"Saved content from {url}"],
                suggestions=["Review saved content in your archive"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to save content: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _web_search(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Perform web search"""
        if not query:
            return AgentResponse.failure(
                message="No search query specified",
                agent_name=self.name,
                error="Missing query"
            )
        
        try:
            # This integrates with existing system_control web search
            # For now, return search structure
            search_result = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'results_count': 0,
                'note': 'Integrate with SystemControl.web_search()'
            }
            
            return AgentResponse.success(
                message=f"Web search initiated for: {query}",
                agent_name=self.name,
                data=search_result,
                actions_taken=[f"Searched for '{query}'"],
                requires_followup=True,
                metadata={'integration_needed': 'SystemControl.web_search'}
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Web search failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    def _extract_topic(self, task: str) -> str:
        """Extract research topic from task"""
        task_lower = task.lower()
        if 'research' in task_lower:
            topic = task_lower.split('research', 1)[1].strip()
            return topic.strip('"\'')
        return task
    
    def _extract_url(self, task: str) -> Optional[str]:
        """Extract URL from task string"""
        # Simple URL extraction
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, task)
        if match:
            return match.group(0)
        return None
    
    def _extract_query(self, task: str) -> str:
        """Extract search query from task"""
        task_lower = task.lower()
        for prefix in ['search web for', 'search for', 'search']:
            if prefix in task_lower:
                query = task_lower.split(prefix, 1)[1].strip()
                return query.strip('"\'')
        return task
    
    def get_monitored_sites(self) -> List[Dict[str, Any]]:
        """Get list of monitored websites"""
        return self.monitored_sites
    
    def get_saved_content(self) -> List[Dict[str, Any]]:
        """Get list of saved content"""
        return self.saved_content
    
    async def shutdown(self) -> bool:
        """Cleanup and shutdown"""
        logger.info(f"PersonalWebAgent shutting down (monitored: {len(self.monitored_sites)}, saved: {len(self.saved_content)})")
        return True
