"""
PRISM Main Entry Point
Starts the coordinator and manages the application lifecycle
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import config
from backend.coordinator import coordinator


def setup_logging():
    """Configure logging with Unicode support"""
    import io
    
    logger.remove()  # Remove default handler
    
    # Create UTF-8 wrapped stdout to handle Unicode characters like emojis
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Send ALL logs to UTF-8 wrapped STDOUT to avoid Electron interpreting STDERR as errors
    logger.add(
        utf8_stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=config.log_level,
        colorize=False,  # Disable colorize to avoid potential stderr usage
        backtrace=False,
        diagnose=False,
        catch=True  # Catch logging errors to prevent crashes
    )
    
    # File logging with UTF-8 encoding
    log_dir = config.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Open file with UTF-8 encoding explicitly
    log_file_path = log_dir / "prism_{time:YYYY-MM-DD}.log"
    logger.add(
        str(log_file_path),
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        catch=True,  # Catch logging errors to prevent crashes
        encoding="utf-8"  # This works for file handlers
    )
    
    logger.info("Logging configured with Unicode support")


async def main():
    """Main application entry point"""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("PRISM - Personal Response Interface for System Management")
    logger.info("=" * 60)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info("=" * 60)
    
    try:
        # Start the coordinator
        await coordinator.start()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Graceful shutdown
        await coordinator.shutdown()
        logger.info("PRISM terminated")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
