"""
Text-to-Speech module for PRISM
Uses pyttsx3 for quick setup, can be upgraded to Coqui TTS later
"""

import logging
import pyttsx3
from pathlib import Path

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Handles text-to-speech output"""
    
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self._configure_voice()
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.engine = None
    
    def _configure_voice(self):
        """Configure voice properties"""
        if not self.engine:
            return
        
        try:
            # Set properties
            self.engine.setProperty('rate', 175)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Try to set a better voice
            voices = self.engine.getProperty('voices')
            
            # Prefer female voice or first available
            for voice in voices:
                if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Using voice: {voice.name}")
                    break
            else:
                # Use first voice if no preference found
                if voices:
                    self.engine.setProperty('voice', voices[0].id)
                    logger.info(f"Using default voice: {voices[0].name}")
                    
        except Exception as e:
            logger.warning(f"Failed to configure voice: {e}")
    
    def speak(self, text: str, block: bool = True):
        """
        Speak the given text
        
        Args:
            text: Text to speak
            block: Whether to block until speech is complete
        """
        if not self.engine:
            logger.warning("TTS engine not available")
            return
        
        try:
            logger.info(f"Speaking: {text[:50]}...")
            self.engine.say(text)
            
            if block:
                self.engine.runAndWait()
            else:
                # Non-blocking speech
                self.engine.startLoop(False)
                self.engine.iterate()
                self.engine.endLoop()
                
        except Exception as e:
            logger.error(f"Failed to speak: {e}")
    
    def save_to_file(self, text: str, filename: str):
        """
        Save speech to audio file
        
        Args:
            text: Text to convert
            filename: Output filename
        """
        if not self.engine:
            logger.warning("TTS engine not available")
            return
        
        try:
            output_path = Path(__file__).parent.parent / "temp" / filename
            output_path.parent.mkdir(exist_ok=True)
            
            self.engine.save_to_file(text, str(output_path))
            self.engine.runAndWait()
            
            logger.info(f"Saved speech to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save speech: {e}")
            return None
    
    def stop(self):
        """Stop current speech"""
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                logger.error(f"Failed to stop speech: {e}")
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [{"id": v.id, "name": v.name, "languages": v.languages} for v in voices]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
    
    def set_voice(self, voice_id: str):
        """Set voice by ID"""
        if not self.engine:
            return
        
        try:
            self.engine.setProperty('voice', voice_id)
            logger.info(f"Voice changed to {voice_id}")
        except Exception as e:
            logger.error(f"Failed to set voice: {e}")
