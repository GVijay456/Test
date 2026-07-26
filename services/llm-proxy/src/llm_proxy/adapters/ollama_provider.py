"""Ollama provider adapter — local/self-hosted open-source models.

Targets the Ollama REST API directly via httpx.
No API key required. Models are pulled on first use.

Typical model names: "llama3.2", "mistral", "phi3.5", "qwen2.5-coder"
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from aai_core.adapters.llm import LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk
from aai_core.errors import AAIError, ErrorCode


class OllamaProvider(LLMProvider):
    """Ollama local model provider.

    Swap to any Ollama-hosted model by changing the model name in the request.
    Supports streaming and tool calls (Ollama v0.3+).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout, connect=5.0)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    @property
    def provider_id(self) -> str:
        return "ollama"

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        # Strip provider prefix if present (e.g. "ollama/llama3.2" → "llama3.2")
        model = request.model.removeprefix("ollama/") if request.model else "llama3.2"
        payload: dict[str, Any] = {
            "model": model,
            "messages": request.messages,
            "stream": request.stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.tools:
            payload["tools"] = request.tools
        return payload

    async def complete(self, request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(request)
        payload["stream"] = False

        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AAIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Ollama error {exc.response.status_code}: {exc.response.text}",
                http_status=502,
                retriable=True,
            ) from exc
        except httpx.RequestError as exc:
            raise AAIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Ollama unreachable: {exc}",
                http_status=503,
                retriable=True,
            ) from exc

        data = resp.json()
        message = data.get("message", {})
        content = message.get("content", "")

        tool_calls = []
        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            tool_calls.append({
                "id": f"ollama-{len(tool_calls)}",
                "type": "function",
                "function": {
                    "name": fn.get("name", ""),
                    "arguments": json.dumps(args) if isinstance(args, dict) else args,
                },
            })

        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=data.get("model", payload["model"]),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop" if data.get("done") else "length",
            tool_calls=tool_calls,
            cost_usd=0.0,   # self-hosted — no per-token cost
            raw=data,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        payload = self._build_payload(request)
        payload["stream"] = True

        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = data.get("message", {})
                    content = message.get("content", "")
                    done = data.get("done", False)

                    yield LLMStreamChunk(
                        delta=content,
                        finish_reason="stop" if done else None,
                    )
                    if done:
                        break

        except httpx.RequestError as exc:
            raise AAIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Ollama stream error: {exc}",
                http_status=503,
                retriable=True,
            ) from exc

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []
