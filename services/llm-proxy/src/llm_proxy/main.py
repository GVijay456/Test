"""LLM Proxy service — unified LLM access with circuit breaker."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from aai_core.adapters.llm import LLMRequest
from aai_core.config import load_config
from aai_core.errors import AAIError, ErrorCode

from .adapters.litellm_provider import LiteLLMProvider
from .adapters.ollama_provider import OllamaProvider
from .circuit_breaker.breaker import CircuitBreaker
from .routing.router import LLMRouter, ProviderRegistry

log = structlog.get_logger()


def _build_registry(config) -> ProviderRegistry:
    registry = ProviderRegistry()

    litellm_provider = LiteLLMProvider(
        default_model=config.llm.default_model,
        litellm_proxy_url=config.llm.litellm_proxy_url,
    )
    litellm_breaker = CircuitBreaker(
        provider_id="litellm",
        failure_threshold=5,
        cool_down_seconds=30.0,
    )

    ollama_provider = OllamaProvider(base_url=config.llm.ollama_url)
    ollama_breaker = CircuitBreaker(
        provider_id="ollama",
        failure_threshold=3,
        cool_down_seconds=15.0,
    )

    # Pattern → provider mapping
    registry.register(r"^ollama/.*", ollama_provider, ollama_breaker)
    registry.register(r"^(gpt-|o1|o3|text-embedding)", litellm_provider, litellm_breaker)
    registry.register(r"^anthropic/", litellm_provider, litellm_breaker)
    registry.register(r"^bedrock/", litellm_provider, litellm_breaker)
    registry.register(r"^azure/", litellm_provider, litellm_breaker)
    registry.register(r"^groq/", litellm_provider, litellm_breaker)
    registry.set_default(litellm_provider, litellm_breaker)

    return registry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = load_config(os.environ.get("AAI_CONFIG_FILE"))
    app.state.config = config

    registry = _build_registry(config)
    app.state.router = LLMRouter(registry, default_model=config.llm.default_model)
    app.state.registry = registry

    log.info("llm_proxy_started", default_model=config.llm.default_model)
    yield
    log.info("llm_proxy_stopped")


# ── Request / response models ─────────────────────────────────────────────────

class CompletionRequest(BaseModel):
    messages: list[dict[str, Any]]
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    tools: list[dict[str, Any]] = []
    tool_choice: str | dict[str, Any] = "auto"
    stream: bool = False
    extra: dict[str, Any] = {}


class CompletionResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str
    tool_calls: list[dict[str, Any]] = []
    cost_usd: float


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(title="AAI LLM Proxy", version="0.1.0", lifespan=lifespan)

    @app.post("/v1/llm/complete", response_model=CompletionResponse)
    async def complete(body: CompletionRequest, request: Request):
        router: LLMRouter = request.app.state.router
        llm_req = LLMRequest(
            messages=body.messages,
            model=body.model or request.app.state.config.llm.default_model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            tools=body.tools,
            tool_choice=body.tool_choice,
            stream=False,
            extra=body.extra,
        )
        resp = await router.complete(llm_req)
        return CompletionResponse(
            content=resp.content,
            model=resp.model,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            finish_reason=resp.finish_reason,
            tool_calls=resp.tool_calls,
            cost_usd=resp.cost_usd,
        )

    @app.post("/v1/llm/stream")
    async def stream(body: CompletionRequest, request: Request):
        router: LLMRouter = request.app.state.router
        llm_req = LLMRequest(
            messages=body.messages,
            model=body.model or request.app.state.config.llm.default_model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            tools=body.tools,
            stream=True,
            extra=body.extra,
        )

        async def _chunks():
            import json
            async for chunk in router.stream(llm_req):
                yield f"data: {json.dumps({'delta': chunk.delta, 'finish_reason': chunk.finish_reason})}\n\n"

        return StreamingResponse(_chunks(), media_type="text/event-stream")

    @app.get("/v1/llm/providers")
    async def providers(request: Request):
        registry: ProviderRegistry = request.app.state.registry
        return {"providers": registry.all_states()}

    @app.get("/internal/health/live")
    async def liveness():
        return {"status": "ok"}

    @app.get("/internal/health/ready")
    async def readiness(request: Request):
        registry: ProviderRegistry = request.app.state.registry
        states = registry.all_states()
        all_open = all(v == "open" for v in states.values())
        return {
            "status": "degraded" if all_open else "ok",
            "providers": states,
        }

    @app.exception_handler(AAIError)
    async def aai_error_handler(request: Request, exc: AAIError) -> JSONResponse:
        log.warning("llm_error", code=exc.code, message=exc.message)
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", exc_info=exc)
        err = AAIError(ErrorCode.INTERNAL_ERROR, "Internal server error", http_status=500)
        return JSONResponse(status_code=500, content=err.to_dict())

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("llm_proxy.main:app", host="0.0.0.0", port=8003, reload=True)
