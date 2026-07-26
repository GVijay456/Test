"""LLM provider adapter ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class LLMRequest:
    messages: list[dict[str, Any]]
    model: str
    temperature: float = 0.0
    max_tokens: int = 4096
    tools: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str | dict[str, Any] = "auto"
    stream: bool = False
    # Passed through to provider — provider-specific overrides
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str                          # "stop" | "tool_calls" | "length"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)

    # Reasoning model fields (o3, claude extended thinking, DeepSeek R1)
    # thinking_tokens are billed separately and must NOT be passed back to the
    # model as assistant content — strip before building next message.
    thinking_tokens: int = 0
    thinking_blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LLMStreamChunk:
    delta: str
    finish_reason: str | None = None
    tool_call_delta: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Plug-and-play LLM provider interface.

    Implementations: LiteLLMProvider (wraps OpenAI/Anthropic/Bedrock/etc.),
    OllamaProvider, vLLMProvider.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique string like 'openai', 'anthropic', 'ollama'."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Non-streaming completion."""

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Streaming completion — yields chunks until finish_reason is set."""

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if provider is reachable."""

    async def estimate_tokens(self, messages: list[dict[str, Any]], model: str) -> int:
        """Best-effort token count. Override for accurate counting."""
        chars = sum(len(str(m)) for m in messages)
        return chars // 4
