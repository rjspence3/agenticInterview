"""
Tests for error handling, validation, and rate limiting functionality.

This module tests:
- Error message sanitization
- Error code classification
- Input validation functions
- Rate limiter behavior
"""

import pytest
import time
from unittest.mock import Mock

# Import modules under test
from error_handling import (
    ErrorCode,
    sanitize_error_message,
    get_error_code,
    get_user_message,
    handle_error,
    format_validation_errors,
)
from validators import (
    validate_required,
    validate_max_length,
    validate_name,
    validate_email,
    sanitize_text,
    sanitize_multiline_text,
    validate_string_list,
    validate_person_form,
    validate_template_form,
    validate_question_form,
    validate_answer,
)
from llm_client import RateLimiter


# ==============================================================================
# Error Handling Tests
# ==============================================================================

class TestErrorSanitization:
    """Test error message sanitization."""

    def test_sanitize_openai_api_key(self):
        """API keys should be redacted from error messages."""
        error = Exception("Invalid API key: sk-abc123xyz456789012345678901234567890")
        sanitized = sanitize_error_message(error)
        assert "sk-abc123xyz456789012345678901234567890" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_anthropic_api_key(self):
        """Anthropic API keys should be redacted."""
        error = Exception("Authentication failed: sk-ant-api123456789012345678901234567890")
        sanitized = sanitize_error_message(error)
        assert "sk-ant-api123456789012345678901234567890" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_file_paths(self):
        """File paths should be redacted."""
        error = Exception("File not found: /Users/john/secrets/config.py")
        sanitized = sanitize_error_message(error)
        assert "/Users/john" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_database_url(self):
        """Database connection strings should be redacted."""
        error = Exception("Connection failed: postgresql://user:pass@localhost/db")
        sanitized = sanitize_error_message(error)
        assert "postgresql://" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_preserve_safe_messages(self):
        """Safe error messages should be preserved."""
        error = Exception("Invalid input: name is required")
        sanitized = sanitize_error_message(error)
        assert "Invalid input: name is required" in sanitized


class TestErrorCodeClassification:
    """Test error code classification."""

    def test_rate_limit_error(self):
        """Rate limit errors should be classified correctly."""
        error = Exception("Rate limit exceeded")
        assert get_error_code(error) == ErrorCode.LLM_RATE_LIMIT

    def test_authentication_error(self):
        """Authentication errors should be classified correctly."""
        error = Exception("Invalid API key")
        assert get_error_code(error) == ErrorCode.LLM_INVALID_KEY

    def test_timeout_error(self):
        """Timeout errors should be classified correctly."""
        error = Exception("Request timeout")
        assert get_error_code(error) == ErrorCode.LLM_TIMEOUT

    def test_not_found_error(self):
        """Not found errors should be classified correctly."""
        error = Exception("Item not found")
        assert get_error_code(error) == ErrorCode.DB_NOT_FOUND

    def test_validation_error(self):
        """Validation errors should be classified correctly."""
        error = Exception("Invalid format")
        assert get_error_code(error) == ErrorCode.VALIDATION_ERROR

    def test_unknown_error(self):
        """Unknown errors should be classified as UNKNOWN_ERROR."""
        error = Exception("Some random error")
        assert get_error_code(error) == ErrorCode.UNKNOWN_ERROR


class TestUserMessages:
    """Test user-friendly error messages."""

    def test_get_user_message_for_rate_limit(self):
        """Rate limit should have user-friendly message."""
        message = get_user_message(ErrorCode.LLM_RATE_LIMIT)
        assert "wait" in message.lower() or "too many" in message.lower()

    def test_get_user_message_for_api_error(self):
        """API error should have user-friendly message."""
        message = get_user_message(ErrorCode.LLM_API_ERROR)
        assert "unavailable" in message.lower() or "later" in message.lower()

    def test_get_user_message_for_unknown(self):
        """Unknown error should have generic message."""
        message = get_user_message(ErrorCode.UNKNOWN_ERROR)
        assert "unexpected" in message.lower() or "error" in message.lower()


