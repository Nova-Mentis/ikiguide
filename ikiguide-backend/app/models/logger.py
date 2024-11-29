import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from app.config import settings

class LoggingManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_level: str = None, log_dir: str = None):
        if not LoggingManager._initialized:
            self.logger = logging.getLogger()
            self._setup_logging(settings.LOG_LEVEL, log_dir)
            LoggingManager._initialized = True

    def _setup_logging(self, log_level: str = None, log_dir: str = None):
        """
        Configure logging for the application.
        
        :param log_level: Optional log level override
        :param log_dir: Optional log directory override
        """
        # Use provided values or fall back to settings
        level = settings.LOG_LEVEL
        directory = settings.LOG_DIR

        # Ensure log directory exists with error handling
        try:
            log_path = Path(directory)
            log_path.mkdir(exist_ok=True, parents=True)
        except (PermissionError, OSError) as e:
            print(f"ERROR: Unable to create log directory {directory}: {e}")
            directory = './logs'  # Fallback to current directory
            log_path = Path(directory)
            log_path.mkdir(exist_ok=True, parents=True)

        # Configure logging levels with robust error handling
        try:
            self.logger.setLevel(level)
        except AttributeError:
            print(f"WARNING: Invalid log level {level}. Defaulting to INFO.")
            self.logger.setLevel("INFO")  # Set to INFO if provided level is invalid

        # Clear any existing handlers to prevent duplicate logging
        self.logger.handlers.clear()

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Create file handler
        log_file = os.path.join(directory, 'app.log')
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger

# Initialize the logging manager
logging_manager = LoggingManager()
logger = logging_manager.get_logger()
logger.info("Logging system initialized successfully")

# Suppress warnings
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)