"""LiteLLM provider — covers OpenAI, Anthropic, Bedrock, Azure, Groq, etc.

One adapter handles all cloud providers via LiteLLM's unified interface.
Model names follow LiteLLM convention:
  "gpt-4o-mini"           → OpenAI
  "anthropic/claude-haiku-4-5-20251001"  → Anthropic
  "bedrock/meta.llama3-70b-instruct-v1:0" → AWS Bedrock
  "azure/gpt-4o"          → Azure OpenAI
  "groq/llama-3.1-70b-versatile" → Groq
"""
from __future__ import annotations

import os
from typing import Any, AsyncIterator

import litellm
from aai_core.adapters.llm import LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk
from aai_core.errors import AAIError, ErrorCode

# Suppress LiteLLM's verbose startup banner
litellm.suppress_debug_info = True
litellm.set_verbose = False


def _map_litellm_error(exc: Exception) -> AAIError:
    """Convert LiteLLM exceptions to AAIError."""
    msg = str(exc)
    exc_type = type(exc).__name__

    if "RateLimitError" in exc_type or "429" in msg:
        return AAIError(ErrorCode.LLM_RATE_LIMITED, f"LLM rate limited: {msg}", http_status=429, retriable=True)
    if "ContextWindowExceededError" in exc_type or "context_length" in msg.lower():
        return AAIError(ErrorCode.LLM_CONTEXT_OVERFLOW, f"Context window exceeded: {msg}", http_status=400)
    if "AuthenticationError" in exc_type or "401" in msg:
        return AAIError(ErrorCode.LLM_PROVIDER_ERROR, f"LLM auth failed: {msg}", http_status=401)
    return AAIError(ErrorCode.LLM_PROVIDER_ERROR, f"LLM provider error: {msg}", http_status=502, retriable=True)


class LiteLLMProvider(LLMProvider):
    """Unified LLM provider via LiteLLM.

    Swap the underlying model by changing config.llm.default_model.
    API keys are read from environment variables per LiteLLM convention.
    """

    def __init__(
        self,
        default_model: str = "gpt-4o-mini",
        litellm_proxy_url: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._default_model = default_model
        self._proxy_url = litellm_proxy_url
        self._extra_headers = extra_headers or {}

        # Route through LiteLLM proxy if configured (enterprise deployment)
        if litellm_proxy_url:
            litellm.api_base = litellm_proxy_url

    @property
    def provider_id(self) -> str:
        return "litellm"

    def _build_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        model = request.model or self._default_model
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            kwargs["tools"] = request.tools
            kwargs["tool_choice"] = request.tool_choice
        if self._extra_headers:
            kwargs["extra_headers"] = self._extra_headers
        kwargs.update(request.extra)
        return kwargs

    async def complete(self, request: LLMRequest) -> LLMResponse:
        kwargs = self._build_kwargs(request)
        try:
            resp = await litellm.acompletion(**kwargs)
        except Exception as exc:
            raise _map_litellm_error(exc) from exc

        choice = resp.choices[0]
        message = choice.message

        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        usage = resp.usage
        cost = litellm.completion_cost(completion_response=resp)

        return LLMResponse(
            content=message.content or "",
            model=resp.model or kwargs["model"],
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            finish_reason=choice.finish_reason or "stop",
            tool_calls=tool_calls,
            cost_usd=cost or 0.0,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        kwargs = self._build_kwargs(request)
        kwargs["stream"] = True
        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as exc:
            raise _map_litellm_error(exc) from exc

        async for chunk in response:
            choice = chunk.choices[0]
            delta = choice.delta
            content = delta.content or ""
            finish = choice.finish_reason

            tool_delta = None
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                tc = delta.tool_calls[0]
                tool_delta = {
                    "index": tc.index,
                    "id": getattr(tc, "id", None),
                    "function": {
                        "name": getattr(tc.function, "name", None) if tc.function else None,
                        "arguments": getattr(tc.function, "arguments", "") if tc.function else "",
                    },
                }

            yield LLMStreamChunk(
                delta=content,
                finish_reason=finish,
                tool_call_delta=tool_delta,
            )

    async def health(self) -> bool:
        # Check that at least one API key env var is set
        return bool(
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("AWS_ACCESS_KEY_ID")
            or self._proxy_url
        )
