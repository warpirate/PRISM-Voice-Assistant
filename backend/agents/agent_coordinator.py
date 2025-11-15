"""
Agent Coordinator
Enhanced coordinator that routes tasks to appropriate agents
"""

import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from backend.agents.base_agent import AgentCapability
from backend.agents.agent_registry import AgentRegistry
from backend.agents.agent_response import AgentResponse, ResponseStatus


class AgentCoordinator:
    """
    Coordinates tasks between multiple agents
    
    Responsibilities:
    - Parse user intent and determine required capabilities
    - Route tasks to appropriate agents
    - Handle multi-agent workflows
    - Aggregate results from multiple agents
    - Manage fallbacks and error recovery
    """
    
    def __init__(self, registry: AgentRegistry, main_coordinator=None):
        """
        Initialize coordinator
        
        Args:
            registry: Agent registry instance
            main_coordinator: Reference to main PRISM coordinator
        """
        self.registry = registry
        self.task_history: List[Dict[str, Any]] = []
        self._main_coordinator = main_coordinator
        
        logger.info("AgentCoordinator initialized")
    
    async def execute_task_with_intent(
        self,
        intent_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute a task using parsed intent data from LLM
        
        Args:
            intent_data: Parsed intent containing agent_type, task_type, parameters
            context: Optional context data
            
        Returns:
            AgentResponse: Response from agent
        """
        agent_type = intent_data.get('agent_type')
        task_type = intent_data.get('task_type')
        parameters = intent_data.get('parameters', {})
        
        # Map agent_type to capability
        # Note: 'open_app' and system control tasks should use SYSTEM_CONTROL capability
        # but we don't have a dedicated system control agent yet, so route to file_management
        capability_map = {
            'file_management': AgentCapability.FILE_MANAGEMENT,
            'web_operations': AgentCapability.WEB_OPERATIONS,
            'productivity': AgentCapability.PRODUCTIVITY,
            'system_control': AgentCapability.SYSTEM_CONTROL,
        }
        
        # Special handling: if task is 'open_app', it's actually a system control task
        # but should be handled by LLM fallback since we don't have a dedicated agent
        if task_type == 'open_app':
            return AgentResponse.failure(
                message="Application opening requires LLM processing",
                agent_name="AgentCoordinator",
                error="No dedicated system control agent - use LLM fallback"
            )
        
        capability = capability_map.get(agent_type)
        if not capability:
            return AgentResponse.failure(
                message=f"Unknown agent type: {agent_type}",
                agent_name="AgentCoordinator",
                error="Invalid agent type"
            )
        
        # Get agents with required capability
        agents = self.registry.get_agents_by_capabilities([capability])
        
        if not agents:
            return AgentResponse.failure(
                message=f"No agents available for {agent_type}",
                agent_name="AgentCoordinator",
                error="No matching agents found"
            )
        
        agent = agents[0]
        
        logger.info(f"Routing task '{task_type}' to agent '{agent.name}' with parameters: {parameters}")
        
        try:
            # Add intent data to context
            if not context:
                context = {}
            context['task_type'] = task_type
            context['parameters'] = parameters
            
            # Execute with structured parameters
            response = await agent._safe_execute(task_type, context)
            
            # Record task execution
            self.task_history.append({
                'task': task_type,
                'agent': agent.name,
                'parameters': parameters,
                'status': response.status.value,
                'timestamp': response.timestamp.isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return AgentResponse.failure(
                message=f"Task execution error: {str(e)}",
                agent_name="AgentCoordinator",
                error=str(e)
            )
    
    async def execute_task(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[AgentCapability]] = None
    ) -> AgentResponse:
        """
        Execute a task by routing to appropriate agent(s)
        (Legacy method - prefer execute_task_with_intent when using LLM parsing)
        
        Args:
            task: Task description
            context: Optional context data
            capabilities: Optional list of required capabilities (if known)
            
        Returns:
            AgentResponse: Aggregated response from agent(s)
        """
        if not capabilities:
            # If capabilities not specified, try to infer from task
            capabilities = self._infer_capabilities(task)
        
        if not capabilities:
            return AgentResponse.failure(
                message="Could not determine required capabilities for task",
                agent_name="AgentCoordinator",
                error="No capabilities specified or inferred"
            )
        
        # Get agents with required capabilities
        agents = self.registry.get_agents_by_capabilities(capabilities)
        
        if not agents:
            return AgentResponse.failure(
                message=f"No agents available for capabilities: {[c.value for c in capabilities]}",
                agent_name="AgentCoordinator",
                error="No matching agents found"
            )
        
        # For now, use first matching agent (single-agent execution)
        # Future: Implement multi-agent coordination for complex tasks
        agent = agents[0]
        
        logger.info(f"Routing task to agent '{agent.name}' with capabilities {[c.value for c in capabilities]}")
        
        try:
            response = await agent._safe_execute(task, context)
            
            # Record task execution
            self.task_history.append({
                'task': task,
                'agent': agent.name,
                'capabilities': [c.value for c in capabilities],
                'status': response.status.value,
                'timestamp': response.timestamp.isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return AgentResponse.failure(
                message=f"Task execution error: {str(e)}",
                agent_name="AgentCoordinator",
                error=str(e)
            )
    
    async def execute_multi_agent_task(
        self,
        task: str,
        agent_tasks: Dict[str, str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, AgentResponse]:
        """
        Execute a task requiring multiple agents
        
        Args:
            task: Overall task description
            agent_tasks: Dict mapping agent names to their specific tasks
            context: Optional context data
            
        Returns:
            Dict mapping agent names to their responses
        """
        responses = {}
        
        # Execute tasks in parallel
        tasks = []
        agent_names = []
        
        for agent_name, agent_task in agent_tasks.items():
            agent = self.registry.get_agent(agent_name)
            if agent:
                tasks.append(agent._safe_execute(agent_task, context))
                agent_names.append(agent_name)
            else:
                logger.warning(f"Agent '{agent_name}' not found, skipping task")
                responses[agent_name] = AgentResponse.failure(
                    message=f"Agent not found",
                    agent_name=agent_name,
                    error="Agent not registered"
                )
        
        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to agent names
        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                responses[agent_name] = AgentResponse.failure(
                    message=f"Agent execution failed: {str(result)}",
                    agent_name=agent_name,
                    error=str(result)
                )
            else:
                responses[agent_name] = result
        
        return responses
    
    def _infer_capabilities(self, task: str) -> List[AgentCapability]:
        """
        Infer required capabilities from task description
        
        This is a simple keyword-based approach. In production, this would
        use the LLM to understand intent and map to capabilities.
        
        Args:
            task: Task description
            
        Returns:
            List of inferred capabilities
        """
        task_lower = task.lower()
        capabilities = []
        
        # File-related keywords
        file_keywords = ['file', 'folder', 'directory', 'document', 'organize', 'backup', 'search files']
        if any(keyword in task_lower for keyword in file_keywords):
            capabilities.append(AgentCapability.FILE_MANAGEMENT)
        
        # Web-related keywords
        web_keywords = ['web', 'search', 'website', 'browse', 'research', 'monitor', 'url']
        if any(keyword in task_lower for keyword in web_keywords):
            capabilities.append(AgentCapability.WEB_OPERATIONS)
        
        # Productivity keywords
        productivity_keywords = ['focus', 'productivity', 'habit', 'routine', 'schedule', 'break', 'session']
        if any(keyword in task_lower for keyword in productivity_keywords):
            capabilities.append(AgentCapability.PRODUCTIVITY)
        
        # System control keywords
        system_keywords = ['open', 'launch', 'close', 'application', 'app', 'program']
        if any(keyword in task_lower for keyword in system_keywords):
            capabilities.append(AgentCapability.SYSTEM_CONTROL)
        
        return capabilities
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history"""
        return self.task_history[-limit:]
    
    def clear_history(self):
        """Clear task history"""
        self.task_history.clear()
        logger.info("Task history cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get coordinator health status"""
        agent_health = await self.registry.health_check_all()
        stats = self.registry.get_statistics()
        
        return {
            'coordinator_status': 'healthy',
            'total_agents': stats['total_agents'],
            'healthy_agents': stats['healthy_agents'],
            'tasks_executed': len(self.task_history),
            'agent_health': agent_health
        }
