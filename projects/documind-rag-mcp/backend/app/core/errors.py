"""Structured application errors.

Every error the API returns follows {"error": {"code": ..., "message": ...}}.
Internals (stack traces, provider bodies, SQL) never reach the client.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for controlled, client-safe errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "An internal error occurred.") -> None:
        super().__init__(message)
        self.message = message

    def to_payload(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


class ValidationAppError(AppError):
    status_code = 400
    code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message)


class ProviderUnavailableError(AppError):
    status_code = 503
    code = "provider_unavailable"

    def __init__(self, message: str = "AI provider temporarily unavailable.") -> None:
        super().__init__(message)


class ProviderRateLimitError(AppError):
    """Raised internally by providers on 429; callers retry / fall back."""

    status_code = 503
    code = "provider_rate_limited"

    def __init__(self, message: str = "Provider rate limit reached.") -> None:
        super().__init__(message)


class MalformedModelOutputError(AppError):
    """LLM returned output that failed structured validation after retry."""

    status_code = 502
    code = "malformed_model_output"

    def __init__(self, message: str = "The model returned an invalid response.") -> None:
        super().__init__(message)


class StorageError(AppError):
    status_code = 502
    code = "storage_error"

    def __init__(self, message: str = "Document storage operation failed.") -> None:
        super().__init__(message)
