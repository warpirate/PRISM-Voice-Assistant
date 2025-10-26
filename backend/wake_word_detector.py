"""
Simple wake word detector for "Hey PRISM"
Uses audio energy detection and basic pattern matching
"""

import logging
import threading
import time
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("PyAudio not available")
    PYAUDIO_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("Whisper not available")
    WHISPER_AVAILABLE = False


class SimpleWakeWordDetector:
    """
    Simple wake word detector that listens for "Hey PRISM" or "PRISM"
    Uses continuous audio monitoring with Whisper for transcription
    """
    
    def __init__(self, callback=None, wake_phrases=None):
        """
        Initialize wake word detector
        
        Args:
            callback: Function to call when wake word is detected
            wake_phrases: List of phrases to detect (default: ["hey prism", "prism"])
        """
        self.callback = callback
        self.wake_phrases = wake_phrases or ["hey prism", "prism", "hey prison"]
        self.running = False
        self.audio = None
        self.whisper_model = None
        self.listen_thread = None
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.BUFFER_DURATION = 2  # seconds of audio to analyze
        self.ENERGY_THRESHOLD = 500  # Minimum energy to consider as speech
        
        self._initialize()
    
    def _initialize(self):
        """Initialize audio and Whisper"""
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio not available - wake word detection disabled")
            return
        
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available - wake word detection disabled")
            return
        
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            logger.info("PyAudio initialized for wake word detection")
            
            # Load Whisper model (tiny for speed)
            logger.info("Loading Whisper tiny model for wake word detection...")
            self.whisper_model = whisper.load_model("tiny")
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
    
    def start(self):
        """Start listening for wake word"""
        if not self.audio or not self.whisper_model:
            logger.error("Cannot start wake word detector - components not initialized")
            return False
        
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        logger.info(f"Wake word detector started. Listening for: {', '.join(self.wake_phrases)}")
        return True
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        logger.info("Wake word detector stopped")
    
    def _calculate_energy(self, audio_data):
        """Calculate audio energy level"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            return np.sqrt(np.mean(audio_array**2))
        except:
            return 0
    
    def _listen_loop(self):
        """Main listening loop"""
        try:
            # Open audio stream
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            logger.info("🎤 Listening for wake word...")
            logger.info("Say 'Hey PRISM' or 'PRISM' to activate")
            
            # Buffer to store recent audio
            buffer_size = int(self.RATE * self.BUFFER_DURATION / self.CHUNK)
            audio_buffer = deque(maxlen=buffer_size)
            
            silence_counter = 0
            speech_detected = False
            
            while self.running:
                try:
                    # Read audio chunk
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_buffer.append(data)
                    
                    # Calculate energy
                    energy = self._calculate_energy(data)
                    
                    # Detect speech activity
                    if energy > self.ENERGY_THRESHOLD:
                        if not speech_detected:
                            speech_detected = True
                            silence_counter = 0
                    else:
                        if speech_detected:
                            silence_counter += 1
                            
                            # After 0.5 seconds of silence, process the buffer
                            if silence_counter > int(0.5 * self.RATE / self.CHUNK):
                                self._process_audio_buffer(audio_buffer)
                                speech_detected = False
                                silence_counter = 0
                    
                except Exception as e:
                    logger.error(f"Error in listen loop: {e}")
                    time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
    
    def _process_audio_buffer(self, audio_buffer):
        """Process audio buffer to detect wake word"""
        try:
            # Combine buffer into single audio array
            audio_data = b''.join(audio_buffer)
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_array,
                language='en',
                fp16=False,
                task='transcribe'
            )
            
            text = result['text'].strip().lower()
            
            if text:
                logger.debug(f"Detected: '{text}'")
                
                # Check for wake phrases
                for phrase in self.wake_phrases:
                    if phrase in text:
                        logger.info(f"✓ Wake word detected: '{text}'")
                        if self.callback:
                            self.callback()
                        return
            
        except Exception as e:
            logger.error(f"Error processing audio buffer: {e}")
    
    def test_microphone(self):
        """Test if microphone is working"""
        if not self.audio:
            return False
        
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            # Read a few chunks
            for _ in range(10):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                energy = self._calculate_energy(data)
                logger.info(f"Microphone energy: {energy:.2f}")
            
            stream.stop_stream()
            stream.close()
            
            logger.info("✓ Microphone test successful")
            return True
            
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False
