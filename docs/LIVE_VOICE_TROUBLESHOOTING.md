# Live Voice Troubleshooting Guide

## Current Issue: No Audio Response from Gemini

### Problem
Live Voice mode connects successfully but the agent doesn't speak or respond with audio.

### Root Causes

1. **Audio Format Mismatch**: The code expects audio in `model_turn.parts[].inline_data` but Gemini Live API may send it in different formats
2. **Response Structure**: The response structure from Gemini Live API varies and the code wasn't handling all cases
3. **Debugging Needed**: Insufficient logging to see what's actually being received

## Python vs JavaScript for Live Audio

### Recommendation: **JavaScript/WebSocket is better for Gemini Live API**

#### Why JavaScript is Better:

1. **Official Support**: Google's Live API examples use JavaScript/WebSocket
2. **Browser Native**: WebRTC and Web Audio API are native to browsers
3. **Lower Latency**: Direct browser-to-API communication without Python intermediary
4. **Better Audio Handling**: Web Audio API is designed for real-time audio
5. **Simpler Architecture**: No need for PyAudio, less audio format conversion

#### Current Python Approach Issues:

1. **PyAudio Complexity**: Requires native audio drivers, platform-specific
2. **Format Conversion**: Multiple conversions (mic → PyAudio → Python → Gemini → Python → PyAudio → speakers)
3. **Latency**: Additional hops through Python backend
4. **Debugging Difficulty**: Harder to inspect WebSocket frames in Python
5. **Library Maturity**: Python Gemini SDK for Live API is newer, less examples

## Recommended Architecture Change

### Current (Python-based):
```
Microphone → PyAudio → Python → WebSocket → Gemini Live API
                                                    ↓
Speakers ← PyAudio ← Python ← WebSocket ← Audio Response
```

### Recommended (JavaScript-based):
```
Microphone → Web Audio API → WebSocket → Gemini Live API
                                              ↓
Speakers ← Web Audio API ← WebSocket ← Audio Response
```

## Implementation Options

### Option 1: Pure JavaScript (Recommended)

**Pros**:
- Lowest latency
- Native browser support
- Simpler debugging
- Official examples available
- No Python audio dependencies

**Cons**:
- Requires rewriting live voice in JavaScript
- Need to integrate with Electron renderer

**Implementation**:
```javascript
// In renderer.js or separate live-voice.js
class LiveVoiceClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.ws = null;
        this.audioContext = new AudioContext({ sampleRate: 24000 });
        this.mediaStream = null;
    }
    
    async connect() {
        // Get microphone access
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
            audio: { 
                sampleRate: 24000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        // Connect to Gemini Live API
        this.ws = new WebSocket(
            `wss://generativelanguage.googleapis.com/ws/v1beta/models/gemini-2.0-flash-exp:streamGenerateContent?key=${this.apiKey}`
        );
        
        this.ws.onopen = () => this.onConnect();
        this.ws.onmessage = (event) => this.onMessage(event);
        this.ws.onerror = (error) => this.onError(error);
    }
    
    onConnect() {
        // Send setup message
        this.ws.send(JSON.stringify({
            setup: {
                model: "models/gemini-2.0-flash-exp",
                generation_config: {
                    response_modalities: ["AUDIO"]
                }
            }
        }));
        
        // Start sending audio
        this.startAudioStream();
    }
    
    startAudioStream() {
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        const processor = this.audioContext.createScriptProcessor(2400, 1, 1);
        
        processor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = this.float32ToPCM16(inputData);
            
            // Send to Gemini
            this.ws.send(JSON.stringify({
                realtime_input: {
                    media_chunks: [{
                        data: this.arrayBufferToBase64(pcmData),
                        mime_type: "audio/pcm"
                    }]
                }
            }));
        };
        
        source.connect(processor);
        processor.connect(this.audioContext.destination);
    }
    
    onMessage(event) {
        const response = JSON.parse(event.data);
        
        // Handle audio response
        if (response.server_content?.model_turn?.parts) {
            for (const part of response.server_content.model_turn.parts) {
                if (part.inline_data?.mime_type?.startsWith('audio/')) {
                    this.playAudio(part.inline_data.data);
                }
            }
        }
    }
    
    playAudio(base64Audio) {
        const audioData = this.base64ToArrayBuffer(base64Audio);
        this.audioContext.decodeAudioData(audioData, (buffer) => {
            const source = this.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(this.audioContext.destination);
            source.start();
        });
    }
    
    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return pcm16.buffer;
    }
    
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
    
    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }
    
    disconnect() {
        if (this.ws) this.ws.close();
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
    }
}
```

### Option 2: Hybrid (Keep Python, Fix Issues)

**Pros**:
- Minimal changes to existing code
- Keep backend-centric architecture
- Easier to integrate with existing Python agents

**Cons**:
- Still has latency issues
- PyAudio dependency remains
- More complex debugging

**Fixes Applied**:
1. Added alternative audio format handling
2. Added comprehensive logging
3. Added error handling for audio playback
4. Debug response structure

## Testing the Fixes

### 1. Enable Debug Logging

In `.env`:
```env
LOG_LEVEL=DEBUG
```

### 2. Test Live Voice

1. Start PRISM: `npm start`
2. Click Live Voice button
3. Speak something
4. Check logs for:
   - "Received response type: ..."
   - "Received audio chunk: X bytes"
   - "Received direct audio: X bytes"

### 3. Expected Log Output

**Success**:
```
INFO | Live voice session started successfully
DEBUG | Received response type: <class 'google.genai.types.LiveServerMessage'>
DEBUG | Received audio chunk: 4800 bytes
INFO | Response started
```

**Failure**:
```
DEBUG | Received response without server_content
ERROR | Error playing audio: ...
```

## Migration Path to JavaScript

### Phase 1: Proof of Concept (1-2 days)
1. Create `ui/live-voice-client.js`
2. Implement basic WebSocket connection
3. Test audio streaming
4. Verify lower latency

### Phase 2: Integration (2-3 days)
1. Integrate with Electron renderer
2. Update UI controls
3. Handle state management
4. Add error handling

### Phase 3: Polish (1-2 days)
1. Add audio visualization
2. Optimize buffer sizes
3. Add reconnection logic
4. Remove Python live voice code

### Phase 4: Testing (1 day)
1. Test various scenarios
2. Measure latency improvements
3. Verify audio quality
4. Test error recovery

## Immediate Next Steps

1. **Test Current Fixes**: Run with DEBUG logging to see what's being received
2. **Check Audio Format**: Verify Gemini is sending audio in expected format
3. **Consider Migration**: If issues persist, migrate to JavaScript implementation
4. **Reference Implementation**: Check Google's live-api-web-console for working example

## Resources

- [Gemini Live API Docs](https://ai.google.dev/api/live)
- [Google Live API Web Console (JS)](https://github.com/google-gemini/live-api-web-console)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## Conclusion

**For production-quality live voice in PRISM, JavaScript/WebSocket is the better choice.** The current Python implementation can work but requires more debugging and will always have higher latency. Consider migrating to JavaScript for:

- Lower latency (50-100ms improvement)
- Better audio quality
- Simpler debugging
- Official support and examples
- Native browser capabilities
