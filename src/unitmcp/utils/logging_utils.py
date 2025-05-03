"""
Logging utilities for UnitMCP.

This module provides standardized logging configuration and utilities
for the UnitMCP project to ensure consistent logging across all modules.

Functions:
    configure_logging: Configure logging with standardized settings
    get_logger: Get a logger with standardized settings
    log_exception: Log an exception with appropriate level and traceback

Example:
    ```python
    from unitmcp.utils.logging_utils import configure_logging, get_logger
    
    # Configure logging for the application
    configure_logging(level="INFO", log_file="app.log")
    
    # Get a logger for a specific module
    logger = get_logger(__name__)
    
    # Use the logger
    logger.info("Application started")
    ```
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union, Any

# Define log levels with their corresponding integer values
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Define a standard log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"


def configure_logging(
    level: Union[str, int] = "INFO",
    log_file: Optional[str] = None,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_dir: Optional[str] = None,
    console: bool = True,
    detailed: bool = False,
    quiet: bool = False
) -> None:
    """
    Configure logging with standardized settings.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or integer value
        log_file: Path to log file, if None, logs only to console
        log_format: Format string for log messages
        log_dir: Directory to store log files, if None, uses current directory
        console: Whether to log to console
        detailed: Whether to use detailed log format
        quiet: If True, only log warnings and errors
    """
    # Convert string level to integer if needed
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # Override level if quiet mode is enabled
    if quiet and level < logging.WARNING:
        level = logging.WARNING
    
    # Use detailed format if requested
    if detailed:
        log_format = DETAILED_LOG_FORMAT
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        if log_dir:
            # Create log directory if it doesn't exist
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            log_file = os.path.join(log_dir, log_file)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str, level: Optional[Union[str, int]] = None) -> logging.Logger:
    """
    Get a logger with standardized settings.
    
    Args:
        name: Name of the logger, typically __name__
        level: Optional level to set for this logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level if specified
    if level is not None:
        if isinstance(level, str):
            level = LOG_LEVELS.get(level.upper(), logging.INFO)
        logger.setLevel(level)
    
    return logger


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An exception occurred",
    level: str = "ERROR",
    include_traceback: bool = True
) -> None:
    """
    Log an exception with appropriate level and traceback.
    
    Args:
        logger: Logger instance
        exception: Exception to log
        message: Message to log with the exception
        level: Log level to use
        include_traceback: Whether to include traceback in the log
    """
    log_method = getattr(logger, level.lower(), logger.error)
    
    if include_traceback:
        log_method(f"{message}: {exception}\n{traceback.format_exc()}")
    else:
        log_method(f"{message}: {exception}")


def create_timed_rotating_logger(
    name: str,
    log_dir: str,
    level: Union[str, int] = "INFO",
    backup_count: int = 7,
    when: str = "midnight"
) -> logging.Logger:
    """
    Create a logger that rotates files based on time.
    
    Args:
        name: Name of the logger
        log_dir: Directory to store log files
        level: Log level
        backup_count: Number of backup files to keep
        when: When to rotate ('S', 'M', 'H', 'D', 'W0'-'W6', 'midnight')
        
    Returns:
        Configured logger instance
    """
    from logging.handlers import TimedRotatingFileHandler
    
    # Convert string level to integer if needed
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create handler
    log_file = os.path.join(log_dir, f"{name}.log")
    handler = TimedRotatingFileHandler(
        log_file,
        when=when,
        backupCount=backup_count
    )
    
    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def log_method_call(logger: logging.Logger, level: str = "DEBUG"):
    """
    Decorator to log method calls with arguments and return values.
    
    Args:
        logger: Logger instance
        level: Log level to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            log_method = getattr(logger, level.lower(), logger.debug)
            log_method(f"Calling {func_name}({signature})")
            
            try:
                result = func(*args, **kwargs)
                log_method(f"{func_name} returned {result!r}")
                return result
            except Exception as e:
                log_exception(logger, e, f"Exception in {func_name}")
                raise
        
        return wrapper
    
    return decorator
