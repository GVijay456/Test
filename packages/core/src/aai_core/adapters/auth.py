"""Auth provider adapter ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AuthResult:
    tenant_id: str
    user_id: str | None
    scopes: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.scopes


class AuthProvider(ABC):
    """Plug-and-play identity provider interface.

    Implementations: KeycloakProvider (default), Auth0Provider,
    CognitoProvider, AzureADProvider.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique string like 'keycloak', 'auth0', 'cognito'."""

    @abstractmethod
    async def validate_jwt(self, token: str) -> AuthResult:
        """Validate a JWT/OIDC token. Raises AAIError on failure."""

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Return (new_access_token, new_refresh_token)."""

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if IdP is reachable."""
