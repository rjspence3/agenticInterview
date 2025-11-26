"""
Input validation functions for the Agentic Interview System.

This module provides reusable validators for form inputs, API payloads,
and configuration data. All validators return (is_valid, error_message) tuples.
"""

import re
import html
from typing import Tuple, List, Any, Optional

from constants import (
    MAX_NAME_LENGTH,
    MAX_EMAIL_LENGTH,
    MAX_ROLE_LENGTH,
    MAX_DEPARTMENT_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_QUESTION_TEXT_LENGTH,
    MAX_KEYPOINT_LENGTH,
    MAX_TAG_LENGTH,
    MAX_ANSWER_LENGTH,
    MAX_CRITERION_NAME_LENGTH,
    MAX_CRITERION_DEFINITION_LENGTH,
    MAX_CRITERIA_COUNT,
)


# ==============================================================================
# Text Validation
# ==============================================================================

def validate_required(value: Any, field_name: str = "Field") -> Tuple[bool, str]:
    """
    Validate that a value is not None or empty.

    Args:
        value: The value to check
        field_name: Name of the field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"
    if isinstance(value, str) and not value.strip():
        return False, f"{field_name} is required"
    return True, ""


def validate_max_length(
    value: str,
    max_length: int,
    field_name: str = "Field"
) -> Tuple[bool, str]:
    """
    Validate that a string doesn't exceed maximum length.

    Args:
        value: The string to check
        max_length: Maximum allowed length
        field_name: Name of the field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value and len(value) > max_length:
        return False, f"{field_name} must be {max_length} characters or less"
    return True, ""


def validate_name(name: str, field_name: str = "Name") -> Tuple[bool, str]:
    """
    Validate a name field (person name, template name, etc.).

    Args:
        name: The name to validate
        field_name: Name of the field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error = validate_required(name, field_name)
    if not is_valid:
        return is_valid, error

    is_valid, error = validate_max_length(name, MAX_NAME_LENGTH, field_name)
    if not is_valid:
        return is_valid, error

    return True, ""


# ==============================================================================
# Email Validation
# ==============================================================================

# Basic email regex pattern (not exhaustive but catches most issues)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_email(email: str, required: bool = True) -> Tuple[bool, str]:
    """
    Validate an email address.

    Args:
        email: The email to validate
        required: Whether the email is required

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not email.strip():
        if required:
            return False, "Email is required"
        return True, ""  # Empty is OK if not required

    email = email.strip()

    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email must be {MAX_EMAIL_LENGTH} characters or less"

    if not EMAIL_PATTERN.match(email):
        return False, "Please enter a valid email address"

    return True, ""


# ==============================================================================
# Text Sanitization
# ==============================================================================

def sanitize_text(text: str) -> str:
    """
    Sanitize text input to prevent XSS and clean up whitespace.

    Args:
        text: The text to sanitize

    Returns:
        Sanitized text string
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # HTML escape special characters to prevent XSS
    text = html.escape(text)

    # Normalize internal whitespace (collapse multiple spaces)
    text = ' '.join(text.split())

    return text


def sanitize_multiline_text(text: str) -> str:
    """
    Sanitize multiline text (preserves newlines but escapes HTML).

    Args:
        text: The multiline text to sanitize

    Returns:
        Sanitized text string
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # HTML escape special characters
    text = html.escape(text)

    return text


# ==============================================================================
# List/Array Validation
# ==============================================================================

def validate_string_list(
    items: List[str],
    max_item_length: int,
    max_items: int = 100,
    field_name: str = "List"
) -> Tuple[bool, str]:
    """
    Validate a list of strings.

    Args:
        items: List of strings to validate
        max_item_length: Maximum length for each item
        max_items: Maximum number of items allowed
        field_name: Name of the field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(items, list):
        return False, f"{field_name} must be a list"

    if len(items) > max_items:
        return False, f"{field_name} cannot have more than {max_items} items"

    for i, item in enumerate(items):
        if not isinstance(item, str):
            return False, f"{field_name} item {i+1} must be a string"
        if len(item) > max_item_length:
            return False, f"{field_name} item {i+1} exceeds maximum length of {max_item_length}"

    return True, ""


def validate_tags(tags: List[str]) -> Tuple[bool, str]:
    """
    Validate a list of tags.

    Args:
        tags: List of tag strings

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_string_list(tags, MAX_TAG_LENGTH, max_items=20, field_name="Tags")


