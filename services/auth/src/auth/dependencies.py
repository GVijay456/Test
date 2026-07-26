"""FastAPI dependency injection — wires validators to DB + cache."""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .cache.redis_cache import RedisAuthCache
from .core.api_key import APIKeyValidator
from .core.jwt_minter import InternalJWTMinter
from .db.repository import APIKeyRepository


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.db_session_factory() as session:
        yield session


async def get_repo(request: Request) -> APIKeyRepository:
    async with request.app.state.db_session_factory() as session:
        return APIKeyRepository(session)


async def get_cache(request: Request) -> RedisAuthCache:
    return RedisAuthCache(request.app.state.redis)


async def get_api_key_validator(request: Request) -> APIKeyValidator:
    return APIKeyValidator(
        cache=RedisAuthCache(request.app.state.redis),
        repo=APIKeyRepository(
            await request.app.state.db_session_factory().__anext__()  # type: ignore
        ),
        server_secret=request.app.state.config.auth.api_key_secret.get_secret_value(),
    )


async def get_jwt_minter(request: Request) -> InternalJWTMinter:
    return InternalJWTMinter(
        secret=request.app.state.config.auth.internal_jwt_secret.get_secret_value(),
        ttl_seconds=request.app.state.config.auth.internal_jwt_ttl,
    )
