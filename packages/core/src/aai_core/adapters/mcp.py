"""MCP (Model Context Protocol) adapter ABC.

Implementations connect to any MCP-compatible server (local stdio, HTTP SSE,
or WebSocket transport) and expose its tools as first-class platform tools.

Usage pattern:
    adapter = SomeMCPAdapter(server_url="http://localhost:8080")
    tools   = await adapter.list_tools()          # returns ToolManifest list
    result  = await adapter.call_tool("web_search", {"query": "…"})
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPToolManifest:
    """Mirrors MCP tools/list response schema."""
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    # Optional annotations from MCP spec (title, readOnlyHint, etc.)
    annotations: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolResult:
    """Mirrors MCP tools/call response schema."""
    content: list[dict[str, Any]]   # [{type: "text"|"image"|"resource", …}]
    is_error: bool = False


class MCPAdapter(ABC):
    """Plug-and-play MCP server adapter.

    Implementations: StdioMCPAdapter (subprocess), HttpMCPAdapter (HTTP+SSE),
    WsMCPAdapter (WebSocket).
    """

    @property
    @abstractmethod
    def server_id(self) -> str:
        """Unique identifier for this MCP server, e.g. 'filesystem', 'web'."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection / start subprocess. Idempotent."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close connection / terminate subprocess."""

    @abstractmethod
    async def list_tools(self) -> list[MCPToolManifest]:
        """Return all tools exposed by this MCP server."""

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        """Invoke a tool on the MCP server and return its result."""

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if the MCP server is reachable."""

    async def __aenter__(self) -> "MCPAdapter":
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.disconnect()


class MCPToolAdapter:
    """Wraps a single MCP tool as a callable platform tool.

    Enables MCP tools to be registered in the platform tool registry
    alongside native built-in tools without special-casing.
    """

    def __init__(self, adapter: MCPAdapter, manifest: MCPToolManifest) -> None:
        self._adapter = adapter
        self._manifest = manifest

    @property
    def name(self) -> str:
        return f"{self._adapter.server_id}__{self._manifest.name}"

    @property
    def description(self) -> str:
        return self._manifest.description

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._manifest.input_schema

    async def __call__(self, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await self._adapter.call_tool(self._manifest.name, arguments)
        # Normalise to a single text string for the platform's tool_output field
        text_parts = [
            part["text"]
            for part in result.content
            if part.get("type") == "text" and "text" in part
        ]
        return {
            "output": "\n".join(text_parts),
            "is_error": result.is_error,
            "raw_content": result.content,
        }
