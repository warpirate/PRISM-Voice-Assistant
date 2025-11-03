# PRISM Workflows Documentation

## User Interaction Workflows

### Voice Activation Workflow

```
1. User says "Prism" OR clicks orb OR presses Ctrl+Space
   ↓
2. Coordinator receives activation signal
   ↓
3. State changes to LISTENING
   ↓
4. UI shows green orb + waveform animation
   ↓
5. Voice Pipeline starts listening (10s timeout)
   ↓
6. User speaks command
   ↓
7. Google Speech Recognition converts to text
   ↓
8. Text sent to Coordinator for processing
   ↓
9. Continue to "Input Processing Workflow"
```

### Text Input Workflow

```
1. User types in text input field
   ↓
2. User presses Enter or clicks Send
   ↓
3. UI displays user message immediately
   ↓
4. Message sent to backend via WebSocket
   ↓
5. Coordinator receives text input
   ↓
6. Continue to "Input Processing Workflow"
```

### Live Voice Mode Workflow

```
1. User clicks Live Voice button
   ↓
2. LiveVoiceManager starts session
   ↓
3. Connect to Gemini Live API (WebSocket)
   ↓
4. Start bidirectional audio streaming
   - Input: Microphone → Gemini
   - Output: Gemini → Speakers
   ↓
5. Continuous conversation (no activation needed)
   ↓
6. User clicks button again to stop
   ↓
7. Session closes gracefully
```

## Core Processing Workflows

### Input Processing Workflow

```
1. Coordinator.process_text_input(text)
   ↓
2. Acquire processing lock (prevent concurrent)
   ↓
3. Store user message in memory (if enabled)
   ↓
4. Add to conversation context
   ↓
5. Send user message to UI
   ↓
6. Try MCP query handling (screen context queries)
   ├─ If handled: Deliver response → IDLE
   └─ If not: Continue
   ↓
7. Try agent execution
   ├─ Parse intent with AI Engine
   ├─ Route to Agent Coordinator
   ├─ Execute with appropriate agent
   ├─ If successful: Deliver response → IDLE
   └─ If failed: Continue
   ↓
8. Fallback to LLM processing
   ├─ Build context (system state, history)
   ├─ Call Gemini API
   ├─ Extract actions from response
   └─ Continue
   ↓
9. Execute actions (if required)
   ↓
10. Deliver response (text + voice)
    ↓
11. Release processing lock
    ↓
12. Return to IDLE state
```

### Agent Execution Workflow

```
1. AI Engine parses user intent
   ├─ Call Gemini with intent parsing prompt
   ├─ Extract structured intent (agent_type, task_type, parameters)
   └─ Return intent_data with confidence score
   ↓
2. Check confidence threshold
   ├─ If < 0.5: Fallback to LLM
   ├─ If conversational: Fallback to LLM
   └─ If good: Continue
   ↓
3. Agent Coordinator receives intent
   ├─ Map agent_type to capability
   ├─ Find agents with capability
   └─ Select first matching agent
   ↓
4. Agent executes task
   ├─ Parse parameters
   ├─ Perform operation
   ├─ Generate response
   └─ Return AgentResponse
   ↓
5. Check response status
   ├─ If SUCCESS: Return to coordinator
   └─ If FAILURE: Fallback to LLM
   ↓
6. Store response in memory
   ↓
7. Deliver response to user
```

### Action Execution Workflow

```
1. AI Response contains actions
   ↓
2. Extract ACTION tags from response text
   ├─ Find "ACTION: {...}" patterns
   ├─ Parse JSON objects
   └─ Remove tags from text
   ↓
3. For each action:
   ├─ Validate action type
   ├─ Get parameters
   ├─ Call SystemControl.execute_action()
   ├─ Wait for completion
   ├─ Add delays for UI sync (if needed)
   ├─ Handle errors
   └─ Notify user (if requested)
   ↓
4. All actions completed
   ↓
5. Return to IDLE
```

## File Operations Workflows

### File Search Workflow

```
1. User: "search for report in documents"
   ↓
2. Intent parsed: {agent_type: file_management, task_type: search_files}
   ↓
3. PersonalFileAgent receives task
   ↓
4. Try Windows Search Index (fast)
   ├─ Build SQL query
   ├─ Execute search
   ├─ If results: Return immediately
   └─ If fails: Continue
   ↓
5. Try DIR command (medium speed)
   ├─ Execute: dir /s /b *report*
   ├─ Parse output
   ├─ If results: Return
   └─ If fails: Continue
   ↓
6. Fallback to Python rglob (slow but reliable)
   ├─ Recursively scan directories
   ├─ Match filenames
   └─ Return results
   ↓
7. Format response
   ├─ List first 10 matches
   ├─ Include file metadata
   └─ Add suggestions
   ↓
8. Return AgentResponse to coordinator
```

