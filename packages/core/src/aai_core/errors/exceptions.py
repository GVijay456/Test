"""Structured exception carrying an AAI error code + HTTP status."""
from __future__ import annotations

from typing import Any

from .codes import ErrorCode


class AAIError(Exception):
    """Base exception for all platform errors.

    Always carries an ErrorCode so callers can handle by code, not string.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        http_status: int = 500,
        detail: dict[str, Any] | None = None,
        retriable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.detail = detail or {}
        self.retriable = retriable

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "detail": self.detail,
                "retriable": self.retriable,
            }
        }

    # Convenience constructors for common cases
    @classmethod
    def not_found(cls, resource: str, id: str) -> "AAIError":
        code_map = {
            "run": ErrorCode.RUN_NOT_FOUND,
            "tenant": ErrorCode.TENANT_NOT_FOUND,
            "tool": ErrorCode.TOOL_NOT_FOUND,
        }
        code = code_map.get(resource, ErrorCode.INTERNAL_ERROR)
        return cls(code, f"{resource} {id!r} not found", http_status=404)

    @classmethod
    def auth_failed(cls, reason: str) -> "AAIError":
        return cls(ErrorCode.AUTH_INVALID_API_KEY, reason, http_status=401)

    @classmethod
    def forbidden(cls, reason: str = "Insufficient permissions") -> "AAIError":
        return cls(ErrorCode.AUTHZ_FORBIDDEN, reason, http_status=403)

    @classmethod
    def rate_limited(cls, retry_after: int = 60) -> "AAIError":
        return cls(
            ErrorCode.AUTH_RATE_LIMITED,
            "Rate limit exceeded",
            http_status=429,
            detail={"retry_after": retry_after},
            retriable=True,
        )