class TestHandleError:
    """Test the handle_error function."""

    def test_handle_error_returns_user_message(self):
        """handle_error should return user-friendly message."""
        error = Exception("Rate limit exceeded")
        message = handle_error(error, context="Test context", log_level="warning")
        # Should return rate limit message
        assert "wait" in message.lower() or "too many" in message.lower()

    def test_format_validation_errors_single(self):
        """Single validation error should be returned as-is."""
        errors = ["Name is required"]
        result = format_validation_errors(errors)
        assert result == "Name is required"

    def test_format_validation_errors_multiple(self):
        """Multiple errors should be formatted as list."""
        errors = ["Name is required", "Email is invalid"]
        result = format_validation_errors(errors)
        assert "Name is required" in result
        assert "Email is invalid" in result
        assert "-" in result  # Should have bullet points


# ==============================================================================
# Validation Tests
# ==============================================================================

class TestBasicValidation:
    """Test basic validation functions."""

    def test_validate_required_with_value(self):
        """Non-empty value should pass validation."""
        is_valid, error = validate_required("test", "Field")
        assert is_valid is True
        assert error == ""

    def test_validate_required_with_none(self):
        """None should fail validation."""
        is_valid, error = validate_required(None, "Field")
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_required_with_empty_string(self):
        """Empty string should fail validation."""
        is_valid, error = validate_required("", "Field")
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_required_with_whitespace(self):
        """Whitespace-only string should fail validation."""
        is_valid, error = validate_required("   ", "Field")
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_max_length_within_limit(self):
        """String within limit should pass."""
        is_valid, error = validate_max_length("test", 10, "Field")
        assert is_valid is True
        assert error == ""

    def test_validate_max_length_exceeds_limit(self):
        """String exceeding limit should fail."""
        is_valid, error = validate_max_length("a" * 101, 100, "Field")
        assert is_valid is False
        assert "100" in error