### File Opening Workflow

```
1. User: "open coolie movie from downloads"
   ↓
2. Intent: {task_type: open_file, search_term: coolie, location: downloads, file_type: video}
   ↓
3. PersonalFileAgent searches for file
   ├─ Use search workflow
   └─ Get list of matches
   ↓
4. If multiple matches:
   ├─ Sort by modified time (most recent first)
   └─ Select first match
   ↓
5. Open file with OS default application
   ├─ Windows: os.startfile()
   ├─ macOS: subprocess.run(["open", path])
   └─ Linux: subprocess.run(["xdg-open", path])
   ↓
6. Return success response
```

### Downloads Organization Workflow

```
1. User: "organize my downloads"
   ↓
2. PersonalFileAgent.organize_downloads()
   ↓
3. Scan Downloads folder (root level only)
   ↓
4. For each file:
   ├─ Determine category by extension
   ├─ Create category folder if needed
   ├─ Move file to category folder
   ├─ Handle name conflicts (add timestamp)
   └─ Track moved files
   ↓
5. Return summary
   ├─ Count of organized files
   ├─ List of moves (first 10)
   └─ Suggestions
```

## Application Control Workflows

### Application Opening Workflow

```
1. User: "open chrome"
   ↓
2. SystemControl.open_application("chrome")
   ↓
3. Fuzzy match application name
   ├─ Search installed apps database
   ├─ Check aliases
   ├─ Calculate confidence score
   └─ Get best match
   ↓
4. If match found (>60% confidence):
   ├─ Get command/path
   ├─ Execute application
   │   ├─ Try os.startfile()
   │   ├─ Try shutil.which()
   │   ├─ Try System32 path
   │   └─ Fallback to shell execution
   ├─ Wait 1.5s for window to appear
   └─ Return success
   ↓
5. If no match:
   ├─ Get top 5 suggestions
   └─ Return failure with suggestions
```

### UI Automation Workflow

```
1. User: "type hello in notepad"
   ↓
2. AI generates multi-step actions:
   ACTION: {"type": "mcp_focus_window", "parameters": {"title": "notepad"}}
   ACTION: {"type": "mcp_type_text", "parameters": {"text": "hello"}}
   ↓
3. Execute actions sequentially:
   ├─ Focus notepad window (via MCP)
   ├─ Wait 0.3s for focus
   ├─ Type "hello" (via MCP)
   └─ Wait 0.4s for completion
   ↓
4. Return success
```

### WhatsApp Messaging Workflow

```
1. User: "send message to John saying hello"
   ↓
2. AI generates automation sequence:
   ACTION: {"type": "open_application", "parameters": {"name": "whatsapp"}}
   ACTION: {"type": "mcp_focus_window", "parameters": {"title": "whatsapp"}}
   ACTION: {"type": "mcp_hotkey", "parameters": {"keys": "ctrl+f"}}
   ACTION: {"type": "mcp_type_text", "parameters": {"text": "John"}}
   ACTION: {"type": "mcp_press_key", "parameters": {"key": "down"}}
   ACTION: {"type": "mcp_press_key", "parameters": {"key": "enter"}}
   ACTION: {"type": "mcp_type_text", "parameters": {"text": "hello"}}
   ACTION: {"type": "mcp_press_key", "parameters": {"key": "enter"}}
   ↓
3. Execute each action with delays:
   ├─ Open WhatsApp
   ├─ Wait 1.5s
   ├─ Focus window
   ├─ Wait 0.3s
   ├─ Open search (Ctrl+F)
   ├─ Wait 0.4s
   ├─ Type "John"
   ├─ Wait 0.4s
   ├─ Press Down (select contact)
   ├─ Wait 0.3s
   ├─ Press Enter (open chat)
   ├─ Wait 0.4s
   ├─ Type "hello"
   ├─ Wait 0.4s
   ├─ Press Enter (send)
   └─ Wait 0.3s
   ↓
4. Return success
```

## System Workflows

### Startup Workflow

```
1. User runs start.bat
   ↓
2. Electron main process starts
   ├─ Create main window
   ├─ Create system tray
   ├─ Setup WebSocket server (port 9876)
   ├─ Register global hotkeys
   └─ Spawn Python backend process
   ↓
3. Python backend starts
   ├─ Load configuration from .env
   ├─ Initialize logging
   ├─ Create Coordinator
   └─ Start coordinator
   ↓
4. Coordinator initializes subsystems
   ├─ Voice Pipeline (STT, TTS)
   ├─ AI Engine (Gemini)
   ├─ System Control
   ├─ Memory System (SQLite)
   ├─ WebSocket Bridge
   ├─ Agent System
   │   ├─ PersonalFileAgent
   │   ├─ PersonalWebAgent
   │   └─ PersonalProductivityAgent
   └─ MCP Client (Windows automation)
   ↓
5. WebSocket connection established
   ├─ Backend connects to Electron server
   └─ Bidirectional communication ready
   ↓
6. UI shows IDLE state
   ↓
7. System ready for user input
```

