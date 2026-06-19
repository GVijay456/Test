"""Plugin system ABCs."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PluginTrustLevel(StrEnum):
    PLATFORM  = "platform"    # built-in, fully trusted
    VERIFIED  = "verified"    # reviewed + signed by platform team
    COMMUNITY = "community"   # user-installed, sandboxed
    BYOP      = "byop"        # Bring Your Own Plugin, most restricted


@dataclass
class HealthStatus:
    healthy: bool
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginHook:
    """A hook point the plugin subscribes to."""
    event: str          # e.g. "before_llm_call", "after_tool_call", "on_run_complete"
    priority: int = 100 # lower = runs first


class Plugin(ABC):
    """Base class for all platform plugins.

    Plugins are loaded from a signed manifest. The manifest is verified
    against the plugin registry before the plugin class is instantiated.
    Trust level determines sandbox restrictions (gVisor for community/byop).
    """

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Globally unique plugin identifier, e.g. 'com.acme.legal-search'."""

    @property
    @abstractmethod
    def version(self) -> str:
        """SemVer string, e.g. '1.2.0'."""

    @property
    def trust_level(self) -> PluginTrustLevel:
        return PluginTrustLevel.COMMUNITY

    @property
    def hooks(self) -> list[PluginHook]:
        """Declare which events this plugin subscribes to."""
        return []

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """Called once at plugin load time."""

    @abstractmethod
    async def health(self) -> HealthStatus:
        """Called by the health check endpoint."""

    async def teardown(self) -> None:
        """Called on graceful shutdown. Override to release resources."""
