class LLMError(Exception):
    """Base exception for LLM provider errors."""

class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""

class LLMRateLimitError(LLMError):
    """Raised when an LLM provider rate-limits the request."""

class LLMProviderError(LLMError):
    """Raised when an LLM provider request fails."""

class LLMQuotaExceededError(LLMError):
    """Raised when the application zero-cost token budget is exhausted."""

    def __init__(self, message: str = "", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after  # seconds until the blocking budget frees up, when known

class LLMProviderDisabledError(LLMError):
    """Raised when the configured LLM provider is disabled by runtime policy."""

class LLMConcurrencyLimitError(LLMError):
    """Raised when the application concurrency guard is saturated."""