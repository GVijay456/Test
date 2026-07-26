"""Secret store adapter ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod


class SecretStore(ABC):
    """Plug-and-play secret store interface.

    Implementations: VaultStore (default), AWSSecretsManagerStore,
    AzureKeyVaultStore, GCPSecretManagerStore.
    """

    @property
    @abstractmethod
    def store_id(self) -> str:
        """Unique string like 'vault', 'aws-sm', 'azure-kv'."""

    @abstractmethod
    async def get(self, path: str, version: int | None = None) -> str:
        """Retrieve a secret value by path. Returns plaintext."""

    @abstractmethod
    async def put(self, path: str, value: str) -> int:
        """Write a secret. Returns the new version number."""

    @abstractmethod
    async def delete(self, path: str, version: int | None = None) -> None:
        """Delete a secret version (or all versions if version=None)."""

    @abstractmethod
    async def list_versions(self, path: str) -> list[int]:
        """Return all available version numbers for a path."""

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if store is reachable."""
