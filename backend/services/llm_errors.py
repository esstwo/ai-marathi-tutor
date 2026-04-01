"""Custom exceptions for LLM service failures."""


class LLMServiceError(Exception):
    """Base exception for all LLM service errors."""


class LLMRateLimitError(LLMServiceError):
    """Raised when the LLM API returns a rate limit (429) error after retries."""


class LLMTimeoutError(LLMServiceError):
    """Raised when the LLM API times out after retries."""


class LLMAuthError(LLMServiceError):
    """Raised when the LLM API key is invalid or expired."""


class LLMContentFilterError(LLMServiceError):
    """Raised when the LLM refuses to respond due to content filtering."""


class LLMConnectionError(LLMServiceError):
    """Raised when the LLM API is unreachable after retries."""
