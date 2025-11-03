# PRISM AI Agents Documentation

## Overview

PRISM implements an **agent-centric architecture** where autonomous agents handle specific domains of functionality. Agents can operate independently without LLM processing for simple tasks, providing faster responses and better reliability.

## Agent Philosophy

### Agent-Centric vs LLM-Centric

**Traditional LLM-Centric Approach**:
```
User Input → LLM → Action Extraction → System Execution
```
- LLM makes all decisions
- Agents are passive tools
- Slower (every request needs LLM)
- Fails if LLM unavailable

**PRISM Agent-Centric Approach**:
```
User Input → Intent Parsing (LLM) → Agent Coordinator → Agents
                                                           ↓
                                                    Execute Independently
                                                           ↓
                                                    LLM (only if needed)
```
- Agents are autonomous decision-makers
- LLM used for intent parsing and complex reasoning
- Faster (skip LLM for routine operations)
- More reliable (agents have fallback logic)

### Benefits

1. **Modularity** - Each agent is independent, testable, replaceable
2. **Scalability** - Add new agents without modifying core
3. **Autonomy** - Agents make decisions without LLM for simple tasks
4. **Reliability** - Fallback to agent logic if LLM fails
5. **Efficiency** - Skip LLM for routine operations
6. **Extensibility** - Plugin system becomes natural

## Agent Lifecycle

### States

```python
class AgentStatus(Enum):
    INITIALIZING = "initializing"  # Setting up resources
    READY = "ready"                # Available for tasks
    BUSY = "busy"                  # Currently executing
    ERROR = "error"                # Error occurred
    SHUTDOWN = "shutdown"          # Cleaned up
```

### Lifecycle Methods

```python
class BaseAgent(ABC):
    async def initialize(self) -> bool:
        """Setup resources, connections, etc."""
        pass
    
    async def execute(self, task: str, context: Dict) -> AgentResponse:
        """Execute a task"""
        pass
    
    async def shutdown(self) -> bool:
        """Cleanup and shutdown"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Return health status"""
        pass
```

### Execution Flow

```
1. Agent Registration
   - Agent created with name and capabilities
   - Registered in AgentRegistry
   - Initialized (resources loaded)
   - Status: INITIALIZING → READY

2. Task Execution
   - Status: READY → BUSY
   - Execute task with context
   - Track execution metrics
   - Status: BUSY → READY (or ERROR)

3. Shutdown
   - Cleanup resources
   - Unregister from registry
   - Status: READY → SHUTDOWN
```

## Agent Registry

### Purpose

Central registry for agent management, discovery, and routing.

### Features

- **Registration**: Register/unregister agents dynamically
- **Discovery**: Find agents by capability
- **Health Monitoring**: Track agent health and status
- **Capability Indexing**: Fast lookup by capability

### Usage

```python
# Create registry
registry = AgentRegistry()

# Register agent
file_agent = PersonalFileAgent()
await registry.register(file_agent)

# Find agents by capability
agents = registry.get_agents_by_capability(AgentCapability.FILE_MANAGEMENT)

# Health check
health = await registry.health_check_all()

# Shutdown all
await registry.shutdown_all()
```

### Statistics

```python
stats = registry.get_statistics()
# Returns:
{
    'total_agents': 3,
    'healthy_agents': 3,
    'registered_capabilities': 4,
    'agents_by_status': {
        'ready': 3,
        'busy': 0,
        'error': 0
    }
}
```

## Agent Coordinator

### Purpose

Routes tasks to appropriate agents based on capabilities and intent.

### Routing Strategy

```python
async def execute_task_with_intent(intent_data, context):
    """
    1. Extract agent_type from intent
    2. Map to capability
    3. Find agents with capability
    4. Execute with first matching agent
    5. Return standardized response
    """
```

### Intent-Based Execution

The coordinator uses LLM-parsed intent for precise routing:

```python
intent_data = {
    'agent_type': 'file_management',
    'task_type': 'search_files',
    'parameters': {
        'search_term': 'coolie',
        'location': 'downloads',
        'file_type': 'video'
    },
    'confidence': 0.95
}

response = await coordinator.execute_task_with_intent(intent_data, context)
```

### Multi-Agent Tasks

```python
# Execute tasks across multiple agents in parallel
agent_tasks = {
    'PersonalFileAgent': 'search for project files',
    'PersonalWebAgent': 'research Python tutorials'
}

responses = await coordinator.execute_multi_agent_task(
    task="Research and organize",
    agent_tasks=agent_tasks,
    context=context
)
```

## Agent Capabilities

### Capability Enum

```python
class AgentCapability(Enum):
    FILE_MANAGEMENT = "file_management"      # File operations
    WEB_OPERATIONS = "web_operations"        # Web research, monitoring
    PRODUCTIVITY = "productivity"            # Focus, habits, tracking
    SYSTEM_CONTROL = "system_control"        # App/system control
    MEMORY = "memory"                        # Data storage, retrieval
    LEARNING = "learning"                    # Pattern recognition
    AUTOMATION = "automation"                # Task automation
    HEALTH = "health"                        # System health monitoring
    DEVELOPMENT = "development"              # Dev tools integration
    CONTEXT = "context"                      # Context awareness
```

### Capability Mapping

```python
# Intent to Capability
capability_map = {
    'file_management': AgentCapability.FILE_MANAGEMENT,
    'web_operations': AgentCapability.WEB_OPERATIONS,
    'productivity': AgentCapability.PRODUCTIVITY,
    'system_control': AgentCapability.SYSTEM_CONTROL,
}
```

## Agent Response Format

### AgentResponse Class

```python
@dataclass
class AgentResponse:
    status: ResponseStatus          # SUCCESS, FAILURE, PARTIAL
    message: str                    # Human-readable message
    agent_name: str                 # Agent that handled request
    data: Optional[Dict] = None     # Structured data
    actions_taken: List[str] = []   # Actions performed
    suggestions: List[str] = []     # Suggestions for user
    error: Optional[str] = None     # Error details
    requires_followup: bool = False # Needs more input
    metadata: Optional[Dict] = None # Additional metadata
    timestamp: datetime             # Response timestamp
```

### Response Status

```python
class ResponseStatus(Enum):
    SUCCESS = "success"      # Task completed successfully
    FAILURE = "failure"      # Task failed
    PARTIAL = "partial"      # Partially completed
```

### Creating Responses

```python
# Success
return AgentResponse.success(
    message="Found 5 files matching 'report'",
    agent_name=self.name,
    data={'matches': [...], 'count': 5},
    actions_taken=["Searched Downloads folder"],
    suggestions=["Open most recent file?"]
)

# Failure
return AgentResponse.failure(
    message="File not found",
    agent_name=self.name,
    error="No matching files in specified location"
)

# Partial
return AgentResponse.partial(
    message="Found some results but search incomplete",
    agent_name=self.name,
    data={'partial_results': [...]},
    error="Permission denied for some directories"
)
```

## Built-in Agents

### 1. PersonalFileAgent

**Capabilities**: FILE_MANAGEMENT, SYSTEM_CONTROL

**Purpose**: Handle all file-related operations

**Features**:
- Auto-organize downloads by file type
- Natural language file search
- Windows Search Index integration (10x-100x faster)
- File opening with fuzzy matching
- Backup system
- Old file cleanup

**Supported Tasks**:

```python
# Organize downloads
await agent.execute("organize_downloads", context)

# Search files
await agent.execute("search_files", {
    'task_type': 'search_files',
    'parameters': {
        'search_term': 'report',
        'location': 'documents',
        'file_type': 'document'
    }
})

# Open file
await agent.execute("open_file", {
    'task_type': 'open_file',
    'parameters': {
        'search_term': 'coolie',
        'location': 'downloads',
        'file_type': 'video'
    }
})

# Backup files
await agent.execute("backup", {
    'task_type': 'backup',
    'parameters': {'path': '/path/to/files'}
})

# Cleanup old files
await agent.execute("cleanup", {
    'task_type': 'cleanup',
    'parameters': {'days': 90}
})
```

**File Categories**:

```python
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
```

**Search Strategy**:

```
1. Try Windows Search Index (instant results)
   ↓ (if fails)
2. Try DIR command (fast recursive)
   ↓ (if fails)
3. Fallback to Python rglob (slow but reliable)
```

**Example Response**:

```python
{
    'status': 'success',
    'message': 'Found 3 files matching "report" in documents',
    'agent_name': 'PersonalFileAgent',
    'data': {
        'matches': [
            {
                'name': 'Q4_Report.pdf',
                'path': 'C:/Users/.../Documents/Q4_Report.pdf',
                'size': 524288,
                'modified': '2025-01-15T10:30:00'
            },
            ...
        ],
        'search_term': 'report',
        'location': 'documents',
        'file_type': 'document'
    },
    'actions_taken': ['Searched Documents folder'],
    'suggestions': ['Open most recent file?']
}
```

### 2. PersonalWebAgent

**Capabilities**: WEB_OPERATIONS

**Purpose**: Handle web research, monitoring, and content management

**Features**:
- Topic research planning
- Website monitoring
- Content saving/archiving
- Web search integration

**Supported Tasks**:

```python
# Research topic
await agent.execute("research Python best practices", context)

# Monitor website
await agent.execute("monitor https://example.com", context)

# Save content
await agent.execute("save content from https://example.com", context)

# Web search
await agent.execute("search web for AI tutorials", context)
```

