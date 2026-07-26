"""Tests for LLM router — provider selection and circuit breaker integration."""
from __future__ import annotations

from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from aai_core.adapters.llm import LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk
from aai_core.errors import AAIError, ErrorCode
from llm_proxy.circuit_breaker.breaker import CircuitBreaker
from llm_proxy.routing.router import LLMRouter, ProviderRegistry


def _mock_response(content: str = "hello") -> LLMResponse:
    return LLMResponse(
        content=content,
        model="gpt-4o-mini",
        prompt_tokens=5,
        completion_tokens=3,
        finish_reason="stop",
    )


def _mock_provider(provider_id: str, response: LLMResponse | None = None) -> LLMProvider:
    p = MagicMock(spec=LLMProvider)
    p.provider_id = provider_id
    p.complete = AsyncMock(return_value=response or _mock_response())
    return p


def _simple_request(model: str = "gpt-4o-mini") -> LLMRequest:
    return LLMRequest(messages=[{"role": "user", "content": "hi"}], model=model)


class TestProviderRegistry:
    def test_pattern_match(self):
        reg = ProviderRegistry()
        p = _mock_provider("openai")
        reg.register(r"^gpt-", p)
        provider, _ = reg.resolve("gpt-4o-mini")
        assert provider.provider_id == "openai"

    def test_ollama_pattern(self):
        reg = ProviderRegistry()
        p_ollama = _mock_provider("ollama")
        p_openai = _mock_provider("openai")
        reg.register(r"^ollama/", p_ollama)
        reg.register(r"^gpt-", p_openai)
        provider, _ = reg.resolve("ollama/llama3.2")
        assert provider.provider_id == "ollama"

    def test_default_used_when_no_match(self):
        reg = ProviderRegistry()
        p = _mock_provider("default")
        reg.set_default(p)
        provider, _ = reg.resolve("unknown-model-xyz")
        assert provider.provider_id == "default"

    def test_no_match_no_default_raises(self):
        reg = ProviderRegistry()
        with pytest.raises(AAIError) as exc:
            reg.resolve("unknown-model")
        assert exc.value.code == ErrorCode.LLM_PROVIDER_ERROR

    def test_all_states(self):
        reg = ProviderRegistry()
        reg.register(r"^gpt-", _mock_provider("openai"))
        states = reg.all_states()
        assert "openai" in states


class TestLLMRouter:
    @pytest.mark.asyncio
    async def test_routes_to_correct_provider(self):
        reg = ProviderRegistry()
        p = _mock_provider("openai")
        reg.register(r"^gpt-", p)
        reg.set_default(p)

        router = LLMRouter(reg, default_model="gpt-4o-mini")
        resp = await router.complete(_simple_request("gpt-4o-mini"))
        assert resp.content == "hello"
        p.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_default_model_when_none(self):
        reg = ProviderRegistry()
        p = _mock_provider("openai")
        reg.register(r"^gpt-", p)
        reg.set_default(p)

        router = LLMRouter(reg, default_model="gpt-4o-mini")
        req = LLMRequest(messages=[{"role": "user", "content": "hi"}], model=None)
        resp = await router.complete(req)
        assert resp.content == "hello"

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_on_failures(self):
        reg = ProviderRegistry()
        p = MagicMock(spec=LLMProvider)
        p.provider_id = "test"
        p.complete = AsyncMock(
            side_effect=AAIError(ErrorCode.LLM_PROVIDER_ERROR, "error", http_status=502)
        )
        breaker = CircuitBreaker("test", failure_threshold=2, cool_down_seconds=999)
        reg.register(r"^test-", p, breaker)
        reg.set_default(p, breaker)

        router = LLMRouter(reg, default_model="test-model")
        for _ in range(2):
            with pytest.raises(AAIError):
                await router.complete(_simple_request("test-model"))

        with pytest.raises(AAIError) as exc:
            await router.complete(_simple_request("test-model"))
        assert exc.value.code == ErrorCode.LLM_CIRCUIT_OPEN
