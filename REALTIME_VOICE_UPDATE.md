# Realtime Voice Implementation Update

## Changes Made

### 1. **Audio Queue Architecture**
- Added `audio_in_queue` for incoming audio from Gemini (playback queue)
- Added `out_queue` for outgoing audio to Gemini (send queue with maxsize=5)
- Separated audio capture, sending, receiving, and playback into distinct loops

### 2. **Configuration Updates**
- Changed `_get_session_config()` to return `types.LiveConnectConfig` object instead of dict
- Added proper `speech_config` with voice configuration (Leda voice)
- Simplified configuration - removed tools temporarily for testing
- Chunk size increased from 512 to 1024 to match sample code

### 3. **Audio Stream Initialization**
- Updated `start_audio_streams()` to use `asyncio.to_thread()` for PyAudio calls
- Added explicit default input device selection via `get_default_input_device_info()`
- Removed manual stream start/stop calls (PyAudio handles this)

### 4. **Streaming Loop Refactor**
Replaced complex single loops with four specialized loops:

#### `_listen_audio()` (formerly part of `_send_audio_loop`)
- Reads audio chunks from microphone
- Queues audio data with mime type for sending
- Uses `asyncio.to_thread()` to avoid blocking

#### `_send_realtime()`
- Dequeues audio data from `out_queue`
- Sends to Gemini session via `session.send(input=msg)`
- Simple queue consumer pattern

#### `_receive_audio_loop()` (simplified)
- Uses turn-based iteration: `turn = self.session.receive()`
- Handles audio data by queuing to `audio_in_queue`
- Handles text responses via callback
- Clears audio queue on turn complete (for interruption support)

#### `_play_audio_loop()` (new)
- Dequeues audio from `audio_in_queue`
- Plays to speakers via `asyncio.to_thread()`
- Separate from receive loop for better performance

### 5. **Session Management**
- Updated `start_session()` to initialize queues before starting tasks
- Added `http_options={"api_version": "v1beta"}` to client initialization
- Removed initial greeting send (not needed)
- Start all four tasks concurrently
- Updated `stop_session()` to cancel `play_task`

### 6. **Model Configuration**
- Using `models/gemini-2.5-flash-native-audio-preview-09-2025`
- Proper model path with `models/` prefix

## Key Improvements

1. **Better Separation of Concerns**: Each loop has one responsibility
2. **Proper Queue Management**: Prevents blocking and allows interruptions
3. **Turn-Based Receive**: Matches Gemini Live API's actual behavior
4. **Thread Safety**: All PyAudio calls wrapped in `asyncio.to_thread()`
5. **Simpler Error Handling**: Less complex state management

## Testing

Run the dependency test:
```bash
python test_realtime.py
```

Start PRISM and toggle realtime voice mode from the UI to test the implementation.

## Known Limitations

- Tools/function calling temporarily removed from config (add back after basic audio works)
- No user speech transcription callback yet (can be added back)
- No function call handling in receive loop (can be added back)

## Next Steps

1. Test basic audio streaming works
2. Re-add tools configuration once audio is stable
3. Add back function call handling in receive loop
4. Add user speech transcription handling
5. Test interruption behavior (VAD)
