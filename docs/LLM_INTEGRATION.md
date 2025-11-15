# PRISM LLM Integration Documentation

## Overview

PRISM uses Google Gemini as its primary Large Language Model for natural language understanding, intent parsing, and response generation. The system is designed with a hybrid approach: agents handle routine tasks independently, while the LLM provides complex reasoning and natural language capabilities.

## Supported LLM Providers

### Google Gemini (Primary)

**Current Model**: `gemini-2.5-flash` (October 2025)

**Why Gemini**:
- **Free Tier**: 250 requests/day with generous rate limits
- **Fast**: Optimized for low-latency responses
- **Large Context**: 1M token context window
- **Multimodal**: Text, audio, images, video support
- **Safety**: Configurable safety settings
- **Quality**: High-quality responses comparable to GPT-4

**Alternative Models**:
- `gemini-2.5-flash` - Recommended (fastest, best balance)
- `gemini-2.0-flash` - Slightly older, still excellent
- `gemini-2.0-flash-lite` - Lighter version for simple tasks

### Configuration

```env
# .env file
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## AI Engine Architecture

### Core Components

```python
class AIEngine:
    """
    Central AI engine for:
    - Natural language understanding
    - Response generation
    - Action extraction
    - Intent parsing
    """
    
    def __init__(self):
        self.model = None
        self.provider = "gemini"
        self.system_prompt = "..."  # PRISM personality
```

### Initialization

```python
async def initialize(self):
    """Initialize Gemini with safety settings"""
    genai.configure(api_key=config.ai.gemini_api_key)
    
    # Disable safety filters for assistant use
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    self.model = genai.GenerativeModel(
        model_name=config.ai.model,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 2048,
        },
        safety_settings=safety_settings
    )
```

## System Prompt Design

### PRISM Personality

The system prompt defines PRISM's behavior, capabilities, and response format:

```python
system_prompt = """You are PRISM (Personal Response Interface for System Management), 
my personal AI assistant. I am here to help you with:

1. **System Control**: Opening/closing applications, managing files, executing commands
2. **UI Automation**: Controlling applications via keyboard/mouse, clicking buttons, filling forms
3. **Information Retrieval**: Answering questions, searching the web, providing knowledge
4. **Productivity**: Creating files, organizing tasks, managing workflows
5. **System Monitoring**: RAM usage, running processes, system information
6. **Natural Conversation**: Engaging in helpful, friendly dialogue

**My Personality**: I am your personal assistant - helpful, efficient, and natural. 
I respond like a capable assistant, not a system. I speak directly and personally to you.

**IMPORTANT**: Never mention technical details like confidence scores, system processes, 
or implementation details. Just respond naturally and get things done.
"""
```

### Action Format

PRISM uses a special ACTION tag format for system operations:

```python
"""
**Action Format** (required for system actions):
ACTION: {"type": "action_type", "parameters": {...}}

Available actions:
- open_application: {"name": "app_name"} 
- close_application: {"name": "app_name"}
- open_file: {"path": "file_path"}
- search_files: {"query": "search_term", "location": "directory"}
- create_file: {"path": "file_path", "content": "file_content"}
- web_search: {"query": "search_query"}
- system_command: {"command": "command_to_execute"}
- get_memory_info: {} (get RAM usage)
- mcp_focus_window: {"title": "window_title"}
- mcp_hotkey: {"keys": "ctrl+n"}
- mcp_type_text: {"text": "text to type"}
- mcp_press_key: {"key": "enter"}
- mcp_click: {"x": 100, "y": 200}
"""
```

### Example Responses

**Simple Application Opening**:
```
User: "Open notepad"
Assistant: "I'll open Notepad for you right away.
ACTION: {"type": "open_application", "parameters": {"name": "notepad"}}"
```

**Complex UI Automation**:
```
User: "send message to John on whatsapp saying hello"
Assistant: "I'll send that message to John on WhatsApp.
ACTION: {"type": "open_application", "parameters": {"name": "whatsapp"}}
ACTION: {"type": "mcp_focus_window", "parameters": {"title": "whatsapp"}}
ACTION: {"type": "mcp_hotkey", "parameters": {"keys": "ctrl+f"}}
ACTION: {"type": "mcp_type_text", "parameters": {"text": "John"}}
ACTION: {"type": "mcp_press_key", "parameters": {"key": "down"}}
ACTION: {"type": "mcp_press_key", "parameters": {"key": "enter"}}
ACTION: {"type": "mcp_type_text", "parameters": {"text": "hello"}}
ACTION: {"type": "mcp_press_key", "parameters": {"key": "enter"}}

