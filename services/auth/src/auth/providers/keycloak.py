"""Keycloak OIDC auth provider adapter.

Swappable: replace with Auth0Provider, CognitoProvider, or AzureADProvider
by changing config.auth_provider_backend — no code changes in other services.
"""
from __future__ import annotations

import httpx

from aai_core.adapters.auth import AuthProvider, AuthResult
from aai_core.errors import AAIError, ErrorCode

from ..core.jwt_validator import JWTValidator
from ..cache.redis_cache import RedisAuthCache


class KeycloakAuthProvider(AuthProvider):
    """Keycloak OIDC provider.

    Discovers JWKS URL from the well-known endpoint automatically.
    """

    def __init__(
        self,
        realm_url: str,          # e.g. http://keycloak:8080/realms/aai
        audience: str,
        cache: RedisAuthCache,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._realm_url = realm_url.rstrip("/")
        self._audience = audience
        self._cache = cache
        self._http = http_client or httpx.AsyncClient(timeout=5.0)
        self._validator: JWTValidator | None = None

    @property
    def provider_id(self) -> str:
        return "keycloak"

    async def _get_validator(self) -> JWTValidator:
        if self._validator is not None:
            return self._validator

        # Fetch OIDC discovery document to get issuer + jwks_uri
        discovery_url = f"{self._realm_url}/.well-known/openid-configuration"
        try:
            resp = await self._http.get(discovery_url)
            resp.raise_for_status()
            config = resp.json()
        except Exception as exc:
            raise AAIError(
                ErrorCode.AUTH_JWT_INVALID,
                f"Failed to fetch Keycloak OIDC config: {exc}",
                http_status=503,
                retriable=True,
            )

        self._validator = JWTValidator(
            cache=self._cache,
            issuer=config["issuer"],
            jwks_url=config["jwks_uri"],
            audience=self._audience,
            http_client=self._http,
        )
        return self._validator

    async def validate_jwt(self, token: str) -> AuthResult:
        validator = await self._get_validator()
        return await validator.validate(token)

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Exchange refresh token for new access + refresh tokens."""
        # Fetch token endpoint from discovery
        validator = await self._get_validator()
        token_endpoint = f"{self._realm_url}/protocol/openid-connect/token"

        try:
            resp = await self._http.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self._audience,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise AAIError(
                ErrorCode.AUTH_JWT_INVALID,
                f"Token refresh failed: {exc}",
                http_status=401,
            )

        return data["access_token"], data["refresh_token"]

    async def health(self) -> bool:
        try:
            resp = await self._http.get(
                f"{self._realm_url}/.well-known/openid-configuration",
                timeout=3.0,
            )
            return resp.status_code == 200
        except Exception:
            return False