class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Valid email should pass."""
        is_valid, error = validate_email("test@example.com")
        assert is_valid is True
        assert error == ""

    def test_invalid_email_no_at(self):
        """Email without @ should fail."""
        is_valid, error = validate_email("testexample.com")
        assert is_valid is False
        assert "valid email" in error.lower()

    def test_invalid_email_no_domain(self):
        """Email without domain should fail."""
        is_valid, error = validate_email("test@")
        assert is_valid is False
        assert "valid email" in error.lower()

    def test_email_optional_empty(self):
        """Empty email should pass when not required."""
        is_valid, error = validate_email("", required=False)
        assert is_valid is True
        assert error == ""

    def test_email_required_empty(self):
        """Empty email should fail when required."""
        is_valid, error = validate_email("", required=True)
        assert is_valid is False
        assert "required" in error.lower()


class TestSanitization:
    """Test text sanitization functions."""

    def test_sanitize_text_strips_whitespace(self):
        """Sanitize should strip leading/trailing whitespace."""
        result = sanitize_text("  test  ")
        assert result == "test"

    def test_sanitize_text_escapes_html(self):
        """Sanitize should escape HTML special chars."""
        result = sanitize_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_text_normalizes_whitespace(self):
        """Sanitize should collapse multiple spaces."""
        result = sanitize_text("hello    world")
        assert result == "hello world"

    def test_sanitize_multiline_preserves_newlines(self):
        """Multiline sanitize should preserve newlines."""
        result = sanitize_multiline_text("line1\nline2")
        assert "\n" in result


class TestFormValidation:
    """Test form validation functions."""

    def test_validate_person_form_valid(self):
        """Valid person form should pass."""
        is_valid, error = validate_person_form(
            name="John Doe",
            email="john@example.com",
            role="Developer",
            department="Engineering"
        )
        assert is_valid is True
        assert error == ""

    def test_validate_person_form_missing_name(self):
        """Missing name should fail."""
        is_valid, error = validate_person_form(
            name="",
            email="john@example.com"
        )
        assert is_valid is False
        assert "name" in error.lower()

    def test_validate_person_form_invalid_email(self):
        """Invalid email should fail."""
        is_valid, error = validate_person_form(
            name="John",
            email="invalid-email"
        )
        assert is_valid is False
        assert "email" in error.lower()

    def test_validate_template_form_valid(self):
        """Valid template form should pass."""
        is_valid, error = validate_template_form(
            name="Technical Interview",
            description="A standard technical interview template"
        )
        assert is_valid is True
        assert error == ""

    def test_validate_template_form_missing_name(self):
        """Missing template name should fail."""
        is_valid, error = validate_template_form(name="")
        assert is_valid is False

    def test_validate_question_form_valid(self):
        """Valid question form should pass."""
        is_valid, error = validate_question_form(
            question_text="What is recursion?",
            competency="Python",
            difficulty="Medium",
            keypoints=["base case", "recursive case"]
        )
        assert is_valid is True
        assert error == ""

    def test_validate_question_form_missing_text(self):
        """Missing question text should fail."""
        is_valid, error = validate_question_form(
            question_text="",
            competency="Python",
            difficulty="Medium",
            keypoints=[]
        )
        assert is_valid is False

    def test_validate_answer_valid(self):
        """Valid answer should pass."""
        is_valid, error = validate_answer("This is my answer to the question.")
        assert is_valid is True
        assert error == ""

    def test_validate_answer_empty(self):
        """Empty answer should fail."""
        is_valid, error = validate_answer("")
        assert is_valid is False
        assert "required" in error.lower()


# ==============================================================================
# Rate Limiter Tests
# ==============================================================================

class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_initial_state_allows_calls(self):
        """Fresh rate limiter should allow calls."""
        limiter = RateLimiter(max_calls_per_session=10, max_calls_per_minute=5)
        allowed, error = limiter.check_rate_limit()
        assert allowed is True
        assert error == ""

    def test_session_limit_enforcement(self):
        """Session limit should be enforced."""
        limiter = RateLimiter(max_calls_per_session=3, max_calls_per_minute=100)

        # Make 3 calls
        for _ in range(3):
            limiter.record_call()

        # 4th call should be blocked
        allowed, error = limiter.check_rate_limit()
        assert allowed is False
        assert "session limit" in error.lower()

    def test_minute_limit_enforcement(self):
        """Minute limit should be enforced."""
        limiter = RateLimiter(max_calls_per_session=100, max_calls_per_minute=2)

        # Make 2 calls
        for _ in range(2):
            limiter.record_call()

        # 3rd call should be blocked
        allowed, error = limiter.check_rate_limit()
        assert allowed is False
        assert "rate limit" in error.lower()

    def test_session_reset(self):
        """Session reset should clear session counter."""
        limiter = RateLimiter(max_calls_per_session=2, max_calls_per_minute=100)

        # Use up session limit
        limiter.record_call()
        limiter.record_call()

        # Should be blocked
        allowed, _ = limiter.check_rate_limit()
        assert allowed is False

        # Reset session
        limiter.reset_session()

        # Should be allowed again
        allowed, _ = limiter.check_rate_limit()
        assert allowed is True

    def test_get_usage_stats(self):
        """Usage stats should reflect actual usage."""
        limiter = RateLimiter(max_calls_per_session=10, max_calls_per_minute=5)

        limiter.record_call()
        limiter.record_call()

        stats = limiter.get_usage_stats()
        assert stats["session_calls"] == 2
        assert stats["session_limit"] == 10
        assert stats["session_remaining"] == 8
        assert stats["minute_calls"] == 2
        assert stats["minute_limit"] == 5
        assert stats["minute_remaining"] == 3