Message sent to John."
```

## Processing Pipeline

### 1. Input Processing

```python
async def process_input(
    self,
    user_input: str,
    conversation_history: List[Dict[str, str]] = None,
    system_context: Dict[str, Any] = None
) -> AIResponse:
    """
    Main processing pipeline:
    1. Build context (system state, conversation history)
    2. Call Gemini API
    3. Extract actions from response
    4. Return structured AIResponse
    """
```

### 2. Context Building

```python
def _build_context(self, system_context: Dict) -> str:
    """
    Build context string from system information:
    - Current directory
    - Running applications
    - System context (if available)
    - Recent conversation
    """
    context_parts = ["Current system context:"]
    
    if "current_directory" in system_context:
        context_parts.append(f"Working directory: {system_context['current_directory']}")
    
    if "running_applications" in system_context:
        apps = system_context["running_applications"]
        context_parts.append(f"Running applications: {', '.join(apps[:5])}")
    
    return "\n".join(context_parts)
```

### 3. Gemini API Call

```python
async def _process_gemini(
    self,
    user_input: str,
    conversation_history: List[Dict],
    context: str
) -> AIResponse:
    """Call Gemini with full context"""
    
    # Build full prompt
    full_prompt = f"{self.system_prompt}\n\n{context}\n\n"
    
    # Add conversation history (last 10 messages)
    if conversation_history:
        full_prompt += "Previous conversation:\n"
        for msg in conversation_history[-10:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            full_prompt += f"{role.capitalize()}: {content}\n"
    
    # Add current input
    full_prompt += f"User: {user_input}\nAssistant:"
    
    # Call Gemini API (async)
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: self.model.generate_content(full_prompt)
    )
    
    return AIResponse(text=response.text)
```

### 4. Action Extraction

```python
def _extract_actions(self, response: AIResponse) -> AIResponse:
    """
    Extract ACTION tags from response text:
    1. Find all ACTION: {...} patterns
    2. Parse JSON objects
    3. Remove ACTION tags from text
    4. Return cleaned response with actions list
    """
    
    action_keyword = "ACTION:"
    decoder = json.JSONDecoder()
    blocks_to_remove = []
    
    # Find all ACTION blocks
    search_start = 0
    while True:
        idx = response.text.find(action_keyword, search_start)
        if idx == -1:
            break
        
        # Find JSON object
        brace_idx = response.text.find('{', idx)
        substring = response.text[brace_idx:]
        
        try:
            action_obj, end_pos = decoder.raw_decode(substring)
            response.requires_action = True
            response.actions.append(action_obj)
            blocks_to_remove.append((idx, brace_idx + end_pos))
            search_start = brace_idx + end_pos
        except json.JSONDecodeError:
            search_start = brace_idx + 1
    
    # Remove ACTION blocks from text
    for start_idx, end_idx in reversed(blocks_to_remove):
        response.text = response.text[:start_idx] + response.text[end_idx:]
    
    response.text = response.text.strip()
    return response
```

## Intent Parsing for Agents

### Purpose

Parse user input into structured intent for agent routing, avoiding full LLM processing for simple tasks.

### Intent Parsing Prompt

```python
intent_prompt = """You are PRISM's intent parser. Analyze the user's request and extract structured information.

User request: "{user_input}"

Analyze this request and respond with a JSON object containing:
1. "agent_type": Which agent should handle this (file_management, web_operations, productivity, system_control, or conversational)
2. "task_type": The specific task (e.g., "search_files", "organize_downloads", "web_search", "open_app", etc.)
3. "parameters": A dictionary of extracted parameters relevant to the task
4. "confidence": Your confidence level (0.0 to 1.0)

For file searches, extract:
- search_term: What to search for (keywords only, not full sentence)
- location: Where to search (e.g., "downloads", "documents", "desktop", or null for all)
- file_type: Type of file if mentioned (e.g., "video", "document", "image", or null)

Examples:

User: "search for coolie movie in my downloads folder"
Response: {
  "agent_type": "file_management",
  "task_type": "search_files",
  "parameters": {
    "search_term": "coolie",
    "location": "downloads",
    "file_type": "video"
  },
  "confidence": 0.95
}

User: "open og movie from downloads"
Response: {
  "agent_type": "file_management",
  "task_type": "open_file",
  "parameters": {
    "search_term": "og",
    "location": "downloads",
    "file_type": "video"
  },
  "confidence": 0.98
}

Now analyze the user's request and respond ONLY with the JSON object, no other text:
"""
```

### Intent Parsing Flow

```python
async def parse_user_intent(self, user_input: str) -> Dict[str, Any]:
    """
    Parse user input to structured intent:
    1. Build intent parsing prompt
    2. Call Gemini API
    3. Extract JSON from response
    4. Return structured intent
    5. Fallback to keyword-based parsing if LLM fails
    """
    
    try:
        # Call Gemini
        response = await self.model.generate_content(intent_prompt)
        response_text = response.text.strip()
        
        # Extract JSON (handle markdown code blocks)
        if "```json" in response_text:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        # Parse JSON
        intent_data = json.loads(response_text)
        return intent_data
        
    except Exception as e:
        logger.error(f"Intent parsing failed: {e}")
        # Fallback to keyword-based parsing
        return self._fallback_intent_parsing(user_input)
