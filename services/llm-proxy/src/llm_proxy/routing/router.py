"""LLM router — selects provider + model, enforces circuit breaker.

Routing priority:
  1. Explicit model in request (tenant override or agent preference)
  2. Config default model
  3. Fallback provider if primary circuit is OPEN

Provider registry maps model-name prefixes to provider instances:
  "gpt-*", "o1-*", "o3-*", "text-embedding-*" → LiteLLM (OpenAI)
  "anthropic/*"                                → LiteLLM (Anthropic)
  "bedrock/*"                                  → LiteLLM (Bedrock)
  "ollama/*"                                   → OllamaProvider
  anything else                                → LiteLLM (default)
"""
from __future__ import annotations

import re
from typing import Any, AsyncIterator

from aai_core.adapters.llm import LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk
from aai_core.errors import AAIError, ErrorCode

from ..circuit_breaker.breaker import CircuitBreaker, CircuitState


class ProviderRegistry:
    """Maps model name patterns to (provider, circuit_breaker) pairs."""

    def __init__(self) -> None:
        self._entries: list[tuple[str, LLMProvider, CircuitBreaker]] = []
        self._default: tuple[LLMProvider, CircuitBreaker] | None = None

    def register(
        self,
        pattern: str,
        provider: LLMProvider,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        if breaker is None:
            breaker = CircuitBreaker(provider_id=provider.provider_id)
        self._entries.append((pattern, provider, breaker))

    def set_default(
        self,
        provider: LLMProvider,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        if breaker is None:
            breaker = CircuitBreaker(provider_id=provider.provider_id)
        self._default = (provider, breaker)

    def resolve(self, model: str) -> tuple[LLMProvider, CircuitBreaker]:
        for pattern, provider, breaker in self._entries:
            if re.match(pattern, model, re.IGNORECASE):
                return provider, breaker
        if self._default:
            return self._default
        raise AAIError(
            ErrorCode.LLM_PROVIDER_ERROR,
            f"No provider registered for model {model!r}",
            http_status=400,
        )

    def all_states(self) -> dict[str, str]:
        states = {}
        for _, provider, breaker in self._entries:
            states[provider.provider_id] = breaker.state
        if self._default:
            provider, breaker = self._default
            states[f"{provider.provider_id}:default"] = breaker.state
        return states


class LLMRouter:
    """Routes LLM requests through the registry with circuit breaker protection.

    Falls back to the next healthy provider if the primary circuit is OPEN.
    """

    def __init__(self, registry: ProviderRegistry, default_model: str = "gpt-4o-mini") -> None:
        self._registry = registry
        self._default_model = default_model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self._default_model
        request = LLMRequest(
            messages=request.messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=request.tools,
            tool_choice=request.tool_choice,
            stream=False,
            extra=request.extra,
        )
        provider, breaker = self._registry.resolve(model)
        return await breaker.call(provider.complete, request)

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        model = request.model or self._default_model
        request = LLMRequest(
            messages=request.messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=request.tools,
            tool_choice=request.tool_choice,
            stream=True,
            extra=request.extra,
        )
        provider, breaker = self._registry.resolve(model)

        # Wrap the async generator call inside the circuit breaker
        if breaker.state == CircuitState.OPEN:
            raise AAIError(
                ErrorCode.LLM_CIRCUIT_OPEN,
                f"Circuit breaker OPEN for provider {provider.provider_id!r}",
                http_status=503,
                retriable=True,
            )

        async for chunk in provider.stream(request):
            yield chunk
