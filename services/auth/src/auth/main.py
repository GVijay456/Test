"""Auth service entry point."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aai_core.config import load_config
from aai_core.errors import AAIError

from .api.routes import router
from .db.models import Base

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    config = load_config(os.environ.get("AAI_CONFIG_FILE"))
    app.state.config = config

    # DB
    engine = create_async_engine(
        config.database.url,
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        pool_timeout=config.database.pool_timeout,
        echo=config.debug,
    )
    app.state.db_engine = engine
    app.state.db_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Redis
    redis = Redis.from_url(config.redis.url, decode_responses=True)
    app.state.redis = redis

    # Optional: OIDC JWT validator (only if configured)
    if config.auth.jwks_url and config.auth.jwt_issuer:
        from .cache.redis_cache import RedisAuthCache
        from .core.jwt_validator import JWTValidator

        app.state.jwt_validator = JWTValidator(
            cache=RedisAuthCache(redis),
            issuer=config.auth.jwt_issuer,
            jwks_url=config.auth.jwks_url,
            audience=config.auth.jwt_audience,
        )
    else:
        app.state.jwt_validator = None

    log.info("auth_service_started", environment=config.environment)

    yield

    await redis.aclose()
    await engine.dispose()
    log.info("auth_service_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AAI Auth Service",
        version="0.1.0",
        docs_url="/docs" if os.environ.get("AAI_ENVIRONMENT", "local") != "production" else None,
        lifespan=lifespan,
    )

    app.include_router(router)

    @app.exception_handler(AAIError)
    async def aai_error_handler(request: Request, exc: AAIError) -> JSONResponse:
        log.warning("auth_error", code=exc.code, message=exc.message, path=request.url.path)
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", exc_info=exc)
        from aai_core.errors import ErrorCode
        err = AAIError(ErrorCode.INTERNAL_ERROR, "Internal server error", http_status=500)
        return JSONResponse(status_code=500, content=err.to_dict())

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "auth.main:app",
        host="0.0.0.0",
        port=8001,
        reload=os.environ.get("AAI_ENVIRONMENT", "local") == "local",
    )
