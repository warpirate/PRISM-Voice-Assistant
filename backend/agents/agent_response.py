"""
Standardized Agent Response Format
Consistent response structure for all agents
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ResponseStatus(Enum):
    """Response status codes"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    PENDING = "pending"
    REQUIRES_INPUT = "requires_input"


@dataclass
class AgentResponse:
    """
    Standardized response format for all agents
    
    Attributes:
        status: Response status code
        message: Human-readable response message
        data: Response data payload
        actions_taken: List of actions performed by agent
        suggestions: Optional suggestions for user
        metadata: Additional context or metadata
        timestamp: Response timestamp
        agent_name: Name of agent that generated response
        requires_followup: Whether response requires followup action
        error: Error details if status is FAILURE
    """
    
    status: ResponseStatus
    message: str
    agent_name: str
    data: Optional[Dict[str, Any]] = None
    actions_taken: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    requires_followup: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            'status': self.status.value,
            'message': self.message,
            'agent_name': self.agent_name,
            'data': self.data,
            'actions_taken': self.actions_taken,
            'suggestions': self.suggestions,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'requires_followup': self.requires_followup,
            'error': self.error
        }
    
    @classmethod
    def success(cls, message: str, agent_name: str, **kwargs) -> 'AgentResponse':
        """Create success response"""
        return cls(
            status=ResponseStatus.SUCCESS,
            message=message,
            agent_name=agent_name,
            **kwargs
        )
    
    @classmethod
    def failure(cls, message: str, agent_name: str, error: str = None, **kwargs) -> 'AgentResponse':
        """Create failure response"""
        return cls(
            status=ResponseStatus.FAILURE,
            message=message,
            agent_name=agent_name,
            error=error or message,
            **kwargs
        )
    
    @classmethod
    def pending(cls, message: str, agent_name: str, **kwargs) -> 'AgentResponse':
        """Create pending response"""
        return cls(
            status=ResponseStatus.PENDING,
            message=message,
            agent_name=agent_name,
            **kwargs
        )
    
    def is_success(self) -> bool:
        """Check if response is successful"""
        return self.status in [ResponseStatus.SUCCESS, ResponseStatus.PARTIAL_SUCCESS]
