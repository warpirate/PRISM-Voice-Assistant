# PRISM System Architecture

## Overview

PRISM (Personal Response Interface for System Management) is a sophisticated voice-activated AI assistant built with a hybrid agent-centric and LLM-centric architecture. The system combines Python backend processing with an Electron-based glassmorphic UI.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ELECTRON UI (Frontend)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Glassmorphic │  │   Matrix     │  │  Conversation│     │
│  │     Orb      │  │ Visualization│  │    Panel     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                    WebSocket (Port 9876)
                            │
┌─────────────────────────────────────────────────────────────┐
│                   PYTHON BACKEND (Core)                      │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PRISM COORDINATOR (Hub)                   │  │
│  │  • State Management                                    │  │
│  │  • Message Routing                                     │  │
│  │  • Subsystem Orchestration                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                  │
│  ┌─────────────┬──────────┴──────────┬──────────────────┐  │
│  │             │                      │                   │  │
│  ▼             ▼                      ▼                   ▼  │
│ ┌──────┐  ┌────────┐  ┌──────────┐  ┌────────────────┐    │
│ │Voice │  │   AI   │  │  System  │  │     Memory     │    │
│ │Pipeline│ │ Engine │  │ Control  │  │     System     │    │
│ └──────┘  └────────┘  └──────────┘  └────────────────┘    │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              AGENT SYSTEM (Autonomous)                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │ File Agent   │  │  Web Agent   │  │Productivity│  │  │
│  │  │              │  │              │  │   Agent    │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │           Managed by Agent Coordinator                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    External Services
                            │
              ┌─────────────┴─────────────┐
              │                           │
         ┌────▼────┐              ┌──────▼──────┐
         │ Gemini  │              │   Windows   │
         │   API   │              │  MCP Server │
         └─────────┘              └─────────────┘
```

## Core Components

### 1. Coordinator (`coordinator.py`)

**Purpose**: Central orchestration hub for all PRISM subsystems

**Responsibilities**:
- System lifecycle management (start, shutdown)
- State management (idle, listening, processing, responding, executing, error)
- Message routing between UI and backend
- Subsystem coordination (voice, AI, system control, memory, agents)
- Processing lock management to prevent concurrent operations
- Context caching for performance optimization

**Key Methods**:
- `start()` - Initialize all subsystems
- `process_text_input()` - Handle text-based user input
- `activate_voice()` - Trigger voice input
- `_process_user_input()` - Core processing pipeline
- `_execute_actions()` - Execute system actions
- `_try_agent_execution()` - Route tasks to agents

**State Flow**:
```
IDLE → LISTENING → PROCESSING → RESPONDING/EXECUTING → IDLE
                                      ↓
                                   ERROR → IDLE
```

### 2. Voice Pipeline (`voice_pipeline.py`)

**Purpose**: Handle all voice interaction (STT, TTS)

**Components**:
- **Speech Recognition**: Google Speech Recognition API
- **Text-to-Speech**: pyttsx3 engine with worker thread
- **Audio Processing**: PyAudio for microphone input

**Features**:
- Manual activation (no wake word by default)
- Ambient noise calibration
- Configurable voice, rate, and volume
- Asynchronous TTS queue system

**Key Methods**:
- `initialize()` - Setup audio components
- `start_listening()` - Capture and recognize speech
- `speak()` - Queue text for TTS output

### 3. Live Voice (`live_voice.py`)

**Purpose**: Real-time bidirectional voice streaming with Gemini Live API

**Features**:
- Native audio streaming (24kHz mono)
- Bidirectional communication (simultaneous input/output)
- Session management with reconnection logic
- Audio level monitoring for visualization

**Architecture**:
```
Microphone → Input Stream → Gemini Live API
                                    ↓
Speaker ← Output Stream ← Audio Response
```

**Key Classes**:
- `LiveVoiceSession` - Manages single live session
- `LiveVoiceManager` - High-level session lifecycle

### 4. AI Engine (`ai_engine.py`)

**Purpose**: Natural language understanding and response generation

**Provider**: Google Gemini 2.5 Flash

**Capabilities**:
- Natural language processing
- Intent parsing for agent routing
- Action extraction from responses
- Multi-turn conversation support
- Fallback rule-based processing

**System Prompt Design**:
- Defines PRISM's personality and capabilities
- Specifies action format for system control
- Includes examples for UI automation
- Supports multi-task queries

**Key Methods**:
- `process_input()` - Main NLU pipeline
- `parse_user_intent()` - Extract structured intent for agents
- `parse_app_control_intent()` - Parse app control queries
- `_extract_actions()` - Parse ACTION tags from responses

**Action Format**:
```
ACTION: {"type": "action_type", "parameters": {...}}
```

### 5. System Control (`system_control.py`)

**Purpose**: Execute system-level operations

**Capabilities**:
- Application management (open, close, focus)
- File operations (create, search, open)
- Web search
- System commands (with safety checks)
- MCP integration for UI automation

**Application Discovery**:
- Scans Start Menu, Program Files
- Fuzzy matching for typo tolerance
- Alias support for common variations
- Confidence scoring for matches

**MCP Actions**:
- `mcp_focus_window` - Focus application window
- `mcp_hotkey` - Press keyboard shortcuts
- `mcp_type_text` - Type text input
- `mcp_press_key` - Press single key
- `mcp_click` - Click at coordinates

### 6. Memory System (`memory_system.py`)

**Purpose**: Persistent storage and learning

**Database**: SQLite with three tables:
- `interactions` - User/assistant messages
- `preferences` - User settings
- `patterns` - Learned behaviors

**Features**:
- Conversation history storage
- Pattern recognition (commands, apps)
- Automatic data cleanup (retention policy)
- Data export functionality

**Privacy Controls**:
- Configurable retention period
- Optional conversation storage
- Data export/clear capabilities

### 7. WebSocket Bridge (`websocket_bridge.py`)

**Purpose**: Communication between Python backend and Electron UI

**Architecture**:
- WebSocket server in Electron (port 9876)
- WebSocket client in Python
- Bidirectional message passing
- Automatic reconnection logic

**Message Types**:
- `state_change` - System state updates
- `user_message` - User input
- `assistant_message` - AI responses
- `audio_level` - Audio visualization data
- `error` - Error notifications

### 8. Configuration (`config.py`)

**Purpose**: Centralized configuration management

**Configuration Sections**:
- **Voice**: Language, TTS settings, feedback
- **AI**: Provider, API key, model, temperature
- **UI**: Theme, transparency, animations
- **Privacy**: Storage, retention, analytics

**Environment Variables**:
Loaded from `.env` file with fallback defaults

## Agent System

### Agent Architecture

PRISM implements an **agent-centric** architecture where agents are autonomous entities that can handle tasks independently without always requiring LLM processing.

```
User Input → Intent Parsing (LLM) → Agent Coordinator
                                            ↓
                              ┌─────────────┴─────────────┐
                              │                           │
                        File Agent                   Web Agent
                              │                           │
                        Execute Task              Execute Task
                              │                           │
                        Return Response          Return Response
```

### Base Agent (`base_agent.py`)

**Abstract Base Class** for all agents

**Lifecycle**:
1. `initialize()` - Setup resources
2. `execute()` - Process tasks
3. `shutdown()` - Cleanup

**Status States**:
- INITIALIZING
- READY
- BUSY
- ERROR
- SHUTDOWN

**Capabilities** (AgentCapability enum):
- FILE_MANAGEMENT
- WEB_OPERATIONS
- PRODUCTIVITY
- SYSTEM_CONTROL
- MEMORY
- LEARNING
- AUTOMATION

### Agent Registry (`agent_registry.py`)

**Purpose**: Manage agent lifecycle and discovery

**Features**:
- Agent registration/unregistration
- Capability-based routing
- Health monitoring
- Concurrent execution safety

**Key Methods**:
- `register()` - Register new agent
- `get_agents_by_capability()` - Find agents by capability
- `health_check_all()` - Check all agent health

### Agent Coordinator (`agent_coordinator.py`)

**Purpose**: Route tasks to appropriate agents

**Routing Strategy**:
1. Parse user intent with LLM
2. Map intent to agent capabilities
3. Select appropriate agent
4. Execute task with context
5. Return standardized response

**Key Methods**:
- `execute_task_with_intent()` - Execute with parsed intent
- `execute_multi_agent_task()` - Coordinate multiple agents
- `_infer_capabilities()` - Keyword-based capability inference

### Personal File Agent (`personal_file_agent.py`)

**Capabilities**: FILE_MANAGEMENT, SYSTEM_CONTROL

**Features**:
- Auto-organize downloads by file type
- Natural language file search
- Windows Search Index integration (fast)
- File opening with fuzzy matching
- Backup system
- Old file cleanup

**File Categories**:
- Documents (pdf, doc, txt)
- Images (jpg, png, gif)
- Videos (mp4, mkv, avi)
- Audio (mp3, wav, flac)
- Archives (zip, rar, 7z)
- Code (py, js, java)
- Spreadsheets (xlsx, csv)
- Presentations (ppt, pptx)

**Search Strategy**:
1. Try Windows Search Index (instant)
2. Fallback to recursive directory scan
3. Fuzzy matching for typo tolerance
4. Sort by relevance and recency

### Personal Web Agent (`personal_web_agent.py`)

**Capabilities**: WEB_OPERATIONS

**Features**:
- Topic research planning
- Website monitoring
- Content saving/archiving
- Web search integration

**Planned Features**:
- Price tracking
- Content summarization
- RSS feed monitoring

### Personal Productivity Agent (`personal_productivity_agent.py`)

**Capabilities**: PRODUCTIVITY

**Features**:
- Focus mode management
- Break reminders
- Productivity tracking
- Habit monitoring

## Data Flow

### User Input Processing

```
1. User Input (Voice/Text)
        ↓
2. Coordinator.process_text_input()
        ↓
3. Store in Memory (if enabled)
        ↓
4. Try MCP Query Handling (screen context)
        ↓
5. Try Agent Execution
   - Parse intent with AI Engine
   - Route to Agent Coordinator
   - Execute with agent
        ↓
6. Fallback to LLM Processing
   - Build context (system state, history)
   - Call Gemini API
   - Extract actions
        ↓
7. Execute Actions (if required)
   - System Control operations
   - MCP automation
        ↓
8. Deliver Response
   - Send to UI via WebSocket
   - Speak via TTS (if enabled)
        ↓
9. Return to IDLE state
```

### Action Execution Pipeline

```
1. AI Response with ACTION tags
        ↓
2. Extract actions (JSON parsing)
        ↓
3. For each action:
   - Validate action type
   - Execute via System Control
   - Add delays for UI sync
   - Handle errors
        ↓
