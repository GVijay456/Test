"""Internal JWT minting — short-lived (5 min) service-to-service tokens.

These are signed with a shared secret (HS256). They are never exposed to
external clients — only used for service-to-service calls within the platform.
"""
from __future__ import annotations

import time
from typing import Any

from jose import jwt

from aai_core.adapters.auth import AuthResult
from aai_core.errors import AAIError, ErrorCode


class InternalJWTMinter:
    _ALGORITHM = "HS256"

    def __init__(self, secret: str, ttl_seconds: int = 300) -> None:
        self._secret = secret
        self._ttl = ttl_seconds

    def mint(self, auth_result: AuthResult, issuer: str = "aai-auth") -> str:
        """Mint a short-lived internal JWT from an AuthResult."""
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": issuer,
            "aud": "aai-internal",
            "iat": now,
            "exp": now + self._ttl,
            "tenant_id": auth_result.tenant_id,
            "sub": auth_result.user_id or "api-key",
            "scopes": auth_result.scopes,
        }
        return jwt.encode(claims, self._secret, algorithm=self._ALGORITHM)

    def decode(self, token: str) -> dict[str, Any]:
        """Decode and verify an internal JWT. Raises AAIError on failure."""
        try:
            return jwt.decode(
                token,
                self._secret,
                algorithms=[self._ALGORITHM],
                audience="aai-internal",
            )
        except Exception as exc:
            raise AAIError(
                ErrorCode.AUTH_JWT_INVALID,
                f"Internal JWT invalid: {exc}",
                http_status=401,
            )