**Example Response**:

```python
{
    'status': 'success',
    'message': 'Research plan created for topic: Python best practices',
    'agent_name': 'PersonalWebAgent',
    'data': {
        'topic': 'Python best practices',
        'search_queries': [
            'Python best practices overview',
            'Python best practices latest developments'
        ],
        'sources_to_check': ['Wikipedia', 'Official docs', 'Expert blogs']
    },
    'actions_taken': ['Created research plan'],
    'suggestions': [
        "Use 'search web for' to execute searches",
        "Save interesting content for later review"
    ]
}
```

### 3. PersonalProductivityAgent

**Capabilities**: PRODUCTIVITY

**Purpose**: Manage focus, habits, and productivity tracking

**Features**:
- Focus mode management
- Break reminders
- Productivity tracking
- Habit monitoring

**Supported Tasks**:

```python
# Start focus session
await agent.execute("start focus session 25 minutes", context)

# Track habit
await agent.execute("track habit: exercise", context)

# Get productivity stats
await agent.execute("show productivity stats", context)
```

## Creating Custom Agents

### Step 1: Define Agent Class

```python
from backend.agents.base_agent import BaseAgent, AgentCapability
from backend.agents.agent_response import AgentResponse

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyCustomAgent",
            capabilities=[AgentCapability.AUTOMATION]
        )
        # Initialize agent-specific state
        self.custom_data = {}
    
    async def initialize(self) -> bool:
        """Setup resources"""
        try:
            # Load configuration, connect to services, etc.
            logger.info(f"{self.name} initialized")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def execute(self, task: str, context: Optional[Dict] = None) -> AgentResponse:
        """Execute task"""
        try:
            # Parse task
            if 'my_task' in task.lower():
                return await self._handle_my_task(task, context)
            else:
                return AgentResponse.failure(
                    message=f"Unknown task: {task}",
                    agent_name=self.name,
                    error="Task not recognized"
                )
        except Exception as e:
            return AgentResponse.failure(
                message=f"Execution failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _handle_my_task(self, task: str, context: Dict) -> AgentResponse:
        """Handle specific task"""
        # Implement task logic
        result = self._do_something()
        
        return AgentResponse.success(
            message="Task completed successfully",
            agent_name=self.name,
            data={'result': result},
            actions_taken=["Performed custom action"]
        )
    
    async def shutdown(self) -> bool:
        """Cleanup"""
        logger.info(f"{self.name} shutting down")
        return True
```

### Step 2: Register Agent

```python
# In coordinator.py or agent initialization
custom_agent = MyCustomAgent()
await self.agent_registry.register(custom_agent)
```

### Step 3: Update Intent Parsing (Optional)

```python
# In ai_engine.py parse_user_intent()
# Add examples for your agent's tasks
```

## Agent Communication

### Context Passing

Agents receive context with:
- `conversation_history` - Recent conversation
- `system_context` - System state, running apps, etc.
- `task_type` - Specific task identifier
- `parameters` - Structured parameters from intent parsing

```python
context = {
    'conversation_history': [...],
    'system_context': {
        'running_applications': ['chrome', 'vscode'],
        'current_directory': 'C:/Users/...',
        'mcp_available': True
    },
    'task_type': 'search_files',
    'parameters': {
        'search_term': 'report',
        'location': 'documents'
    }
}
```

### Agent Collaboration

Agents can request help from other agents:

```python
async def execute(self, task: str, context: Dict) -> AgentResponse:
    # Get reference to other agent
    web_agent = self.registry.get_agent('PersonalWebAgent')
    
    # Execute subtask
    web_result = await web_agent.execute("search for info", context)
    
    # Use result in your processing
    if web_result.is_success():
        data = web_result.data
        # Process data...
```

## Intent Parsing

### LLM-Based Intent Extraction

The AI Engine parses user input into structured intent:

```python
intent_data = await ai_engine.parse_user_intent(
    user_input="search for coolie movie in my downloads folder",
    context=None
)

# Returns:
{
    'agent_type': 'file_management',
    'task_type': 'search_files',
    'parameters': {
        'search_term': 'coolie',
        'location': 'downloads',
        'file_type': 'video'
    },
    'confidence': 0.95
}
```

### Intent Examples

**File Search**:
```
Input: "find project report pdf"
Intent: {
    'agent_type': 'file_management',
    'task_type': 'search_files',
    'parameters': {
        'search_term': 'project report',
        'file_type': 'document'
    }
}
```

**File Opening**:
```
Input: "open og movie from downloads"
Intent: {
    'agent_type': 'file_management',
    'task_type': 'open_file',
    'parameters': {
        'search_term': 'og',
        'location': 'downloads',
        'file_type': 'video'
    }
}
```

