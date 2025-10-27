"""
Base Agent Class
Foundation for all PRISM agents with standardized interface and lifecycle
"""

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from loguru import logger

from backend.agents.agent_response import AgentResponse, ResponseStatus


class AgentStatus(Enum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentCapability(Enum):
    """Agent capabilities for discovery and routing"""
    FILE_MANAGEMENT = "file_management"
    WEB_OPERATIONS = "web_operations"
    PRODUCTIVITY = "productivity"
    MEMORY = "memory"
    LEARNING = "learning"
    AUTOMATION = "automation"
    HEALTH = "health"
    DEVELOPMENT = "development"
    CONTEXT = "context"
    SYSTEM_CONTROL = "system_control"


class BaseAgent(ABC):
    """
    Base class for all PRISM agents
    
    Agents are autonomous entities that:
    - Handle specific domains of functionality
    - Can operate independently without LLM for simple tasks
    - Report status and health
    - Follow standardized lifecycle (initialize, execute, shutdown)
    - Return standardized responses
    """
    
    def __init__(self, name: str, capabilities: List[AgentCapability]):
        """
        Initialize base agent
        
        Args:
            name: Agent name (e.g., "PersonalFileAgent")
            capabilities: List of agent capabilities
        """
        self.name = name
        self.capabilities = set(capabilities)
        self.status = AgentStatus.INITIALIZING
        self.initialized_at: Optional[datetime] = None
        self.last_execution: Optional[datetime] = None
        self.execution_count = 0
        self.error_count = 0
        self._lock = asyncio.Lock()
        
        logger.info(f"Agent '{self.name}' created with capabilities: {[c.value for c in capabilities]}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize agent (load resources, setup connections, etc.)
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute a task
        
        Args:
            task: Task description or command
            context: Optional context data (user preferences, conversation history, etc.)
            
        Returns:
            AgentResponse: Standardized response
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Cleanup and shutdown agent
        
        Returns:
            bool: True if shutdown successful
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Dict with health status information
        """
        return {
            'name': self.name,
            'status': self.status.value,
            'initialized_at': self.initialized_at.isoformat() if self.initialized_at else None,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'capabilities': [c.value for c in self.capabilities],
            'healthy': self.status in [AgentStatus.READY, AgentStatus.BUSY]
        }
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has specific capability"""
        return capability in self.capabilities
    
    def has_any_capability(self, capabilities: List[AgentCapability]) -> bool:
        """Check if agent has any of specified capabilities"""
        return bool(self.capabilities.intersection(set(capabilities)))
    
    async def _safe_execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Safe execution wrapper with error handling and status tracking
        
        Args:
            task: Task description
            context: Optional context
            
        Returns:
            AgentResponse: Response from agent or error response
        """
        async with self._lock:
            if self.status not in [AgentStatus.READY, AgentStatus.BUSY]:
                return AgentResponse.failure(
                    message=f"Agent {self.name} is not ready (status: {self.status.value})",
                    agent_name=self.name,
                    error="Agent not in ready state"
                )
            
            prev_status = self.status
            self.status = AgentStatus.BUSY
            
            try:
                logger.debug(f"Agent '{self.name}' executing task: {task[:100]}")
                response = await self.execute(task, context)
                
                self.last_execution = datetime.now()
                self.execution_count += 1
                
                if not response.is_success():
                    self.error_count += 1
                
                self.status = prev_status
                return response
                
            except Exception as e:
                self.error_count += 1
                self.status = AgentStatus.ERROR
                logger.error(f"Agent '{self.name}' execution failed: {str(e)}")
                
                return AgentResponse.failure(
                    message=f"Agent execution failed: {str(e)}",
                    agent_name=self.name,
                    error=str(e)
                )
    
    async def _initialize_agent(self) -> bool:
        """Initialize agent with status tracking"""
        try:
            self.status = AgentStatus.INITIALIZING
            success = await self.initialize()
            
            if success:
                self.status = AgentStatus.READY
                self.initialized_at = datetime.now()
                logger.info(f"Agent '{self.name}' initialized successfully")
            else:
                self.status = AgentStatus.ERROR
                logger.error(f"Agent '{self.name}' initialization failed")
            
            return success
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent '{self.name}' initialization error: {str(e)}")
            return False
    
    async def _shutdown_agent(self) -> bool:
        """Shutdown agent with status tracking"""
        try:
            success = await self.shutdown()
            self.status = AgentStatus.SHUTDOWN
            logger.info(f"Agent '{self.name}' shutdown {'successfully' if success else 'with errors'}")
            return success
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent '{self.name}' shutdown error: {str(e)}")
            return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' status='{self.status.value}'>"
