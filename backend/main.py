"""
PRISM - Personal Response Interface for System Management
Main entry point for the backend
"""

import sys
import json
import logging
import threading
from pathlib import Path

# Setup logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "prism.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# Import PRISM modules
try:
    from voice_pipeline import VoicePipeline
    from prism_llm import PrismLLM
    from system_control import SystemController
    from memory import MemoryManager
    from tts import TextToSpeech
    from web_search import WebSearch
    from file_ops import FileOps
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.info("Some modules may not be available yet. Continuing with basic functionality.")


class PRISMBackend:
    """Main PRISM backend coordinator"""
    
    def __init__(self):
        self.running = False
        self.llm = None
        self.voice_pipeline = None
        self.system_controller = None
        self.memory = None
        self.tts = None
        self.web_search = None
        self.file_ops = None
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all PRISM components"""
        try:
            logger.info("Initializing PRISM components...")
            
            # Initialize memory manager
            self.memory = MemoryManager()
            logger.info("✓ Memory manager initialized")
            
            # Initialize LLM
            self.llm = PrismLLM()
            logger.info("✓ LLM initialized")
            
            # Initialize system controller
            self.system_controller = SystemController()
            logger.info("✓ System controller initialized")
            
            # Initialize TTS
            self.tts = TextToSpeech()
            logger.info("✓ Text-to-speech initialized")
            
            # Initialize web search
            self.web_search = WebSearch()
            logger.info("✓ Web search ready")

            # Initialize file operations
            self.file_ops = FileOps()
            logger.info("✓ File operations ready")

            # Initialize voice pipeline (may take longer)
            self.voice_pipeline = VoicePipeline(on_wake_word=self._on_wake_word)
            logger.info("✓ Voice pipeline initialized")
            
            self._send_status("Ready", "#4cd964")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            self._send_error(f"Initialization error: {str(e)}")
    
    def _send_message(self, msg_type, **kwargs):
        """Send JSON message to Electron frontend"""
        message = {"type": msg_type, **kwargs}
        print(json.dumps(message), flush=True)
    
    def _send_status(self, text, color="#4cd964"):
        """Send status update"""
        self._send_message("status", text=text, color=color)
    
    def _send_error(self, message):
        """Send error message"""
        self._send_message("error", message=message)
        logger.error(message)
    
    def _on_wake_word(self):
        """Callback when wake word is detected"""
        logger.info("Wake word 'PRISM' detected!")
        self._send_message("wake_word")
        self._send_status("Listening...", "#667eea")
        
        # Start listening for command
        self._process_voice_command()
    
    def _process_voice_command(self, text_input=None):
        """Process command from voice or text"""
        try:
            if text_input is not None:
                user_input = text_input
            else:
                user_input = self.voice_pipeline.listen_for_command()
            
            if not user_input:
                self._send_status("No speech detected", "#ffa500")
                return
            
            logger.info(f"User said: {user_input}")
            self._send_message("speech_recognized", text=user_input)
            self._send_status("Processing...", "#ffa500")
            
            # Process with LLM
            response_data = self.llm.query(user_input)
            
            # Execute action if needed
            if response_data.get("action") == "system":
                command = response_data.get("command")
                if command:
                    success = self.system_controller.execute(command)
                    if not success:
                        response_data["text"] = "Sorry, I couldn't execute that command."
            elif response_data.get("action") == "search":
                query = response_data.get("query") or user_input
                if self.web_search and query:
                    results = self.web_search.search(query)
                    response_data["text"] = results.get("summary") or response_data.get("text", "")
                else:
                    response_data["text"] = "Search is unavailable."
            elif response_data.get("action") == "file":
                operation = response_data.get("operation")
                path = response_data.get("path")
                content = response_data.get("content")
                if self.file_ops:
                    success, message = self.file_ops.handle(operation, path, content)
                    response_data["text"] = message
                else:
                    response_data["text"] = "File operations are unavailable."
            
            # Save to memory
            self.memory.save_interaction(
                user_input=user_input,
                response=response_data.get("text", ""),
                action=response_data.get("action", "")
            )
            
            # Send response to UI
            response_text = response_data.get("text", "I'm not sure how to respond to that.")
            self._send_message("response", text=response_text)
            
            # Speak response
            self.tts.speak(response_text)
            
            self._send_message("response_complete")
            self._send_status("Ready", "#4cd964")
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self._send_error(f"Processing error: {str(e)}")
            self._send_status("Ready", "#4cd964")
    
    def _handle_manual_trigger(self):
        """Handle manual trigger from UI (orb click)"""
        logger.info("Manual trigger activated")
        self._on_wake_word()
    
    def _handle_stdin(self):
        """Handle messages from Electron frontend"""
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                data = json.loads(line.strip())
                msg_type = data.get("type")
                
                if msg_type == "manual_trigger":
                    self._handle_manual_trigger()
                elif msg_type == "text_query":
                    text = data.get("text", "")
                    if text:
                        self._process_voice_command(text)
                elif msg_type == "shutdown":
                    self.stop()
                    
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from stdin")
            except Exception as e:
                logger.error(f"Error handling stdin: {e}")
    
    def start(self):
        """Start PRISM backend"""
        logger.info("Starting PRISM backend...")
        self.running = True
        
        # Start stdin handler in separate thread
        stdin_thread = threading.Thread(target=self._handle_stdin, daemon=True)
        stdin_thread.start()
        
        # Start voice pipeline
        if self.voice_pipeline:
            try:
                self.voice_pipeline.start()
            except Exception as e:
                logger.error(f"Failed to start voice pipeline: {e}")
                self._send_error("Voice pipeline failed to start")
        
        logger.info("PRISM backend started successfully")
    
    def stop(self):
        """Stop PRISM backend"""
        logger.info("Stopping PRISM backend...")
        self.running = False
        
        if self.voice_pipeline:
            self.voice_pipeline.stop()
        
        logger.info("PRISM backend stopped")


def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("PRISM - Personal Response Interface for System Management")
    logger.info("=" * 50)
    
    try:
        backend = PRISMBackend()
        backend.start()
        
        # Keep running
        while backend.running:
            import time
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if 'backend' in locals():
            backend.stop()


if __name__ == "__main__":
    main()