**Web Search**:
```
Input: "search for python tutorial"
Intent: {
    'agent_type': 'web_operations',
    'task_type': 'web_search',
    'parameters': {
        'query': 'python tutorial'
    }
}
```

### Confidence Thresholds

```python
if intent_data.get('confidence', 0) < 0.5:
    # Low confidence - fallback to LLM
    return None

if intent_data.get('agent_type') == 'conversational':
    # Conversational task - use LLM
    return None
```

## Error Handling

### Agent-Level Errors

```python
try:
    result = await agent.execute(task, context)
except Exception as e:
    # Agent catches and returns failure response
    return AgentResponse.failure(
        message=f"Task failed: {str(e)}",
        agent_name=self.name,
        error=str(e)
    )
```

### Coordinator-Level Fallback

```python
# Try agent execution
agent_result = await coordinator.execute_task_with_intent(intent_data)

if not agent_result or not agent_result.is_success():
    # Fallback to LLM processing
    response = await ai_engine.process_input(user_input, context)
```

### Safe Execution Wrapper

```python
async def _safe_execute(self, task: str, context: Dict) -> AgentResponse:
    """
    Wrapper that:
    - Checks agent status
    - Sets BUSY state
    - Tracks execution metrics
    - Handles exceptions
    - Returns to READY state
    """
```

## Performance Considerations

### Fast Path for Simple Tasks

```
User: "search for report"
  ↓
Intent Parsing (LLM) - 200ms
  ↓
Agent Execution - 50ms (Windows Search)
  ↓
Total: ~250ms
```

### Slow Path with LLM Fallback

```
User: "tell me about quantum computing"
  ↓
Intent Parsing (LLM) - 200ms
  ↓
Agent Execution - FAIL (conversational)
  ↓
LLM Processing - 1000ms
  ↓
Total: ~1200ms
```

### Optimization Strategies

1. **Cache Intent Patterns** - Common queries cached
2. **Parallel Agent Execution** - Multiple agents run concurrently
3. **Lazy Loading** - Agents initialized on first use
4. **Connection Pooling** - Reuse connections to external services

## Testing Agents

### Unit Testing

```python
import pytest
from backend.agents.personal_file_agent import PersonalFileAgent

@pytest.mark.asyncio
async def test_file_search():
    agent = PersonalFileAgent()
    await agent.initialize()
    
    response = await agent.execute("search_files", {
        'task_type': 'search_files',
        'parameters': {
            'search_term': 'test',
            'location': 'downloads'
        }
    })
    
    assert response.is_success()
    assert 'matches' in response.data
    
    await agent.shutdown()
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_agent_coordinator():
    registry = AgentRegistry()
    coordinator = AgentCoordinator(registry)
    
    # Register agents
    file_agent = PersonalFileAgent()
    await registry.register(file_agent)
    
    # Test routing
    intent = {
        'agent_type': 'file_management',
        'task_type': 'search_files',
        'parameters': {'search_term': 'test'}
    }
    
    response = await coordinator.execute_task_with_intent(intent)
    assert response.is_success()
```

## Best Practices

### 1. Single Responsibility

Each agent should handle one domain:
```python
# Good
class FileAgent: # Handles files only
class WebAgent:  # Handles web only

# Bad
class SuperAgent: # Handles everything
```

### 2. Fail Fast

Return early on invalid input:
```python
if not search_term:
    return AgentResponse.failure(
        message="No search term provided",
        agent_name=self.name,
        error="Missing required parameter"
    )
```

### 3. Structured Responses

Always return structured data:
```python
return AgentResponse.success(
    message="Found 5 files",
    data={
        'matches': [...],
        'count': 5,
        'truncated': False
    }
)
```

### 4. Logging

Log important operations:
```python
logger.info(f"Searching for '{search_term}' in {location}")
logger.debug(f"Found {len(matches)} matches")
logger.error(f"Search failed: {error}")
```

### 5. Resource Cleanup

Always cleanup in shutdown:
```python
async def shutdown(self) -> bool:
    # Close connections
    # Release resources
    # Save state
    return True
```

## Future Enhancements

### Planned Features

1. **Agent Learning** - Agents learn from user patterns
2. **Agent Collaboration** - Multi-agent workflows
3. **Plugin System** - Hot-loadable custom agents
4. **Agent Marketplace** - Share and discover agents
5. **Agent Analytics** - Performance metrics and insights
6. **Agent Versioning** - Update agents independently
7. **Agent Sandboxing** - Secure execution environment
8. **Agent Scheduling** - Cron-like agent tasks

### Experimental Features

- **Autonomous Agents** - Agents that proactively suggest actions
- **Agent Chains** - Sequential agent execution pipelines
- **Agent Voting** - Multiple agents vote on best action
- **Agent Memory** - Shared memory between agents
