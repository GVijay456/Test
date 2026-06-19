"""Redis cache layer for auth lookups.

API key validation: check Redis first (60s TTL), fall back to DB.
JWKS: cached 5 minutes per issuer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from redis.asyncio import Redis


@dataclass
class CachedAPIKey:
    key_id: str
    tenant_id: str
    scopes: list[str]
    is_active: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "CachedAPIKey":
        d = json.loads(data)
        return cls(**d)


class RedisAuthCache:
    _API_KEY_TTL = 60       # seconds — matches architecture spec
    _JWKS_TTL = 300         # 5 minutes
    _IP_BLOCK_TTL = 3600    # 1 hour

    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis

    # ── API key cache ─────────────────────────────────────────────────────

    def _api_key_cache_key(self, key_hash: str) -> str:
        return f"auth:apikey:{key_hash}"

    async def get_api_key(self, key_hash: str) -> CachedAPIKey | None:
        raw = await self._redis.get(self._api_key_cache_key(key_hash))
        if raw is None:
            return None
        return CachedAPIKey.from_json(raw)

    async def set_api_key(self, key_hash: str, entry: CachedAPIKey) -> None:
        await self._redis.set(
            self._api_key_cache_key(key_hash),
            entry.to_json(),
            ex=self._API_KEY_TTL,
        )

    async def invalidate_api_key(self, key_hash: str) -> None:
        await self._redis.delete(self._api_key_cache_key(key_hash))

    # ── JWKS cache ────────────────────────────────────────────────────────

    def _jwks_cache_key(self, jwks_url: str) -> str:
        return f"auth:jwks:{jwks_url}"

    async def get_jwks(self, jwks_url: str) -> dict | None:
        raw = await self._redis.get(self._jwks_cache_key(jwks_url))
        if raw is None:
            return None
        return json.loads(raw)

    async def set_jwks(self, jwks_url: str, jwks: dict) -> None:
        await self._redis.set(
            self._jwks_cache_key(jwks_url),
            json.dumps(jwks),
            ex=self._JWKS_TTL,
        )

    # ── IP block cache (for rate limit enforcement) ───────────────────────

    async def is_ip_blocked(self, ip: str) -> bool:
        return bool(await self._redis.exists(f"auth:block:ip:{ip}"))

    async def block_ip(self, ip: str, ttl: int = _IP_BLOCK_TTL) -> None:
        await self._redis.set(f"auth:block:ip:{ip}", "1", ex=ttl)

    # ── Rate limiting (sliding window counter) ────────────────────────────

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Returns (allowed, current_count)."""
        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, xx=False)  # only set if not already set
        results = await pipe.execute()
        count: int = results[0]
        return count <= max_requests, count
