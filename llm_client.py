"""
LLM Client Abstraction Layer

Provides a unified interface for calling different LLM providers (OpenAI, Anthropic).
Includes retry logic, error handling, and a mock client for testing.
"""

import time
import json
from typing import Protocol
from functools import wraps
from logging_config import get_logger

logger = get_logger(__name__)


# ==============================================================================
# Base Protocol
# ==============================================================================

class LLMClient(Protocol):
    """
    Protocol defining the interface for all LLM clients.

    All implementations must provide the call_llm method.
    """

    def call_llm(self, prompt: str, model: str, temperature: float, timeout: int = 30) -> str:
        """
        Call the LLM and return the response text.

        Args:
            prompt: The prompt to send to the LLM
            model: Model identifier (e.g., "gpt-4", "claude-3-5-sonnet-20241022")
            temperature: 0.0-1.0, controls randomness
            timeout: Request timeout in seconds

        Returns:
            Response text from the LLM

        Raises:
            Various exceptions depending on failure type
        """
        ...


# ==============================================================================
# Rate Limiter
# ==============================================================================

class RateLimiter:
    """
    Simple rate limiter to prevent excessive API calls.

    Tracks calls per session and per minute to prevent cost overruns.
    """

    def __init__(
        self,
        max_calls_per_session: int = 50,
        max_calls_per_minute: int = 10
    ):
        """
        Initialize the rate limiter.

        Args:
            max_calls_per_session: Maximum total calls allowed per session
            max_calls_per_minute: Maximum calls allowed per minute
        """
        self.max_calls_per_session = max_calls_per_session
        self.max_calls_per_minute = max_calls_per_minute
        self.session_calls = 0
        self.minute_calls: list[float] = []  # Timestamps of calls in current minute

    def check_rate_limit(self) -> tuple[bool, str]:
        """
        Check if a call is allowed under current rate limits.

        Returns:
            Tuple of (is_allowed, error_message)
        """
        current_time = time.time()

        # Clean up old minute calls (older than 60 seconds)
        self.minute_calls = [t for t in self.minute_calls if current_time - t < 60]

        # Check session limit
        if self.session_calls >= self.max_calls_per_session:
            return False, f"Session limit reached ({self.max_calls_per_session} calls). Please start a new session."

        # Check minute limit
        if len(self.minute_calls) >= self.max_calls_per_minute:
            wait_time = 60 - (current_time - self.minute_calls[0])
            return False, f"Rate limit reached. Please wait {wait_time:.0f} seconds."

        return True, ""

    def record_call(self):
        """Record that a call was made."""
        self.session_calls += 1
        self.minute_calls.append(time.time())
        logger.debug(f"Rate limiter: session_calls={self.session_calls}, minute_calls={len(self.minute_calls)}")

    def reset_session(self):
        """Reset session call counter (e.g., when starting new interview)."""
        self.session_calls = 0
        logger.info("Rate limiter: session reset")

    def get_usage_stats(self) -> dict:
        """Get current usage statistics."""
        current_time = time.time()
        self.minute_calls = [t for t in self.minute_calls if current_time - t < 60]
        return {
            "session_calls": self.session_calls,
            "session_limit": self.max_calls_per_session,
            "minute_calls": len(self.minute_calls),
            "minute_limit": self.max_calls_per_minute,
            "session_remaining": self.max_calls_per_session - self.session_calls,
            "minute_remaining": self.max_calls_per_minute - len(self.minute_calls),
        }


# Global rate limiter instance (can be configured at startup)
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        # Try to get limits from settings
        try:
            import settings
            _rate_limiter = RateLimiter(
                max_calls_per_session=getattr(settings, 'LLM_MAX_CALLS_PER_SESSION', 50),
                max_calls_per_minute=getattr(settings, 'LLM_MAX_CALLS_PER_MINUTE', 10)
            )
        except ImportError:
            _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter():
    """Reset the global rate limiter (e.g., for new session)."""
    limiter = get_rate_limiter()
    limiter.reset_session()


# ==============================================================================
# Retry Decorator
# ==============================================================================

