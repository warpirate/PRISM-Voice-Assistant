# Vision Agent System - Autonomous UI Interaction

## Overview

PRISM now includes a **VisionAgent** that enables true autonomous UI interaction, similar to Perplexity's Comet. Instead of relying on hardcoded keyboard shortcuts, PRISM can now:

1. **See the screen** using computer vision
2. **Understand UI elements** (buttons, text fields, search boxes)
3. **Click precisely** on the correct elements
4. **Verify actions** by checking the screen state
5. **Adapt** to different UI layouts

## Architecture

```
User Request
    ↓
MessagingAgent (task-specific logic)
    ↓
VisionAgent (computer vision)
    ↓
Gemini 2.0 Flash (vision model)
    ↓
Screenshot Analysis → Element Detection → Coordinates
    ↓
MCP Client (mouse/keyboard control)
    ↓
Action Execution
```

## Key Components

### 1. VisionAgent (`backend/agents/vision_agent.py`)

**Capabilities:**
- `take_screenshot()` - Capture current screen state
- `find_ui_element(description)` - Locate UI elements by natural language
- `click_element(description)` - Find and click elements
- `verify_ui_state(expected)` - Verify action success
- `navigate_to_element(target, steps)` - Multi-step navigation

**How it works:**
1. Takes screenshot using `mss` library
2. Sends image + prompt to Gemini 2.0 Flash vision model
3. Gemini analyzes image and returns:
   - Element location (x, y coordinates)
   - Element type (button, text_field, etc.)
   - Confidence score
   - Description of what it found

**Example:**
```python
# Find message input field
result = await vision_agent.execute(
    "find_ui_element",
    {"element_description": "message input field at bottom of chat"}
)

# Returns:
{
    "found": true,
    "x": 450,
    "y": 680,
    "confidence": 0.95,
    "type": "text_field",
    "description": "Message input box with placeholder 'Type a message'"
}
```

### 2. MessagingAgent (`backend/agents/messaging_agent.py`)

**Purpose:** Autonomous messaging across platforms (WhatsApp, Telegram, Slack, etc.)

**Key Features:**
- Platform-specific knowledge (search field vs message field)
- Visual UI understanding (no hardcoded shortcuts)
- Message delivery verification
- Fallback to keyboard shortcuts if vision unavailable

**Workflow for sending a message:**
1. **Locate search field** using vision
2. **Click** on search field
3. **Type** recipient name
4. **Select** contact from results
5. **Locate message field** (different from search!)
6. **Click** message field
7. **Type** message
8. **Send** message
9. **Verify** message sent successfully

### 3. Integration with Coordinator

The coordinator routes messaging tasks to MessagingAgent, which uses VisionAgent for UI understanding:

```python
# User: "send message to John on WhatsApp saying hello"
# ↓
# Coordinator parses intent → MessagingAgent
# ↓
# MessagingAgent uses VisionAgent to:
#   1. Find search field
#   2. Find message field
#   3. Verify message sent
```

## Comparison: Old vs New Approach

### Old Approach (Keyboard Shortcuts)
```python
# Hardcoded shortcuts - breaks if UI changes
1. Press Ctrl+F (open search)
2. Type "John"
3. Press Enter
4. Type "Hello"  # ❌ Goes in search field!
5. Press Enter
```

**Problems:**
- Types in wrong field
- Breaks if shortcuts change
- No verification
- Not adaptive

### New Approach (Vision-Based)
```python
# Vision-based - adapts to UI
1. Vision: Find "search field"
2. Click at (x, y)
3. Type "John"
4. Press Enter
5. Vision: Find "message input field"  # ✅ Correct field!
6. Click at (x, y)
7. Type "Hello"
8. Press Enter
9. Vision: Verify "message sent"
```

**Benefits:**
- ✅ Clicks correct elements
- ✅ Adapts to UI changes
- ✅ Verifies success
- ✅ Works across platforms

## Platform Support

### WhatsApp
- Search field: "search or start new chat"
- Message field: "type a message"
- Send button: "paper plane icon"

### Telegram
- Search field: "search"
- Message field: "write a message"

### Slack
- Search field: "jump to"
- Message field: "message"

### Discord
- Search field: "find or start a conversation"
- Message field: "message @channel"

## Setup Requirements

### 1. Install Dependencies
```bash
pip install Pillow mss opencv-python
```

### 2. Configure Gemini API
The VisionAgent uses Gemini 2.0 Flash with vision capabilities. Ensure your API key is set in `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Register Agents
Add to `coordinator.py`:
```python
from backend.agents.vision_agent import VisionAgent
from backend.agents.messaging_agent import MessagingAgent

# Initialize
vision_agent = VisionAgent(gemini_api_key=config.ai.gemini_api_key)
messaging_agent = MessagingAgent(
    vision_agent=vision_agent,
    mcp_client=self.mcp_client
)

