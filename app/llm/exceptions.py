class LLMError(Exception):
    """Base exception for LLM provider errors."""

class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""

class LLMRateLimitError(LLMError):
    """Raised when an LLM provider rate-limits the request."""

class LLMProviderError(LLMError):
    """Raised when an LLM provider request fails."""