def retry_on_failure(max_retries: int = 2, delay: float = 1.0):
    """
    Decorator to retry function calls on transient failures.

    Args:
        max_retries: Number of retry attempts (default 2)
        delay: Initial delay between retries in seconds (uses exponential backoff)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_name = type(e).__name__

                    # Only retry on transient errors
                    retryable_errors = [
                        "RateLimitError",
                        "APIConnectionError",
                        "Timeout",
                        "InternalServerError",
                        "ServiceUnavailableError"
                    ]

                    if error_name not in retryable_errors or attempt == max_retries:
                        logger.error(f"LLM call failed after {attempt + 1} attempts: {error_name}: {str(e)}")
                        raise  # Don't retry, re-raise immediately

                    # Exponential backoff
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Retrying after {wait_time}s due to {error_name} (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)

            # Should not reach here, but just in case
            raise last_exception
        return wrapper
    return decorator


# ==============================================================================
# OpenAI Client
# ==============================================================================

class OpenAIClient:
    """
    Client for OpenAI's GPT models (GPT-4, GPT-3.5-turbo, etc.).
    """

    def __init__(self, api_key: str):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (starts with 'sk-')
        """
        try:
            import openai
            self.openai = openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Run: pip install openai"
            )

    @retry_on_failure(max_retries=2, delay=1.0)
    def call_llm(self, prompt: str, model: str, temperature: float, timeout: int = 30) -> str:
        """
        Call OpenAI API and return response.

        Args:
            prompt: The prompt to send
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            temperature: 0.0-1.0
            timeout: Request timeout in seconds

        Returns:
            Response text

        Raises:
            openai.AuthenticationError: Invalid API key
            openai.RateLimitError: Rate limit exceeded
            openai.APIConnectionError: Network error
            openai.APIError: Other API errors
        """
        logger.info(f"Calling OpenAI API: model={model}, temperature={temperature}, prompt_length={len(prompt)}")
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical interviewer evaluating candidate answers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=1500,  # Enough for detailed evaluation JSON
                timeout=timeout
            )

            response_text = response.choices[0].message.content
            elapsed_time = time.time() - start_time
            logger.info(f"OpenAI API call succeeded: model={model}, elapsed={elapsed_time:.2f}s, response_length={len(response_text)}")

            return response_text

        except self.openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise ValueError(f"Invalid OpenAI API key: {e}")
        except self.openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit error: {str(e)}")
            # Retry logic will handle this
            raise
        except self.openai.APIConnectionError as e:
            logger.error(f"OpenAI connection error: {str(e)}")
            raise ConnectionError(f"Network error connecting to OpenAI: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {e}")


# ==============================================================================
# Anthropic Client
# ==============================================================================