```

### Fallback Intent Parsing

```python
def _fallback_intent_parsing(self, user_input: str) -> Dict[str, Any]:
    """
    Keyword-based intent parsing when LLM fails:
    - Pattern matching for common tasks
    - Keyword extraction
    - Confidence scoring based on matches
    """
    
    user_lower = user_input.lower()
    
    # File search pattern
    if 'search' in user_lower or 'find' in user_lower:
        # Extract search term, location, file type
        return {
            'agent_type': 'file_management',
            'task_type': 'search_files',
            'parameters': {...},
            'confidence': 0.7
        }
    
    # Web search pattern
    if 'search' in user_lower and ('web' in user_lower or 'google' in user_lower):
        return {
            'agent_type': 'web_operations',
            'task_type': 'web_search',
            'parameters': {'query': query},
            'confidence': 0.8
        }
```

## Response Generation

### AIResponse Structure

```python
@dataclass
class AIResponse:
    """Structured AI response"""
    text: str                          # Human-readable response
    requires_action: bool = False      # Does it need system actions?
    actions: List[Dict] = []           # List of actions to execute
    confidence: float = 1.0            # Confidence in response
```

### Response Flow

```
1. User Input
   ↓
2. Build Context (system state, history)
   ↓
3. Call Gemini API
   ↓
4. Extract Actions from response
   ↓
5. Clean response text (remove ACTION tags)
   ↓
6. Return AIResponse
   ↓
7. Coordinator executes actions
   ↓
8. Deliver response to user
```

## Conversation Management

### Context Window

Gemini 2.5 Flash supports 1M tokens, but PRISM uses last 10 messages for efficiency:

```python
# Add conversation history (last 10 messages)
for msg in conversation_history[-10:]:
    role = msg.get('role', 'user')
    content = msg.get('content', '')
    full_prompt += f"{role.capitalize()}: {content}\n"
```

### Context Trimming

```python
def _trim_conversation_context(self):
    """Keep conversation context manageable"""
    max_messages = 20
    if len(self.conversation_context) > max_messages:
        # Keep first message (system) and last 19
        self.conversation_context = [
            self.conversation_context[0]
        ] + self.conversation_context[-(max_messages-1):]
```

### Memory Integration

```python
# Store in memory system
if config.privacy.store_conversations:
    await self.memory.store_interaction({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat(),
        "input_method": input_method
    })
```

## Rate Limiting

### Gemini Free Tier Limits

- **Requests per day**: 250
- **Requests per minute**: 15
- **Tokens per minute**: 1M input, 32K output

### Rate Limit Handling

```python
try:
    response = await self.model.generate_content(prompt)
except Exception as e:
    if "429" in str(e) or "quota" in str(e).lower():
        # Rate limit exceeded
        return AIResponse(
            text="I've reached my rate limit. Please try again in a moment.",
            requires_action=False
        )
    else:
        # Other error
        raise
```

### Optimization Strategies

1. **Agent-First Approach** - Use agents for routine tasks, skip LLM
2. **Intent Caching** - Cache common intent patterns
3. **Batch Requests** - Combine multiple queries when possible
4. **Context Pruning** - Only send relevant context

## Error Handling

### API Errors

```python
try:
    response = await self._process_gemini(user_input, history, context)
except Exception as e:
    logger.error(f"Gemini API error: {e}")
    # Fallback to rule-based processing
    return await self._process_fallback(user_input)
```

### Safety Filter Blocks

```python
try:
    text = response.text
except Exception as e:
    # Response blocked by safety filters
    if hasattr(response, 'prompt_feedback'):
        logger.error(f"Response blocked: {response.prompt_feedback}")
    
    # Use fallback response
    text = "I couldn't process that request. Could you rephrase it?"
