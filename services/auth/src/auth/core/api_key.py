"""API key validation — HMAC-SHA256 + Redis 60s cache + DB fallback.

Key format: aai_{env}_{32 random hex chars}
  e.g.  aai_live_a3f8c2d1e4b5...
  e.g.  aai_test_00000000...

Storage: HMAC-SHA256(raw_key, server_secret) is stored in DB.
         Raw key is returned ONCE at creation and never stored.

Validation flow:
  1. Compute HMAC of incoming key
  2. Check Redis (60s TTL) → cache hit: return immediately
  3. DB lookup by hash → populate cache → return
  4. Not found / inactive / expired → raise AAIError
"""
from __future__ import annotations

import asyncio
import hmac
import hashlib
import os
import secrets
from datetime import datetime, timezone

from aai_core.errors import AAIError, ErrorCode

from ..cache.redis_cache import CachedAPIKey, RedisAuthCache
from ..db.repository import APIKeyRepository


def _compute_hash(raw_key: str, secret: str) -> str:
    """HMAC-SHA256(raw_key, secret) → hex digest."""
    return hmac.new(
        secret.encode(),
        raw_key.encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_api_key(environment: str = "live") -> tuple[str, str]:
    """Generate a new API key. Returns (raw_key, key_prefix).

    raw_key must be shown to user once and never stored.
    Store only the HMAC hash.
    """
    random_part = secrets.token_hex(32)          # 256 bits of entropy
    raw_key = f"aai_{environment}_{random_part}"
    key_prefix = raw_key[:12]                    # "aai_live_a3f" for display
    return raw_key, key_prefix


class APIKeyValidator:
    def __init__(
        self,
        cache: RedisAuthCache,
        repo: APIKeyRepository,
        server_secret: str,
    ) -> None:
        self._cache = cache
        self._repo = repo
        self._secret = server_secret

    async def validate(self, raw_key: str) -> CachedAPIKey:
        """Validate a raw API key. Returns CachedAPIKey or raises AAIError."""
        if not raw_key or not raw_key.startswith("aai_"):
            raise AAIError(
                ErrorCode.AUTH_INVALID_API_KEY,
                "Invalid API key format",
                http_status=401,
            )

        key_hash = _compute_hash(raw_key, self._secret)

        # 1 — Redis cache
        cached = await self._cache.get_api_key(key_hash)
        if cached is not None:
            if not cached.is_active:
                raise AAIError(
                    ErrorCode.AUTH_INVALID_API_KEY,
                    "API key revoked",
                    http_status=401,
                )
            return cached

        # 2 — DB lookup
        db_key = await self._repo.get_by_hash(key_hash)
        if db_key is None:
            raise AAIError(
                ErrorCode.AUTH_INVALID_API_KEY,
                "API key not found",
                http_status=401,
            )

        if not db_key.is_active:
            raise AAIError(
                ErrorCode.AUTH_INVALID_API_KEY,
                "API key revoked",
                http_status=401,
            )

        if db_key.expires_at and db_key.expires_at < datetime.now(timezone.utc):
            raise AAIError(
                ErrorCode.AUTH_API_KEY_EXPIRED,
                "API key expired",
                http_status=401,
            )

        tenant = await self._repo.get_tenant(db_key.tenant_id)
        if tenant is None or tenant.is_suspended:
            raise AAIError(
                ErrorCode.TENANT_SUSPENDED,
                "Tenant is suspended",
                http_status=403,
            )

        entry = CachedAPIKey(
            key_id=db_key.id,
            tenant_id=db_key.tenant_id,
            scopes=list(db_key.scopes),
            is_active=True,
        )

        # Populate cache (non-blocking — don't fail if Redis is down)
        asyncio.ensure_future(self._cache.set_api_key(key_hash, entry))

        # Fire-and-forget last_used_at update
        asyncio.ensure_future(self._repo.touch_last_used(db_key.id))

        return entry
