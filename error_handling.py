"""
Error handling utilities for the Agentic Interview System.

This module provides:
- Error sanitization to prevent exposing internal details to users
- Standard error codes for common error types
- User-friendly error messages
"""

from enum import Enum
from typing import Optional
import re

from logging_config import get_logger

logger = get_logger(__name__)


class ErrorCode(Enum):
    """Standard error codes for the application."""

    # Authentication errors
    AUTH_INVALID_PASSWORD = "auth_invalid_password"
    AUTH_SESSION_EXPIRED = "auth_session_expired"

    # LLM errors
    LLM_API_ERROR = "llm_api_error"
    LLM_RATE_LIMIT = "llm_rate_limit"
    LLM_INVALID_KEY = "llm_invalid_key"
    LLM_TIMEOUT = "llm_timeout"
    LLM_PARSE_ERROR = "llm_parse_error"

    # Database errors
    DB_CONNECTION_ERROR = "db_connection_error"
    DB_NOT_FOUND = "db_not_found"
    DB_CONSTRAINT_ERROR = "db_constraint_error"

    # Validation errors
    VALIDATION_ERROR = "validation_error"
    INVALID_CONFIG = "invalid_config"

    # General errors
    INTERNAL_ERROR = "internal_error"
    UNKNOWN_ERROR = "unknown_error"


# Mapping of error codes to user-friendly messages
ERROR_MESSAGES = {
    ErrorCode.AUTH_INVALID_PASSWORD: "Incorrect password. Please try again.",
    ErrorCode.AUTH_SESSION_EXPIRED: "Your session has expired. Please log in again.",

    ErrorCode.LLM_API_ERROR: "AI evaluation is temporarily unavailable. Please try again later.",
    ErrorCode.LLM_RATE_LIMIT: "Too many requests. Please wait a moment before trying again.",
    ErrorCode.LLM_INVALID_KEY: "AI service is not properly configured. Please contact support.",
    ErrorCode.LLM_TIMEOUT: "AI evaluation timed out. Please try again.",
    ErrorCode.LLM_PARSE_ERROR: "Failed to process AI response. Please try again.",

    ErrorCode.DB_CONNECTION_ERROR: "Database connection failed. Please try again later.",
    ErrorCode.DB_NOT_FOUND: "The requested item was not found.",
    ErrorCode.DB_CONSTRAINT_ERROR: "This operation would violate data constraints.",

    ErrorCode.VALIDATION_ERROR: "Invalid input. Please check your data and try again.",
    ErrorCode.INVALID_CONFIG: "Invalid configuration. Please check your settings.",

    ErrorCode.INTERNAL_ERROR: "An internal error occurred. Please try again later.",
    ErrorCode.UNKNOWN_ERROR: "An unexpected error occurred. Please try again later.",
}


# Patterns to detect sensitive information in error messages
SENSITIVE_PATTERNS = [
    # API keys
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
    r'sk-ant-[a-zA-Z0-9]{20,}',  # Anthropic keys
    # File paths
    r'/Users/[^\s]+',
    r'/home/[^\s]+',
    r'C:\\[^\s]+',
    # Database connection strings
    r'postgresql://[^\s]+',
    r'mysql://[^\s]+',
    r'sqlite:///[^\s]+',
    # Generic secrets
    r'password[=:][^\s]+',
    r'secret[=:][^\s]+',
    r'token[=:][^\s]+',
]


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize an error message to remove sensitive information.

    Args:
        error: The exception to sanitize

    Returns:
        Sanitized error message safe for display to users
    """
    message = str(error)

    # Remove sensitive patterns
    for pattern in SENSITIVE_PATTERNS:
        message = re.sub(pattern, '[REDACTED]', message, flags=re.IGNORECASE)

    return message


def get_error_code(error: Exception) -> ErrorCode:
    """
    Determine the appropriate error code for an exception.

    Args:
        error: The exception to classify

    Returns:
        Appropriate ErrorCode enum value
    """
    error_type = type(error).__name__
    error_message = str(error).lower()

    # LLM-related errors
    if 'rate' in error_message and 'limit' in error_message:
        return ErrorCode.LLM_RATE_LIMIT
    if 'authentication' in error_message or 'api key' in error_message.lower():
        return ErrorCode.LLM_INVALID_KEY
    if 'timeout' in error_message:
        return ErrorCode.LLM_TIMEOUT
    if error_type in ('APIError', 'OpenAIError', 'AnthropicError'):
        return ErrorCode.LLM_API_ERROR
    if 'json' in error_message or 'parse' in error_message:
        return ErrorCode.LLM_PARSE_ERROR

    # Database errors
    if error_type == 'IntegrityError':
        return ErrorCode.DB_CONSTRAINT_ERROR
    if error_type == 'OperationalError':
        return ErrorCode.DB_CONNECTION_ERROR
    if 'not found' in error_message:
        return ErrorCode.DB_NOT_FOUND

    # Validation errors
    if error_type == 'ValidationError' or 'invalid' in error_message:
        return ErrorCode.VALIDATION_ERROR
    if 'config' in error_message:
        return ErrorCode.INVALID_CONFIG

    return ErrorCode.UNKNOWN_ERROR


def get_user_message(error_code: ErrorCode) -> str:
    """
    Get the user-friendly message for an error code.

    Args:
        error_code: The ErrorCode enum value

    Returns:
        User-friendly error message
    """
    return ERROR_MESSAGES.get(error_code, ERROR_MESSAGES[ErrorCode.UNKNOWN_ERROR])


def handle_error(
    error: Exception,
    context: Optional[str] = None,
    log_level: str = "error"
) -> str:
    """
    Handle an error by logging it and returning a user-friendly message.

    This function:
    1. Logs the full error details (including sensitive info) for debugging
    2. Returns a sanitized, user-friendly message for display

    Args:
        error: The exception to handle
        context: Optional context about where the error occurred
        log_level: Log level to use ("error", "warning", "info")

    Returns:
        User-friendly error message safe for display
    """
    # Get error classification
    error_code = get_error_code(error)
    sanitized_message = sanitize_error_message(error)

    # Build log message
    log_message = f"[{error_code.value}] {type(error).__name__}: {error}"
    if context:
        log_message = f"{context} - {log_message}"

    # Log full error details
    if log_level == "error":
        logger.error(log_message, exc_info=True)
    elif log_level == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)

    # Return user-friendly message
    return get_user_message(error_code)


def format_validation_errors(errors: list[str]) -> str:
    """
    Format a list of validation errors into a user-friendly message.

    Args:
        errors: List of validation error messages

    Returns:
        Formatted error message
    """
    if not errors:
        return ""
    if len(errors) == 1:
        return errors[0]
    return "Please fix the following issues:\n" + "\n".join(f"- {e}" for e in errors)


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    "ErrorCode",
    "ERROR_MESSAGES",
    "sanitize_error_message",
    "get_error_code",
    "get_user_message",
    "handle_error",
    "format_validation_errors",
]