def validate_keypoints(keypoints: List[str]) -> Tuple[bool, str]:
    """
    Validate a list of keypoints for a question.

    Args:
        keypoints: List of keypoint strings

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_string_list(keypoints, MAX_KEYPOINT_LENGTH, max_items=20, field_name="Keypoints")


# ==============================================================================
# Form Field Validators (for Admin forms)
# ==============================================================================

def validate_person_form(
    name: str,
    email: str,
    role: Optional[str] = None,
    department: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Validate all fields for a Person form.

    Args:
        name: Person's name
        email: Person's email
        role: Optional role
        department: Optional department
        tags: Optional list of tags

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate required fields
    is_valid, error = validate_name(name, "Name")
    if not is_valid:
        return is_valid, error

    is_valid, error = validate_email(email)
    if not is_valid:
        return is_valid, error

    # Validate optional fields
    if role:
        is_valid, error = validate_max_length(role, MAX_ROLE_LENGTH, "Role")
        if not is_valid:
            return is_valid, error

    if department:
        is_valid, error = validate_max_length(department, MAX_DEPARTMENT_LENGTH, "Department")
        if not is_valid:
            return is_valid, error

    if tags:
        is_valid, error = validate_tags(tags)
        if not is_valid:
            return is_valid, error

    return True, ""


def validate_template_form(
    name: str,
    description: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate fields for an InterviewTemplate form.

    Args:
        name: Template name
        description: Optional description

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error = validate_name(name, "Template name")
    if not is_valid:
        return is_valid, error

    if description:
        is_valid, error = validate_max_length(description, MAX_DESCRIPTION_LENGTH, "Description")
        if not is_valid:
            return is_valid, error

    return True, ""


def validate_question_form(
    question_text: str,
    competency: str,
    difficulty: str,
    keypoints: List[str]
) -> Tuple[bool, str]:
    """
    Validate fields for a TemplateQuestion form.

    Args:
        question_text: The question text
        competency: Competency area
        difficulty: Difficulty level
        keypoints: List of keypoints

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error = validate_required(question_text, "Question text")
    if not is_valid:
        return is_valid, error

    is_valid, error = validate_max_length(question_text, MAX_QUESTION_TEXT_LENGTH, "Question text")
    if not is_valid:
        return is_valid, error

    is_valid, error = validate_required(competency, "Competency")
    if not is_valid:
        return is_valid, error

    is_valid, error = validate_required(difficulty, "Difficulty")
    if not is_valid:
        return is_valid, error

    # Keypoints can be empty but if provided must be valid
    if keypoints:
        is_valid, error = validate_keypoints(keypoints)
        if not is_valid:
            return is_valid, error

    return True, ""


def validate_answer(answer: str) -> Tuple[bool, str]:
    """
    Validate a candidate's answer.

    Args:
        answer: The answer text

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error = validate_required(answer, "Answer")
    if not is_valid:
        return is_valid, error

    is_valid, error = validate_max_length(answer, MAX_ANSWER_LENGTH, "Answer")
    if not is_valid:
        return is_valid, error

    return True, ""


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    # Basic validators
    "validate_required",
    "validate_max_length",
    "validate_name",
    "validate_email",
    # Sanitization
    "sanitize_text",
    "sanitize_multiline_text",
    # List validators
    "validate_string_list",
    "validate_tags",
    "validate_keypoints",
    # Form validators
    "validate_person_form",
    "validate_template_form",
    "validate_question_form",
    "validate_answer",
]
