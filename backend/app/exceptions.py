"""Application-level exceptions translated into HTTP responses by Flask."""
from __future__ import annotations


class APIError(Exception):
    """Base class for errors carrying an HTTP status code."""

    status_code = 400
    detail = "Bad request"

    def __init__(self, detail: str | None = None, status_code: int | None = None) -> None:
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(APIError):
    status_code = 404
    detail = "Resource not found"


class ConflictError(APIError):
    status_code = 409
    detail = "Resource conflict"


class UnauthorizedError(APIError):
    status_code = 401
    detail = "Authentication required"


class ForbiddenError(APIError):
    status_code = 403
    detail = "Access denied"


class ValidationError(APIError):
    status_code = 422
    detail = "Validation failed"


class RateLimitError(APIError):
    status_code = 429
    detail = "Too many requests"
