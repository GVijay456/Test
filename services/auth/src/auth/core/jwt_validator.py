"""JWT/OIDC validation — JWKS fetch + cache + exp/iss/aud checks.

Supports any OIDC-compliant provider (Keycloak, Auth0, Cognito, Azure AD).
JWKS are cached 5 minutes in Redis to avoid hammering the IdP.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from aai_core.adapters.auth import AuthResult
from aai_core.errors import AAIError, ErrorCode

from ..cache.redis_cache import RedisAuthCache


class JWTValidator:
    def __init__(
        self,
        cache: RedisAuthCache,
        issuer: str,
        jwks_url: str,
        audience: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._cache = cache
        self._issuer = issuer
        self._jwks_url = jwks_url
        self._audience = audience
        self._http = http_client or httpx.AsyncClient(timeout=5.0)

    async def validate(self, token: str) -> AuthResult:
        """Validate a JWT. Returns AuthResult or raises AAIError."""
        jwks = await self._get_jwks()

        try:
            # jose verifies signature, exp, iss, aud automatically
            claims: dict[str, Any] = jwt.decode(
                token,
                jwks,
                algorithms=["RS256", "ES256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"verify_at_hash": False},
            )
        except ExpiredSignatureError:
            raise AAIError(
                ErrorCode.AUTH_JWT_EXPIRED,
                "JWT token has expired",
                http_status=401,
            )
        except JWTError as exc:
            raise AAIError(
                ErrorCode.AUTH_JWT_INVALID,
                f"JWT validation failed: {exc}",
                http_status=401,
            )

        tenant_id = claims.get("tenant_id") or claims.get("org_id") or ""
        if not tenant_id:
            raise AAIError(
                ErrorCode.AUTH_JWT_INVALID,
                "JWT missing tenant_id / org_id claim",
                http_status=401,
            )

        scopes_raw = claims.get("scope", "") or ""
        scopes = scopes_raw.split() if isinstance(scopes_raw, str) else list(scopes_raw)

        return AuthResult(
            tenant_id=tenant_id,
            user_id=claims.get("sub"),
            scopes=scopes,
            metadata={
                "iss": claims.get("iss", ""),
                "email": claims.get("email", ""),
            },
        )

    async def _get_jwks(self) -> dict[str, Any]:
        cached = await self._cache.get_jwks(self._jwks_url)
        if cached is not None:
            return cached

        try:
            resp = await self._http.get(self._jwks_url)
            resp.raise_for_status()
            jwks: dict[str, Any] = resp.json()
        except Exception as exc:
            raise AAIError(
                ErrorCode.AUTH_JWT_INVALID,
                f"Failed to fetch JWKS: {exc}",
                http_status=503,
                retriable=True,
            )

        await self._cache.set_jwks(self._jwks_url, jwks)
        return jwks
