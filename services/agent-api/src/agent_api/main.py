"""Agent API service entry point."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aai_core.config import load_config
from aai_core.errors import AAIError

from .api.routes import router
from .db.models import Base
from .db.repository import RunRepository
from .streaming.sse import RunSSEStream

log = structlog.get_logger()


class _SimpleMessageBus:
    """Minimal in-process bus for local dev. Replaced by NATS in production."""
    async def publish_run_created(self, run_id, tenant_id, agent_id, input_data):
        log.info("run_created_published", run_id=run_id)

    async def publish_run_cancelled(self, run_id, tenant_id):
        log.info("run_cancelled_published", run_id=run_id)


class _AuthMiddleware:
    """Extracts tenant_id from X-Internal-Token or X-Tenant-Id (dev fallback)."""
    def __init__(self, app, minter=None):
        self._app = app
        self._minter = minter

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            from starlette.requests import Request as StarletteRequest
            req = StarletteRequest(scope, receive)
            token = req.headers.get("X-Internal-Token")
            dev_tenant = req.headers.get("X-Tenant-Id")

            if token and self._minter:
                try:
                    claims = self._minter.decode(token)
                    scope["state"] = scope.get("state", {})
                    scope.setdefault("state", {})["tenant_id"] = claims["tenant_id"]
                except Exception:
                    pass
            elif dev_tenant:
                scope.setdefault("state", {})["tenant_id"] = dev_tenant

        await self._app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    config = load_config(os.environ.get("AAI_CONFIG_FILE"))
    app.state.config = config

    engine = create_async_engine(
        config.database.url,
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        echo=config.debug,
    )
    app.state.db_engine = engine
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    def _run_repo_factory() -> RunRepository:
        return RunRepository(session_factory())

    app.state.run_repo_factory = _run_repo_factory
    app.state.message_bus = _SimpleMessageBus()
    app.state.run_streams: dict[str, RunSSEStream] = {}

    log.info("agent_api_started", environment=config.environment)
    yield

    await engine.dispose()
    log.info("agent_api_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AAI Agent API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)

    @app.exception_handler(AAIError)
    async def aai_error_handler(request: Request, exc: AAIError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", exc_info=exc)
        from aai_core.errors import ErrorCode
        err = AAIError(ErrorCode.INTERNAL_ERROR, "Internal server error", http_status=500)
        return JSONResponse(status_code=500, content=err.to_dict())

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("agent_api.main:app", host="0.0.0.0", port=8002, reload=True)
