"""
Voice Interaction Pipeline
Handles wake word detection, speech recognition, and text-to-speech
"""

import asyncio
import queue
import threading
from typing import Optional, Callable
import speech_recognition as sr
import pyttsx3
from loguru import logger

from backend.config import config


class VoicePipeline:
    """
    Manages voice interaction components:
    - Speech-to-text (Google Speech Recognition)
    - Text-to-speech (pyttsx3)
    - Manual activation only (no wake word)
    """

    def __init__(self):
        self.initialized = False
        
        # Audio components
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.porcupine = None
        self.audio_stream = None
        
        # Threading
        self.wake_word_thread: Optional[threading.Thread] = None
        self.wake_word_active = False
        
        # Callbacks
        self.on_wake_word: Optional[Callable] = None
        self.on_speech_recognized: Optional[Callable] = None
        self.on_audio_level: Optional[Callable] = None
        
        # Audio state
        self.is_listening = False
        self.audio_queue = queue.Queue()

    async def initialize(self):
        """Initialize all voice components"""
        if self.initialized:
            return
        
        logger.info("Initializing voice pipeline...")
        
        try:
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Initialize TTS
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', config.voice.tts_rate)
            self.tts_engine.setProperty('volume', config.voice.tts_volume)
            
            # Set voice if specified
            if config.voice.tts_voice != "default":
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if config.voice.tts_voice.lower() in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Wake word detection removed - using manual activation only
            self.porcupine = None
            
            self.initialized = True
            logger.success("Voice pipeline initialized (manual activation mode)")
            
        except Exception as e:
            logger.error(f"Error initializing voice pipeline: {e}")
            raise

    # Wake word detection removed - manual activation only

    async def start_listening(self):
        """Start listening for speech input"""
        if self.is_listening:
            logger.warning("Already listening, ignoring duplicate request")
            return
        
        self.is_listening = True
        logger.info("Starting speech recognition...")
        
        try:
            with self.microphone as source:
                logger.info("Microphone active, listening for speech...")
                
                # Listen for audio with timeout
                audio = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                )
                
                logger.info("Audio captured, recognizing...")
                
                # Recognize speech
                text = await self._recognize_speech(audio)
                
                if text and self.on_speech_recognized:
                    await self.on_speech_recognized(text)
                elif not text:
                    logger.warning("No text recognized from audio")
        
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout - no speech detected within 10 seconds")
            if self.on_speech_recognized:
                # Notify that listening timed out
                pass
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}", exc_info=True)
        finally:
            self.is_listening = False
            logger.info("Speech recognition session ended")

    async def _recognize_speech(self, audio) -> Optional[str]:
        """Recognize speech from audio using Google Speech Recognition"""
        try:
            logger.info("Recognizing speech...")
            
            # Use Google Speech Recognition (free)
            text = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.recognizer.recognize_google(audio, language=config.voice.language)
            )
            
            logger.success(f"Recognized: {text}")
            return text
            
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None

    async def speak(self, text: str):
        """Convert text to speech and play"""
        if not text:
            return
        
        logger.info(f"Speaking: {text}")
        
        try:
            # Run TTS in thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._speak_sync(text)
            )
        except Exception as e:
            logger.error(f"Error during text-to-speech: {e}")

    def _speak_sync(self, text: str):
        """Synchronous TTS (runs in thread)"""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    async def play_activation_sound(self):
        """Play sound feedback for activation"""
        # Simple beep using TTS
        await self.speak("Listening")

    async def play_error_sound(self):
        """Play sound feedback for errors"""
        await self.speak("Error")

    async def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False

    async def stop_wake_word_detection(self):
        """Stop wake word detection"""
        self.wake_word_active = False
        if self.wake_word_thread:
            self.wake_word_thread.join(timeout=2)

    async def shutdown(self):
        """Shutdown voice pipeline"""
        logger.info("Shutting down voice pipeline...")
        
        await self.stop_wake_word_detection()
        
        if self.porcupine:
            self.porcupine.delete()
        
        if self.tts_engine:
            self.tts_engine.stop()
        
        self.initialized = False
        logger.success("Voice pipeline shutdown complete")
