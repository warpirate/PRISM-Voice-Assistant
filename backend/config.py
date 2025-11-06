"""
Configuration Management System
Handles all system settings and user preferences
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import json

# Load environment variables
load_dotenv()

class VoiceConfig(BaseModel):
    """Voice interaction settings (manual activation only)"""
    language: str = Field(default="en-US")
    tts_voice: str = Field(default="default")
    tts_rate: int = Field(default=175, ge=50, le=300)
    tts_volume: float = Field(default=0.9, ge=0.0, le=1.0)
    enable_voice_feedback: bool = Field(default=True)

class AIConfig(BaseModel):
    """AI provider settings"""
    provider: str = Field(default="gemini")  # gemini, local
    gemini_api_key: Optional[str] = Field(default=None)
    model: str = Field(default="gemini-2.5-flash")  # gemini-2.5-flash, gemini-2.0-flash, gemini-2.0-flash-lite
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048)  # Increased for better responses

class WebSearchConfig(BaseModel):
    """Web search settings"""
    brave_api_key: Optional[str] = Field(default=None)

class UIConfig(BaseModel):
    """User interface settings"""
    theme: str = Field(default="dark")  # dark, light, auto
    transparency: float = Field(default=0.85, ge=0.0, le=1.0)
    animation_speed: str = Field(default="normal")  # slow, normal, fast
    minimize_to_tray: bool = Field(default=True)
    activation_hotkey: str = Field(default="ctrl+space")
    toggle_hotkey: str = Field(default="ctrl+shift+p")

class PrivacyConfig(BaseModel):
    """Privacy and data retention settings"""
    store_conversations: bool = Field(default=True)
    retention_days: int = Field(default=30, ge=1, le=365)
    enable_analytics: bool = Field(default=False)
    local_processing: bool = Field(default=True)

class SystemConfig(BaseModel):
    """Overall system configuration"""
    log_level: str = Field(default="INFO")
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Load values from environment
        self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Voice settings
        self.voice.language = os.getenv("VOICE_LANGUAGE", self.voice.language)
        self.voice.tts_voice = os.getenv("TTS_VOICE", self.voice.tts_voice)
        self.voice.tts_rate = int(os.getenv("TTS_RATE", self.voice.tts_rate))
        self.voice.tts_volume = float(os.getenv("TTS_VOLUME", self.voice.tts_volume))
        self.voice.enable_voice_feedback = os.getenv("ENABLE_VOICE_FEEDBACK", "true").lower() == "true"

        # AI settings
        self.ai.provider = os.getenv("AI_PROVIDER", self.ai.provider)
        self.ai.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.ai.model = os.getenv("GEMINI_MODEL", self.ai.model)

        # Web search settings
        self.web_search.brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")

        # UI settings
        self.ui.theme = os.getenv("THEME", self.ui.theme)
        self.ui.transparency = float(os.getenv("TRANSPARENCY", self.ui.transparency))
        self.ui.animation_speed = os.getenv("ANIMATION_SPEED", self.ui.animation_speed)
        self.ui.minimize_to_tray = os.getenv("MINIMIZE_TO_TRAY", "true").lower() == "true"
        self.ui.activation_hotkey = os.getenv("ACTIVATION_HOTKEY", self.ui.activation_hotkey)
        self.ui.toggle_hotkey = os.getenv("TOGGLE_VISIBILITY_HOTKEY", self.ui.toggle_hotkey)

        # Privacy settings
        self.privacy.store_conversations = os.getenv("STORE_CONVERSATIONS", "true").lower() == "true"
        self.privacy.retention_days = int(os.getenv("RETENTION_DAYS", self.privacy.retention_days))
        self.privacy.enable_analytics = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"

        # System settings
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)

    def save_to_file(self, file_path: Optional[Path] = None):
        """Save configuration to JSON file"""
        if file_path is None:
            file_path = self.data_dir / "config.json"
        
        with open(file_path, 'w') as f:
            json.dump(self.model_dump(mode='json'), f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'SystemConfig':
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

# Global configuration instance
config = SystemConfig()
