"""
Centralized logging configuration for the Agentic Interview System.

This module sets up structured logging with:
- Configurable log level via environment variable
- Console output with timestamp, level, module, and message
- Safe defaults that won't crash the app if misconfigured

Usage:
    from logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Starting interview session", extra={"session_id": 123})
"""

import logging
import os
import sys
from typing import Optional


# Default log level
DEFAULT_LOG_LEVEL = "INFO"

# Log format: timestamp | level | module | message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_log_level_from_env() -> str:
    """
    Get log level from environment variable.

    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    # Validate level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if level not in valid_levels:
        print(f"Warning: Invalid LOG_LEVEL '{level}', using '{DEFAULT_LOG_LEVEL}'", file=sys.stderr)
        return DEFAULT_LOG_LEVEL

    return level


def configure_logging(level: Optional[str] = None):
    """
    Configure the root logger with console output.

    Args:
        level: Log level string (DEBUG, INFO, etc.). If None, reads from environment.
    """
    if level is None:
        level = get_log_level_from_env()

    # Get numeric level
    numeric_level = getattr(logging, level, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Configure logging on module import
try:
    configure_logging()
except Exception as e:
    # Safe fallback: use basicConfig if configuration fails
    print(f"Warning: Failed to configure logging: {e}", file=sys.stderr)
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