# Register
await self.agent_registry.register(vision_agent)
await self.agent_registry.register(messaging_agent)
```

## Usage Examples

### Example 1: Send WhatsApp Message
```
User: "send message to Sarah on WhatsApp saying I'll be late"

PRISM:
1. Opens WhatsApp (if not open)
2. Uses vision to find search field
3. Clicks search field
4. Types "Sarah"
5. Selects contact
6. Uses vision to find message field
7. Clicks message field
8. Types "I'll be late"
9. Sends message
10. Verifies message sent
```

### Example 2: Multi-Platform Messaging
```
User: "message John on Slack and tell him the meeting is at 3pm"

PRISM:
1. Opens Slack
2. Adapts to Slack's UI layout
3. Finds Slack's search field (different from WhatsApp)
4. Locates Slack's message field
5. Sends message
6. Verifies delivery
```

### Example 3: Complex Navigation
```
User: "go to settings in WhatsApp and enable dark mode"

PRISM:
1. Vision: Find "three dots menu"
2. Click menu
3. Vision: Find "Settings" option
4. Click Settings
5. Vision: Find "Theme" option
6. Click Theme
7. Vision: Find "Dark" option
8. Click Dark
9. Verify dark mode enabled
```

## Advantages Over Comet

While inspired by Comet, PRISM's vision system has unique advantages:

1. **Local-First**: All processing happens on your machine
2. **Privacy**: No data sent to external services (except Gemini API for vision)
3. **Customizable**: Add your own platform patterns
4. **Open Source**: Full control over agent behavior
5. **Windows-Native**: Deep integration with Windows UI Automation

## Future Enhancements

### Phase 1 (Current)
- ✅ VisionAgent with Gemini vision
- ✅ MessagingAgent for WhatsApp/Telegram
- ✅ Screenshot capture and analysis
- ✅ Element detection and clicking

### Phase 2 (Next)
- [ ] OCR for reading text on screen
- [ ] Form filling automation
- [ ] Browser automation (YouTube, Gmail, etc.)
- [ ] Multi-monitor support
- [ ] Screenshot caching for performance

### Phase 3 (Advanced)
- [ ] Local vision models (offline operation)
- [ ] UI element tracking (remember positions)
- [ ] Gesture recognition
- [ ] Voice-guided UI navigation
- [ ] Screen recording for debugging

### Phase 4 (Intelligence)
- [ ] Learn from user corrections
- [ ] Build UI maps automatically
- [ ] Predict next actions
- [ ] Handle error states gracefully

## Performance Considerations

### Speed
- Screenshot: ~50ms
- Gemini vision analysis: ~2-3 seconds
- Click execution: ~100ms
- Total per action: ~3-4 seconds

### Optimization Strategies
1. **Cache element positions** for repeated actions
2. **Batch vision requests** when possible
3. **Use lower resolution** for faster analysis
4. **Skip verification** for non-critical actions
5. **Fallback to shortcuts** for known patterns

### Cost
- Gemini 2.0 Flash: Free tier includes vision
- ~1 vision request per UI element
- Typical message send: 3-4 vision requests
- Daily limit: ~250 requests (Gemini free tier)

## Troubleshooting

### Vision agent not finding elements
- **Check screenshot quality**: Ensure high DPI displays are handled
- **Adjust descriptions**: Be more specific ("blue send button" vs "send button")
- **Verify Gemini API**: Check API key and quota

### Clicking wrong coordinates
- **Monitor scaling**: Ensure coordinates account for DPI scaling
- **Multiple monitors**: Specify which monitor to use
- **Window position**: Ensure target window is visible and focused

### Slow performance
- **Reduce screenshot resolution**: Use lower quality for faster analysis
- **Cache results**: Remember element positions for repeated actions
- **Use keyboard shortcuts**: Fallback for known patterns

## Security & Privacy

### Data Handling
- Screenshots are **temporary** (not saved to disk by default)
- Only sent to Gemini API for analysis
- No conversation data included in vision requests
- Element positions cached locally only

### API Security
- Gemini API key stored in `.env` (never committed)
- HTTPS for all API requests
- No third-party services beyond Gemini

### Permissions
- Screen capture: Required for vision
- Mouse/keyboard control: Required for clicking
- No network access beyond API calls

## Conclusion

The VisionAgent system transforms PRISM from a **command-based assistant** to a **truly autonomous agent** that can:

- **See** what's on screen
- **Understand** UI elements
- **Act** precisely and reliably
- **Verify** success
- **Adapt** to changes

This brings PRISM to parity with systems like Comet, while maintaining privacy and local-first principles.

---

**Next Steps:**
1. Install vision dependencies: `pip install -r requirements.txt`
2. Test VisionAgent: `python -m backend.agents.vision_agent`
3. Try messaging: "send message to [contact] on WhatsApp"
4. Monitor logs for vision analysis results
5. Provide feedback for improvements
