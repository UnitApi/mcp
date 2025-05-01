"""
logger.py
"""

"""Logging utilities for MCP hardware."""

import logging
import sys
import json
from typing import Optional
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """
    A simple JSON formatter for logging.
    """

    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "name": record.name,
            "levelname": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "exc_info") and record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def get_logger(
    name: str, level: int = logging.INFO, json_format: bool = False
) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Set formatter
        if json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def setup_logging(
    level: int = logging.INFO, json_format: bool = False, log_file: Optional[str] = None
):
    """Setup logging configuration for the entire application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    # Set formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    if log_file:
        file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