4. Notify user of results
```

## UI Architecture

### Electron Main Process (`main.js`)

**Responsibilities**:
- Window management
- System tray integration
- Global hotkey registration
- WebSocket server hosting
- Backend process spawning
- IPC message handling

**Window Configuration**:
- Frameless, transparent window
- Always on top
- Positioned at bottom-right
- 380x480 dimensions

### Renderer Process (`renderer.js`)

**Responsibilities**:
- UI state management
- User interaction handling
- Backend message processing
- Animation control
- Settings management

**State Management**:
```javascript
AppState = {
    currentState: 'idle',
    isListening: false,
    isProcessing: false,
    isLiveMode: false,
    conversationHistory: [],
    settings: {...}
}
```

**UI Components**:
- Central orb with state-based animations
- Matrix visualization (digital rain effect)
- Conversation panel with message history
- Input area (voice, live voice, text)
- Settings panel (theme, transparency, etc.)

### Glassmorphic Design (`styles.css`)

**Key Features**:
- Frosted glass effect with backdrop-filter
- Smooth transitions and animations
- State-based color coding
- Responsive hover effects
- Dark theme optimized

**CSS Variables**:
```css
--glass-bg: rgba(20, 20, 30, 0.85)
--glass-border: rgba(255, 255, 255, 0.1)
--accent-primary: #667eea
--accent-secondary: #764ba2
```

## External Integrations

### Google Gemini API

**Model**: gemini-2.5-flash (October 2025)

**Features**:
- 1M token context window
- Multimodal support (text, audio, images)
- Free tier: 250 requests/day
- Safety settings configurable

**Configuration**:
```python
generation_config={
    "temperature": 0.7,
    "max_output_tokens": 2048,
}
```

### Gemini Live API

**Model**: gemini-2.0-flash-exp

**Features**:
- Real-time bidirectional audio streaming
- 24kHz mono audio
- Native audio processing
- Low latency responses

**Voice Configuration**:
```python
voice_config=VoiceConfig(
    prebuilt_voice_config=PrebuiltVoiceConfig(
        voice_name="Puck"  # Natural conversational voice
    )
)
```

### Windows MCP Server

**Purpose**: UI automation and screen context

**Capabilities**:
- Window management (focus, close, minimize)
- Keyboard automation (hotkeys, typing)
- Mouse automation (click, move)
- Screen context analysis
- Memory information

## Performance Optimizations

### Context Caching

System context is cached for 5 seconds to avoid redundant MCP calls:
```python
_system_context_cache: Optional[Dict[str, Any]]
_context_cache_time: Optional[datetime]
_context_cache_ttl: int = 5  # seconds
```

### Processing Lock

Prevents concurrent processing of multiple requests:
```python
async with self.processing_lock:
    await self._process_user_input(text)
```

### TTS Worker Thread

Separate thread for TTS to avoid blocking event loop:
```python
tts_worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
```

### Windows Search Index

Uses Windows Search Index for instant file search instead of recursive scanning:
```python
# 10x-100x faster than os.walk()
conn = win32com.client.Dispatch("ADODB.Connection")
conn.Open("Provider=Search.CollatorDSO;...")
```

## Security Considerations

### Safety Checks

**Command Execution**:
```python
dangerous_keywords = ["rm -rf", "del /f", "format", "shutdown"]
if any(keyword in command.lower() for keyword in dangerous_keywords):
    return {"success": False, "message": "Cannot execute dangerous command"}
```

**API Key Protection**:
- Stored in `.env` file (gitignored)
- Never logged or exposed to UI
- Loaded via environment variables

### Privacy Controls

- Optional conversation storage
- Configurable retention period (default: 30 days)
- Local-only data storage
- No telemetry unless enabled
- Data export/clear functionality

## Error Handling

### Graceful Degradation

1. **Agent Failure** → Fallback to LLM
2. **LLM Failure** → Fallback to rule-based processing
3. **Voice Recognition Failure** → Timeout notification
4. **WebSocket Disconnect** → Automatic reconnection

### Error States

- Errors transition to ERROR state
- Auto-return to IDLE after 2 seconds
- User notification via UI
- Detailed logging for debugging

## Logging

**Library**: loguru

**Log Levels**:
- DEBUG: Detailed execution traces
- INFO: General operations
- SUCCESS: Successful completions
- WARNING: Non-critical issues
- ERROR: Failures with stack traces

**Log Location**: `data/logs/`

## Future Architecture Enhancements

### Planned Improvements

1. **Plugin System**
   - Hot-loading of custom agents
   - Plugin marketplace
   - Sandboxed execution

2. **Local AI Fallback**
   - Ollama integration
   - Offline operation
   - Privacy-first mode

3. **Multi-Agent Workflows**
   - Parallel agent execution
   - Agent collaboration
   - Result aggregation

4. **Advanced Memory**
   - Vector embeddings
   - Semantic search
   - Long-term learning

5. **Cross-Platform Support**
   - macOS agent implementations
   - Linux compatibility
   - Platform-specific optimizations