class AnthropicClient:
    """
    Client for Anthropic's Claude models.
    """

    def __init__(self, api_key: str):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (starts with 'sk-ant-')
        """
        try:
            import anthropic
            self.anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError(
                "Anthropic library not installed. Run: pip install anthropic"
            )

    @retry_on_failure(max_retries=2, delay=1.0)
    def call_llm(self, prompt: str, model: str, temperature: float, timeout: int = 30) -> str:
        """
        Call Anthropic API and return response.

        Args:
            prompt: The prompt to send
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            temperature: 0.0-1.0
            timeout: Request timeout in seconds

        Returns:
            Response text

        Raises:
            anthropic.AuthenticationError: Invalid API key
            anthropic.RateLimitError: Rate limit exceeded
            anthropic.APIConnectionError: Network error
            anthropic.APIError: Other API errors
        """
        logger.info(f"Calling Anthropic API: model={model}, temperature={temperature}, prompt_length={len(prompt)}")
        start_time = time.time()

        try:
            # Anthropic uses a system parameter separately, not in messages
            message = self.client.messages.create(
                model=model,
                max_tokens=1500,
                temperature=temperature,
                timeout=timeout,
                system="You are an expert technical interviewer evaluating candidate answers.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text from response
            response_text = message.content[0].text
            elapsed_time = time.time() - start_time
            logger.info(f"Anthropic API call succeeded: model={model}, elapsed={elapsed_time:.2f}s, response_length={len(response_text)}")

            return response_text

        except self.anthropic.AuthenticationError as e:
            logger.error(f"Anthropic authentication error: {str(e)}")
            raise ValueError(f"Invalid Anthropic API key: {e}")
        except self.anthropic.RateLimitError as e:
            logger.warning(f"Anthropic rate limit error: {str(e)}")
            # Retry logic will handle this
            raise
        except self.anthropic.APIConnectionError as e:
            logger.error(f"Anthropic connection error: {str(e)}")
            raise ConnectionError(f"Network error connecting to Anthropic: {e}")
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise RuntimeError(f"Anthropic API error: {e}")


# ==============================================================================
# Mock Client (for testing)
# ==============================================================================

class MockLLMClient:
    """
    Mock LLM client for testing without API calls.

    Returns realistic-looking evaluation JSON based on keywords in the prompt.
    No network calls, no API costs, instant responses.
    """

    def call_llm(self, prompt: str, model: str, temperature: float, timeout: int = 30) -> str:
        """
        Return mock response based on prompt content.

        Analyzes prompt to determine if it's a perfect/partial/weak answer
        and returns appropriate evaluation JSON.
        """
        # Extract keypoints from prompt (simple heuristic)
        keypoints = []
        if "GROUND TRUTH KEYPOINTS" in prompt:
            lines = prompt.split("\n")
            in_keypoints = False
            for line in lines:
                if "GROUND TRUTH KEYPOINTS" in line:
                    in_keypoints = True
                    continue
                if in_keypoints and line.strip() and line[0].isdigit():
                    # Extract keypoint text (remove numbering)
                    kp = line.split(".", 1)[-1].strip()
                    keypoints.append(kp)
                elif in_keypoints and "CANDIDATE'S ANSWER" in line:
                    break

        # Extract answer from prompt
        answer = ""
        if "CANDIDATE'S ANSWER:" in prompt:
            answer = prompt.split("CANDIDATE'S ANSWER:")[-1].strip()
            # Remove any trailing instructions
            if "TASK:" in answer:
                answer = answer.split("TASK:")[0].strip()

        # Determine answer quality based on keyword matching
        answer_lower = answer.lower()
        matched_count = 0
        coverage = []

        for kp in keypoints:
            # Simple substring matching (same as heuristic evaluator)
            kp_lower = kp.lower()
            matched = kp_lower in answer_lower

            if matched:
                matched_count += 1
                # Find a snippet as evidence
                idx = answer_lower.find(kp_lower)
                evidence = answer[max(0, idx-10):min(len(answer), idx+len(kp)+10)]
                coverage.append({
                    "keypoint": kp,
                    "covered": True,
                    "evidence": f"'{evidence.strip()}'"
                })
            else:
                coverage.append({
                    "keypoint": kp,
                    "covered": False,
                    "evidence": "Not mentioned in answer"
                })

        # Calculate score
        if keypoints:
            score = int((matched_count / len(keypoints)) * 100)
        else:
            score = 50  # Default if no keypoints

        # Determine mastery label
        if score >= 80:
            mastery = "strong"
            feedback = f"Excellent answer covering {matched_count}/{len(keypoints)} key concepts clearly."
            followup = ""
        elif score >= 50:
            mastery = "mixed"
            missed = len(keypoints) - matched_count
            feedback = f"Partial understanding demonstrated. Covered {matched_count}/{len(keypoints)} keypoints but missed {missed}."
            followup = f"Can you explain {keypoints[matched_count] if matched_count < len(keypoints) else 'the remaining concepts'} in more detail?"
        else:
            mastery = "weak"
            feedback = f"Significant gaps in understanding. Only covered {matched_count}/{len(keypoints)} essential keypoints."
            followup = f"Let's start with the fundamentals: {keypoints[0] if keypoints else 'the basic concepts'}?"

        # Build JSON response
        response = {
            "keypoints_coverage": coverage,
            "score": score,
            "mastery_label": mastery,
            "feedback": feedback,
            "suggested_followup": followup
        }

        return json.dumps(response, indent=2)


# ==============================================================================
# Factory Function
# ==============================================================================

def get_llm_client(provider: str, api_key: str) -> LLMClient:
    """
    Factory function to create the appropriate LLM client.

    Args:
        provider: "openai", "anthropic", or "mock"
        api_key: API key for the provider (not needed for "mock")

    Returns:
        LLMClient instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider == "openai":
        return OpenAIClient(api_key)
    elif provider == "anthropic":
        return AnthropicClient(api_key)
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Must be 'openai', 'anthropic', or 'mock'."
        )


# ==============================================================================
# Module Test
# ==============================================================================

if __name__ == "__main__":
    # Test MockLLMClient
    print("Testing MockLLMClient...")
    mock_client = MockLLMClient()

    test_prompt = """
QUESTION:
What is recursion?

COMPETENCY: Python
DIFFICULTY: Medium

GROUND TRUTH KEYPOINTS (the candidate should cover these):
1. base case
2. recursive case
3. stack usage

CANDIDATE'S ANSWER:
Recursion is when a function calls itself. You need a base case to stop.

TASK:
Evaluate this answer...
    """

    response = mock_client.call_llm(test_prompt, "mock", 0.3)
    print("\nMock Response:")
    print(response)
    print("\nMockLLMClient test passed!")


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    # Protocol
    "LLMClient",
    # Client implementations
    "OpenAIClient",
    "AnthropicClient",
    "MockLLMClient",
    # Factory
    "get_llm_client",
    # Rate limiting
    "RateLimiter",
    "get_rate_limiter",
    "reset_rate_limiter",
    # Retry decorator
    "retry_on_failure",
]
