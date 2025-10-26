"""
Voice pipeline for PRISM
Handles wake word detection and speech recognition
"""

import logging
import time
import threading
import os
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Try to import Porcupine for wake word detection
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    logger.warning("Porcupine not available. Using custom wake word detector.")
    PORCUPINE_AVAILABLE = False

# Import custom wake word detector
try:
    from wake_word_detector import SimpleWakeWordDetector
    CUSTOM_WAKE_WORD_AVAILABLE = True
except ImportError:
    logger.warning("Custom wake word detector not available")
    CUSTOM_WAKE_WORD_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("Whisper not available. Speech recognition disabled.")
    WHISPER_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("PyAudio not available. Audio input disabled.")
    PYAUDIO_AVAILABLE = False

import wave
import tempfile
from pathlib import Path


class VoicePipeline:
    """Manages voice input pipeline"""
    
    def __init__(self, on_wake_word: Callable = None):
        self.on_wake_word = on_wake_word
        self.running = False
        self.porcupine = None
        self.custom_wake_detector = None
        self.whisper_model = None
        self.audio = None
        self.stream = None
        self.use_custom_detector = False
        self.prefer_custom = os.getenv("USE_CUSTOM_WAKE", "1").lower() not in ("0", "false", "no")
        
        self._initialize()
    
    def _initialize(self):
        """Initialize voice components"""
        # Initialize PyAudio
        if PYAUDIO_AVAILABLE:
            try:
                self.audio = pyaudio.PyAudio()
                logger.info("PyAudio initialized")
            except Exception as e:
                logger.error(f"Failed to initialize PyAudio: {e}")
        
        # Initialize Whisper
        if WHISPER_AVAILABLE:
            try:
                logger.info("Loading Whisper model (this may take a moment)...")
                self.whisper_model = whisper.load_model("base")
                logger.info("Whisper model loaded")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
        
        # Initialize wake word detection
        if self.prefer_custom:
            # Try custom 'Hey PRISM' first
            self._initialize_custom_detector()
            if not self.custom_wake_detector and PORCUPINE_AVAILABLE:
                try:
                    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
                    if access_key:
                        self.porcupine = pvporcupine.create(
                            access_key=access_key,
                            keywords=["computer"]
                        )
                        logger.info("Porcupine fallback initialized with 'computer' keyword")
                        logger.info("Say 'Computer' to activate PRISM")
                    else:
                        logger.warning("PORCUPINE_ACCESS_KEY not set. Manual activation only if custom detector not available.")
                except Exception as e:
                    logger.error(f"Failed to initialize Porcupine fallback: {e}")
        else:
            # Prefer Porcupine first
            if PORCUPINE_AVAILABLE:
                try:
                    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
                    if access_key:
                        self.porcupine = pvporcupine.create(
                            access_key=access_key,
                            keywords=["computer"]
                        )
                        logger.info("Porcupine wake word detection initialized with 'computer' keyword")
                        logger.info("Say 'Computer' to activate PRISM")
                    else:
                        logger.warning("PORCUPINE_ACCESS_KEY not set. Trying custom wake word detector.")
                        self._initialize_custom_detector()
                except Exception as e:
                    logger.error(f"Failed to initialize Porcupine: {e}")
                    logger.info("Trying custom wake word detector...")
                    self._initialize_custom_detector()
            else:
                # Use custom detector if Porcupine not available
                self._initialize_custom_detector()
    
    def _initialize_custom_detector(self):
        """Initialize custom wake word detector for 'Hey PRISM'"""
        if CUSTOM_WAKE_WORD_AVAILABLE:
            try:
                self.custom_wake_detector = SimpleWakeWordDetector(
                    callback=self._on_custom_wake_word,
                    wake_phrases=["hey prism", "prism", "hey prison"]
                )
                self.use_custom_detector = True
                logger.info("✓ Custom wake word detector initialized")
                logger.info("Say 'Hey PRISM' or 'PRISM' to activate")
            except Exception as e:
                logger.error(f"Failed to initialize custom wake word detector: {e}")
                logger.info("Wake word detection disabled. Use click/keyboard activation.")
        else:
            logger.warning("Custom wake word detector not available")
            logger.info("Wake word detection disabled. Use click/keyboard activation.")
    
    def _on_custom_wake_word(self):
        """Callback for custom wake word detector"""
        if self.on_wake_word:
            self.on_wake_word()
    
    def start(self):
        """Start listening for wake word"""
        if not self.audio:
            logger.error("Cannot start voice pipeline: PyAudio not available")
            return
        
        self.running = True
        
        # Start appropriate wake word detector
        if self.use_custom_detector and self.custom_wake_detector:
            # Use custom detector
            self.custom_wake_detector.start()
            logger.info("Voice pipeline started with custom wake word detector")
        elif self.porcupine:
            # Use Porcupine
            wake_thread = threading.Thread(target=self._wake_word_loop, daemon=True)
            wake_thread.start()
            logger.info("Voice pipeline started with Porcupine")
        else:
            logger.warning("No wake word detector available. Use manual activation.")
        
        logger.info("Voice pipeline started")
    
    def stop(self):
        """Stop voice pipeline"""
        self.running = False
        
        if self.custom_wake_detector:
            try:
                self.custom_wake_detector.stop()
            except:
                pass
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        if self.porcupine:
            self.porcupine.delete()
        
        if self.audio:
            self.audio.terminate()
        
        logger.info("Voice pipeline stopped")
    
    def _wake_word_loop(self):
        """Continuously listen for wake word"""
        if not self.porcupine:
            logger.warning("Wake word detection not available, using manual trigger only")
            return
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.porcupine.sample_rate,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            logger.info("Listening for wake word 'Computer'...")
            logger.info("Say 'Computer' to activate PRISM")
            
            while self.running:
                try:
                    pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm = [int.from_bytes(pcm[i:i+2], byteorder='little', signed=True) 
                           for i in range(0, len(pcm), 2)]
                    
                    # Porcupine detection
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:  # Wake word detected
                        logger.info("Wake word 'Computer' detected!")
                        if self.on_wake_word:
                            self.on_wake_word()
                    
                except Exception as e:
                    logger.error(f"Error in wake word loop: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
    
    def listen_for_command(self, duration: int = 5) -> Optional[str]:
        """
        Listen for voice command after wake word
        
        Args:
            duration: Seconds to record
            
        Returns:
            Transcribed text or None
        """
        if not self.audio or not self.whisper_model:
            logger.error("Cannot listen: Audio or Whisper not available")
            return None
        
        try:
            logger.info(f"Recording for {duration} seconds...")
            
            # Record audio
            frames = []
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            for _ in range(0, int(16000 / 1024 * duration)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save to temporary file
            temp_dir = Path(tempfile.gettempdir())
            audio_file = temp_dir / "prism_command.wav"
            
            with wave.open(str(audio_file), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))
            
            # Transcribe with Whisper
            logger.info("Transcribing audio...")
            result = self.whisper_model.transcribe(str(audio_file))
            text = result["text"].strip()
            
            logger.info(f"Transcribed: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Failed to listen for command: {e}")
            return None
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        if not self.audio:
            return False
        
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            # Try to read a frame
            data = stream.read(1024, exception_on_overflow=False)
            
            stream.stop_stream()
            stream.close()
            
            logger.info("Microphone test successful")
            return True
            
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False
