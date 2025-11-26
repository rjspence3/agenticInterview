"""
Centralized constants for the Agentic Interview System.

This module contains all magic numbers, thresholds, and configuration values
that were previously hardcoded throughout the codebase.
"""

# ==============================================================================
# Scoring Thresholds
# ==============================================================================

# Mastery level thresholds (0-100 scale)
MASTERY_STRONG_THRESHOLD = 80  # Score >= 80 = "strong"
MASTERY_MIXED_THRESHOLD = 50   # Score >= 50 = "mixed", below = "weak"

# Overall performance assessment thresholds
PERFORMANCE_EXCELLENT_THRESHOLD = 80
PERFORMANCE_SOLID_THRESHOLD = 60
PERFORMANCE_BASIC_THRESHOLD = 40

# ==============================================================================
# LLM Settings
# ==============================================================================

# Default max tokens for LLM responses
DEFAULT_MAX_TOKENS = 1500

# Default rate limiting settings
DEFAULT_LLM_MAX_CALLS_PER_SESSION = 50
DEFAULT_LLM_MAX_CALLS_PER_MINUTE = 10

# ==============================================================================
# Input Validation Limits
# ==============================================================================

# Maximum lengths for text fields
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254  # RFC 5321 limit
MAX_ROLE_LENGTH = 100
MAX_DEPARTMENT_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_QUESTION_TEXT_LENGTH = 2000
MAX_KEYPOINT_LENGTH = 500
MAX_TAG_LENGTH = 50
MAX_ANSWER_LENGTH = 10000

# Lens configuration limits
MAX_CRITERION_NAME_LENGTH = 50
MAX_CRITERION_DEFINITION_LENGTH = 500
MAX_CRITERIA_COUNT = 20

# ==============================================================================
# UI Constants
# ==============================================================================

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Chart dimensions
CHART_HEIGHT = 400

# ==============================================================================
# Database Constants
# ==============================================================================

# Default organization name
DEFAULT_ORGANIZATION_NAME = "Default Organization"

# ==============================================================================
# Session Status Values
# ==============================================================================

SESSION_STATUS_IN_PROGRESS = "in_progress"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_ABANDONED = "abandoned"

# ==============================================================================
# Mastery Labels
# ==============================================================================

MASTERY_LABEL_STRONG = "strong"
MASTERY_LABEL_MIXED = "mixed"
MASTERY_LABEL_WEAK = "weak"

# ==============================================================================
# Evaluator Types
# ==============================================================================

EVALUATOR_TYPE_HEURISTIC = "heuristic"
EVALUATOR_TYPE_LLM = "llm"

# ==============================================================================
# Error Messages (User-Facing)
# ==============================================================================

ERROR_INVALID_EMAIL = "Please enter a valid email address"
ERROR_NAME_TOO_LONG = f"Name must be {MAX_NAME_LENGTH} characters or less"
ERROR_REQUIRED_FIELD = "This field is required"
ERROR_LLM_UNAVAILABLE = "AI evaluation is temporarily unavailable. Please try again later."
ERROR_RATE_LIMIT_EXCEEDED = "Too many requests. Please wait a moment before trying again."
ERROR_SESSION_NOT_FOUND = "Interview session not found"
ERROR_INVALID_CONFIG = "Invalid configuration. Please check your settings."

# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    # Scoring thresholds
    "MASTERY_STRONG_THRESHOLD",
    "MASTERY_MIXED_THRESHOLD",
    "PERFORMANCE_EXCELLENT_THRESHOLD",
    "PERFORMANCE_SOLID_THRESHOLD",
    "PERFORMANCE_BASIC_THRESHOLD",
    # LLM settings
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_LLM_MAX_CALLS_PER_SESSION",
    "DEFAULT_LLM_MAX_CALLS_PER_MINUTE",
    # Input limits
    "MAX_NAME_LENGTH",
    "MAX_EMAIL_LENGTH",
    "MAX_ROLE_LENGTH",
    "MAX_DEPARTMENT_LENGTH",
    "MAX_DESCRIPTION_LENGTH",
    "MAX_QUESTION_TEXT_LENGTH",
    "MAX_KEYPOINT_LENGTH",
    "MAX_TAG_LENGTH",
    "MAX_ANSWER_LENGTH",
    "MAX_CRITERION_NAME_LENGTH",
    "MAX_CRITERION_DEFINITION_LENGTH",
    "MAX_CRITERIA_COUNT",
    # UI constants
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "CHART_HEIGHT",
    # Database constants
    "DEFAULT_ORGANIZATION_NAME",
    # Status values
    "SESSION_STATUS_IN_PROGRESS",
    "SESSION_STATUS_COMPLETED",
    "SESSION_STATUS_ABANDONED",
    # Mastery labels
    "MASTERY_LABEL_STRONG",
    "MASTERY_LABEL_MIXED",
    "MASTERY_LABEL_WEAK",
    # Evaluator types
    "EVALUATOR_TYPE_HEURISTIC",
    "EVALUATOR_TYPE_LLM",
    # Error messages
    "ERROR_INVALID_EMAIL",
    "ERROR_NAME_TOO_LONG",
    "ERROR_REQUIRED_FIELD",
    "ERROR_LLM_UNAVAILABLE",
    "ERROR_RATE_LIMIT_EXCEEDED",
    "ERROR_SESSION_NOT_FOUND",
    "ERROR_INVALID_CONFIG",
]
