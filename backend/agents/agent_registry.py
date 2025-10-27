"""
Agent Registry System
Manages agent lifecycle, discovery, and routing
"""

import asyncio
from typing import Dict, List, Optional, Set
from loguru import logger

from backend.agents.base_agent import BaseAgent, AgentCapability, AgentStatus


class AgentRegistry:
    """
    Central registry for all agents in the system
    
    Handles:
    - Agent registration and discovery
    - Capability-based routing
    - Health monitoring
    - Dynamic loading/unloading
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._capability_index: Dict[AgentCapability, Set[str]] = {}
        self._lock = asyncio.Lock()
        self.initialized = False
        
        logger.info("AgentRegistry initialized")
    
    async def register(self, agent: BaseAgent) -> bool:
        """
        Register an agent
        
        Args:
            agent: Agent instance to register
            
        Returns:
            bool: True if registration successful
        """
        async with self._lock:
            if agent.name in self._agents:
                logger.warning(f"Agent '{agent.name}' already registered, replacing")
            
            # Initialize agent
            success = await agent._initialize_agent()
            if not success:
                logger.error(f"Failed to initialize agent '{agent.name}'")
                return False
            
            # Register agent
            self._agents[agent.name] = agent
            
            # Index capabilities
            for capability in agent.capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = set()
                self._capability_index[capability].add(agent.name)
            
            logger.info(f"Agent '{agent.name}' registered with {len(agent.capabilities)} capabilities")
            return True
    
    async def unregister(self, agent_name: str) -> bool:
        """
        Unregister an agent
        
        Args:
            agent_name: Name of agent to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        async with self._lock:
            if agent_name not in self._agents:
                logger.warning(f"Agent '{agent_name}' not found in registry")
                return False
            
            agent = self._agents[agent_name]
            
            # Shutdown agent
            await agent._shutdown_agent()
            
            # Remove from capability index
            for capability in agent.capabilities:
                if capability in self._capability_index:
                    self._capability_index[capability].discard(agent_name)
                    if not self._capability_index[capability]:
                        del self._capability_index[capability]
            
            # Remove from registry
            del self._agents[agent_name]
            
            logger.info(f"Agent '{agent_name}' unregistered")
            return True
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        return self._agents.get(agent_name)
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[BaseAgent]:
        """
        Get all agents with specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agents with that capability
        """
        agent_names = self._capability_index.get(capability, set())
        return [self._agents[name] for name in agent_names if name in self._agents]
    
    def get_agents_by_capabilities(self, capabilities: List[AgentCapability]) -> List[BaseAgent]:
        """
        Get all agents with any of specified capabilities
        
        Args:
            capabilities: List of capabilities
            
        Returns:
            List of agents with any matching capability
        """
        matching_agents = set()
        for capability in capabilities:
            agent_names = self._capability_index.get(capability, set())
            matching_agents.update(agent_names)
        
        return [self._agents[name] for name in matching_agents if name in self._agents]
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(self._agents.values())
    
    def get_agent_names(self) -> List[str]:
        """Get names of all registered agents"""
        return list(self._agents.keys())
    
    async def health_check_all(self) -> Dict[str, Dict]:
        """
        Run health check on all agents
        
        Returns:
            Dict mapping agent names to health check results
        """
        health_results = {}
        
        for agent_name, agent in self._agents.items():
            try:
                health_results[agent_name] = await agent.health_check()
            except Exception as e:
                logger.error(f"Health check failed for agent '{agent_name}': {str(e)}")
                health_results[agent_name] = {
                    'name': agent_name,
                    'status': 'error',
                    'healthy': False,
                    'error': str(e)
                }
        
        return health_results
    
    def get_healthy_agents(self) -> List[BaseAgent]:
        """Get all healthy agents (READY or BUSY status)"""
        return [
            agent for agent in self._agents.values()
            if agent.status in [AgentStatus.READY, AgentStatus.BUSY]
        ]
    
    async def shutdown_all(self) -> bool:
        """
        Shutdown all agents
        
        Returns:
            bool: True if all shutdowns successful
        """
        success = True
        agent_names = list(self._agents.keys())
        
        for agent_name in agent_names:
            try:
                result = await self.unregister(agent_name)
                success = success and result
            except Exception as e:
                logger.error(f"Failed to shutdown agent '{agent_name}': {str(e)}")
                success = False
        
        logger.info(f"Agent registry shutdown {'successfully' if success else 'with errors'}")
        return success
    
    def get_statistics(self) -> Dict[str, any]:
        """Get registry statistics"""
        return {
            'total_agents': len(self._agents),
            'healthy_agents': len(self.get_healthy_agents()),
            'registered_capabilities': len(self._capability_index),
            'agents_by_status': {
                status.value: len([a for a in self._agents.values() if a.status == status])
                for status in AgentStatus
            }
        }
    
    def __repr__(self) -> str:
        return f"<AgentRegistry agents={len(self._agents)} capabilities={len(self._capability_index)}>"