### Shutdown Workflow

```
1. User closes window or quits from tray
   ↓
2. Electron sends shutdown signal
   ↓
3. Coordinator.shutdown()
   ├─ Set state to SHUTDOWN
   ├─ Shutdown agents
   │   ├─ Unregister all agents
   │   └─ Cleanup agent resources
   ├─ Shutdown MCP client
   ├─ Shutdown voice pipeline
   │   ├─ Stop TTS worker
   │   └─ Release audio devices
   ├─ Shutdown AI engine
   ├─ Shutdown memory system
   │   └─ Close database connection
   └─ Shutdown WebSocket bridge
   ↓
4. Backend process exits
   ↓
5. Electron main process exits
   ↓
6. Application closed
```

### Error Recovery Workflow

```
1. Error occurs during processing
   ↓
2. Catch exception
   ├─ Log error with stack trace
   ├─ Set state to ERROR
   └─ Notify user
   ↓
3. Attempt recovery
   ├─ If agent error: Fallback to LLM
   ├─ If LLM error: Fallback to rule-based
   ├─ If WebSocket error: Reconnect
   └─ If voice error: Return to text mode
   ↓
4. Wait 2 seconds
   ↓
5. Return to IDLE state
   ↓
6. System ready for next request
```

## Memory & Learning Workflows

### Conversation Storage Workflow

```
1. User sends message
   ↓
2. Store in memory (if enabled)
   ├─ Insert into interactions table
   │   ├─ timestamp
   │   ├─ role (user/assistant)
   │   ├─ content
   │   ├─ input_method (voice/text)
   │   └─ metadata
   └─ Update patterns
       ├─ Extract command keywords
       ├─ Extract application names
       └─ Increment frequency counters
   ↓
3. Assistant responds
   ↓
4. Store assistant message
   ├─ Insert into interactions table
   └─ Link to user message
```

### Pattern Learning Workflow

```
1. User interaction stored
   ↓
2. Extract patterns
   ├─ Command keywords (open, search, create)
   ├─ Application names (chrome, vscode)
   └─ File operations
   ↓
3. Check if pattern exists
   ├─ If exists: Increment frequency
   └─ If new: Create pattern entry
   ↓
4. Update last_seen timestamp
   ↓
5. Patterns used for:
   ├─ Autocomplete suggestions
   ├─ Intent prediction
   └─ Personalization
```

### Data Cleanup Workflow

```
1. System starts or scheduled cleanup
   ↓
2. Check retention policy (default: 30 days)
   ↓
3. Calculate cutoff date
   ↓
4. Delete old interactions
   ├─ WHERE timestamp < cutoff_date
   └─ Log deleted count
   ↓
5. Vacuum database (reclaim space)
```

## UI State Workflows

### State Transition Workflow

```
States: IDLE → LISTENING → PROCESSING → RESPONDING → EXECUTING → IDLE
                                                                    ↓
                                                                  ERROR → IDLE

State Changes:
- IDLE: Blue orb, waiting
- LISTENING: Green orb, waveform animation
- PROCESSING: Orange orb, typing indicator
- RESPONDING: Purple orb, showing response
- EXECUTING: Yellow orb, performing actions
- ERROR: Red orb, error message
```

### Message Display Workflow

```
1. Backend sends message via WebSocket
   ↓
2. Renderer receives message
   ↓
3. Parse message type
   ├─ user_message: Add to conversation (if not duplicate)
   ├─ assistant_message: Add to conversation
   ├─ state_change: Update orb and indicator
   ├─ audio_level: Update waveform
   └─ error: Show error message
   ↓
4. Update UI
   ├─ Add message bubble
   ├─ Format markdown
   ├─ Add timestamp
   └─ Scroll to bottom
   ↓
5. Update conversation history
```

## Best Practices

### Workflow Design Principles

1. **Clear Entry/Exit Points** - Every workflow has defined start and end
2. **Error Handling** - Every step has error recovery
3. **State Management** - State transitions are explicit
4. **Async Operations** - Long operations don't block
5. **User Feedback** - User always knows what's happening
6. **Graceful Degradation** - Fallbacks for every failure
7. **Logging** - All steps logged for debugging
8. **Timeout Handling** - No infinite waits

### Performance Considerations

1. **Parallel Execution** - Independent operations run concurrently
2. **Caching** - Frequently accessed data cached
3. **Lazy Loading** - Resources loaded on demand
4. **Connection Pooling** - Reuse connections
5. **Batch Operations** - Group related operations