```

### Fallback Processing

```python
async def _process_fallback(self, user_input: str) -> AIResponse:
    """
    Rule-based processing when LLM unavailable:
    - Pattern matching for common commands
    - Keyword extraction
    - Simple action generation
    """
    
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ["open", "launch", "start"]):
        app_name = user_input_lower.split("open")[-1].strip()
        return AIResponse(
            text=f"Opening {app_name}...",
            requires_action=True,
            actions=[{
                "type": "open_application",
                "parameters": {"name": app_name}
            }]
        )
```

## Gemini Live API Integration

### Real-Time Voice Streaming

PRISM supports Gemini Live API for bidirectional voice streaming:

```python
class LiveVoiceSession:
    """
    Manages live voice session with Gemini 2.0 Flash
    - 24kHz mono audio
    - Bidirectional streaming
    - Real-time responses
    """
    
    async def start(self, system_instruction: str):
        """Start live session"""
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"  # Natural voice
                    )
                )
            )
        )
        
        async with self.client.aio.live.connect(model=self.model, config=config) as session:
            # Process audio streams
            await self._process_audio(session)
```

### Audio Processing

```python
async def _process_input_audio(self):
    """Capture and send audio to Gemini"""
    while self.is_active:
        # Read from microphone
        audio_data = self.input_stream.read(self.chunk_size)
        
        # Send to Gemini
        await session.send_realtime_input(
            audio=types.Blob(
                data=audio_data,
                mime_type=f"audio/pcm;rate={self.sample_rate}"
            )
        )

async def _process_output_audio(self):
    """Receive and play audio from Gemini"""
    async for response in session.receive():
        if response.server_content.model_turn:
            for part in response.server_content.model_turn.parts:
                if part.inline_data and part.inline_data.mime_type.startswith('audio/'):
                    # Play through speakers
                    self.output_stream.write(part.inline_data.data)
```

## Performance Optimization

### Async Execution

```python
# Run LLM call in executor to avoid blocking
response = await asyncio.get_event_loop().run_in_executor(
    None,
    lambda: self.model.generate_content(full_prompt)
)
```

### Context Caching

```python
# Cache system context for 5 seconds
if self._system_context_cache and cache_age < 5:
    return self._system_context_cache
```

### Parallel Processing

```python
# Process multiple intents in parallel
tasks = [
    ai_engine.parse_user_intent(query1),
    ai_engine.parse_user_intent(query2)
]
results = await asyncio.gather(*tasks)
```

## Testing

### Unit Tests

```python
@pytest.mark.asyncio
async def test_action_extraction():
    engine = AIEngine()
    await engine.initialize()
    
    response = AIResponse(
        text='Opening Chrome. ACTION: {"type": "open_application", "parameters": {"name": "chrome"}}'
    )
    
    result = engine._extract_actions(response)
    
    assert result.requires_action
    assert len(result.actions) == 1
    assert result.actions[0]['type'] == 'open_application'
    assert 'ACTION:' not in result.text
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_pipeline():
    engine = AIEngine()
    await engine.initialize()
    
    response = await engine.process_input(
        user_input="Open notepad",
        conversation_history=[],
        system_context={}
    )
    
    assert response.requires_action
    assert len(response.actions) > 0
```

## Best Practices

### 1. Clear System Prompts

Define clear personality and capabilities:
```python
system_prompt = """
You are PRISM, a helpful assistant.
Your capabilities: [list]
Your personality: [description]
Response format: [format]
"""
```

### 2. Structured Actions

Use consistent action format:
```python
ACTION: {"type": "action_type", "parameters": {...}}
```

### 3. Error Recovery

Always have fallback mechanisms:
```python
try:
    response = await llm_call()
except:
    response = fallback_response()
```

### 4. Context Management

Keep context relevant and sized appropriately:
```python
# Last 10 messages only
history = conversation_history[-10:]
```

### 5. Rate Limit Awareness

Monitor and handle rate limits gracefully:
```python
if rate_limit_exceeded:
    return "Please wait a moment..."
```

## Future Enhancements

### Planned Features

1. **Multi-Modal Input** - Images, audio, video processing
2. **Function Calling** - Native Gemini function calling support
3. **Streaming Responses** - Real-time response streaming
4. **Local LLM Fallback** - Ollama integration for offline mode
5. **Fine-Tuning** - Custom model training for PRISM-specific tasks
6. **Prompt Optimization** - A/B testing for better prompts
7. **Context Compression** - Intelligent context summarization
8. **Multi-Turn Planning** - Complex multi-step task planning
