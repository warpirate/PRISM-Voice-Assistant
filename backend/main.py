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
    """Configure logging"""
    logger.remove()  # Remove default handler
    
    # Send ALL logs to STDOUT to avoid Electron interpreting STDERR as errors
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=config.log_level,
        colorize=False,  # Disable colorize to avoid potential stderr usage
        backtrace=False,
        diagnose=False
    )
    
    # File logging
    log_dir = config.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_dir / "prism_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}"
    )
    
    logger.info("Logging configured")


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
