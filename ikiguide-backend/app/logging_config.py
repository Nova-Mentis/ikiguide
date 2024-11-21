import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

def setup_logging(log_level: str = None, log_dir: str = None):
    """
    Configure logging for the application.
    
    :param log_level: Optional log level override
    :param log_dir: Optional log directory override
    """
    # Debug print for settings
    print(f"DEBUG: APP_DEBUG = {settings.APP_DEBUG}")
    print(f"DEBUG: APP_DEBUG env value = {os.getenv('APP_DEBUG')}")

    # Use provided values or fall back to settings
    level = log_level or settings.LOG_LEVEL
    directory = log_dir or settings.LOG_DIR

    # Ensure log directory exists
    log_path = Path(directory)
    log_path.mkdir(exist_ok=True, parents=True)

    # Configure logging levels
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger configuration
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            
            # File handler with rotation
            RotatingFileHandler(
                log_path / 'app.log', 
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5
            )
        ]
    )

    # Suppress overly verbose loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    # Create a logger for the application
    logger = logging.getLogger('ikiguide')
    logger.setLevel(numeric_level)

    return logger

# Create a global logger
logger = setup_logging()
