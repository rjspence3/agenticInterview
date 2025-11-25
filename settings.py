"""
Configuration settings for Agentic Interview System.

Loads configuration from environment variables (via .env file or system env).
Provides validation and defaults for LLM integration.
"""

import os
from typing import Tuple
from dotenv import load_dotenv

# Load .env file if it exists (for local development)
# In production, use system environment variables instead
load_dotenv()

# ==============================================================================
# LLM Provider Configuration
# ==============================================================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# ==============================================================================
# API Keys
# ==============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ==============================================================================
# Model Selection
# ==============================================================================

# Default models for each provider
DEFAULT_OPENAI_MODEL = "gpt-4"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# Get model from env or use provider-specific default
LLM_MODEL = os.getenv("LLM_MODEL")
if not LLM_MODEL:
    if LLM_PROVIDER == "openai":
        LLM_MODEL = DEFAULT_OPENAI_MODEL
    elif LLM_PROVIDER == "anthropic":
        LLM_MODEL = DEFAULT_ANTHROPIC_MODEL
    else:
        LLM_MODEL = DEFAULT_OPENAI_MODEL  # Fallback

# ==============================================================================
# Generation Parameters
# ==============================================================================

# Temperature: 0.0-1.0 (lower = more deterministic)
try:
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    # Clamp to valid range
    LLM_TEMPERATURE = max(0.0, min(1.0, LLM_TEMPERATURE))
except (ValueError, TypeError):
    LLM_TEMPERATURE = 0.3
    print("Warning: Invalid LLM_TEMPERATURE, using default 0.3")

# API timeout in seconds
try:
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
except (ValueError, TypeError):
    LLM_TIMEOUT = 30
    print("Warning: Invalid LLM_TIMEOUT, using default 30")

# Max retry attempts for transient failures
try:
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
except (ValueError, TypeError):
    LLM_MAX_RETRIES = 2
    print("Warning: Invalid LLM_MAX_RETRIES, using default 2")

# ==============================================================================
# Validation Functions
# ==============================================================================

def validate_llm_config() -> Tuple[bool, str]:
    """
    Validate LLM configuration.

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, "")
        If invalid: (False, "Error description")
    """
    # Check provider is valid
    valid_providers = ["openai", "anthropic", "mock"]
    if LLM_PROVIDER not in valid_providers:
        return False, f"Invalid LLM_PROVIDER '{LLM_PROVIDER}'. Must be one of: {valid_providers}"

    # Check API key is configured for the selected provider
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-openai-key-here":
            return False, "OpenAI API key not configured. Set OPENAI_API_KEY in .env file."
    elif LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "sk-ant-your-anthropic-key-here":
            return False, "Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env file."
    # "mock" provider doesn't need API key

    # All checks passed
    return True, ""

def get_api_key_for_provider(provider: str) -> str:
    """
    Get the API key for the specified provider.

    Args:
        provider: "openai" or "anthropic"

    Returns:
        API key string

    Raises:
        ValueError: If provider is unknown or API key not configured
    """
    if provider == "openai":
        if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-openai-key-here":
            raise ValueError("OpenAI API key not configured")
        return OPENAI_API_KEY
    elif provider == "anthropic":
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "sk-ant-your-anthropic-key-here":
            raise ValueError("Anthropic API key not configured")
        return ANTHROPIC_API_KEY
    elif provider == "mock":
        return "mock-key"  # Mock doesn't need real key
    else:
        raise ValueError(f"Unknown provider: {provider}")

def print_config_summary():
    """Print current configuration (without exposing API keys)."""
    print("=" * 60)
    print("LLM Configuration Summary")
    print("=" * 60)
    print(f"Provider: {LLM_PROVIDER}")
    print(f"Model: {LLM_MODEL}")
    print(f"Temperature: {LLM_TEMPERATURE}")
    print(f"Timeout: {LLM_TIMEOUT}s")
    print(f"Max Retries: {LLM_MAX_RETRIES}")

    # Show API key status (not the actual key!)
    if LLM_PROVIDER == "openai":
        status = "✓ Configured" if OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-openai-key-here" else "✗ Not configured"
        print(f"OpenAI API Key: {status}")
    elif LLM_PROVIDER == "anthropic":
        status = "✓ Configured" if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "sk-ant-your-anthropic-key-here" else "✗ Not configured"
        print(f"Anthropic API Key: {status}")

    is_valid, error = validate_llm_config()
    print(f"Configuration Valid: {'✓ Yes' if is_valid else '✗ No'}")
    if error:
        print(f"Error: {error}")
    print("=" * 60)

# ==============================================================================
# Module-level validation (optional, for debugging)
# ==============================================================================

if __name__ == "__main__":
    # When run directly, print config summary
    print_config_summary()
