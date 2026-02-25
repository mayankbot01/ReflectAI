"""Logging Configuration for ReflectAI Backend

Sets up structured logging with proper formatting and levels.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """Configure application logging with file and console handlers"""
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Format for console (colorized in development)
    if settings.is_development():
        console_format = logging.Formatter(
            "\033[36m%(asctime)s\033[0m - "
            "\033[35m%(name)s\033[0m - "
            "\033[33m%(levelname)s\033[0m - "
            "%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler (if LOG_FILE is specified)
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - "
            "[%(filename)s:%(lineno)d]",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {settings.LOG_LEVEL}")
