"""Tests for API key generation, hashing, and validation."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from auth.core.api_key import APIKeyValidator, _compute_hash, generate_api_key
from auth.cache.redis_cache import CachedAPIKey
from aai_core.errors import AAIError, ErrorCode


class TestGenerateAPIKey:
    def test_format(self):
        raw, prefix = generate_api_key("live")
        assert raw.startswith("aai_live_")
        assert len(raw) == len("aai_live_") + 64  # 32 hex bytes
        assert prefix == raw[:12]

    def test_unique(self):
        k1, _ = generate_api_key()
        k2, _ = generate_api_key()
        assert k1 != k2

    def test_test_environment(self):
        raw, _ = generate_api_key("test")
        assert raw.startswith("aai_test_")


class TestComputeHash:
    def test_deterministic(self):
        h1 = _compute_hash("my-key", "secret")
        h2 = _compute_hash("my-key", "secret")
        assert h1 == h2

    def test_different_key_different_hash(self):
        h1 = _compute_hash("key-a", "secret")
        h2 = _compute_hash("key-b", "secret")
        assert h1 != h2

    def test_different_secret_different_hash(self):
        h1 = _compute_hash("key", "secret-a")
        h2 = _compute_hash("key", "secret-b")
        assert h1 != h2

    def test_output_is_hex(self):
        h = _compute_hash("key", "secret")
        assert len(h) == 64
        int(h, 16)  # raises if not valid hex


class TestAPIKeyValidator:
    def _make_validator(self, cache_result=None, db_result=None, tenant=None):
        cache = AsyncMock()
        cache.get_api_key = AsyncMock(return_value=cache_result)
        cache.set_api_key = AsyncMock()

        repo = AsyncMock()
        repo.get_by_hash = AsyncMock(return_value=db_result)
        repo.get_tenant = AsyncMock(return_value=tenant)
        repo.touch_last_used = AsyncMock()

        return APIKeyValidator(cache=cache, repo=repo, server_secret="test-secret")

    @pytest.mark.asyncio
    async def test_rejects_bad_format(self):
        v = self._make_validator()
        with pytest.raises(AAIError) as exc:
            await v.validate("not-an-aai-key")
        assert exc.value.code == ErrorCode.AUTH_INVALID_API_KEY

    @pytest.mark.asyncio
    async def test_cache_hit_returns_immediately(self):
        cached = CachedAPIKey(
            key_id="k1", tenant_id="t1", scopes=["runs:write"], is_active=True
        )
        v = self._make_validator(cache_result=cached)
        result = await v.validate("aai_live_" + "a" * 64)
        assert result.tenant_id == "t1"
        assert result.scopes == ["runs:write"]

    @pytest.mark.asyncio
    async def test_cache_hit_revoked_raises(self):
        cached = CachedAPIKey(
            key_id="k1", tenant_id="t1", scopes=[], is_active=False
        )
        v = self._make_validator(cache_result=cached)
        with pytest.raises(AAIError) as exc:
            await v.validate("aai_live_" + "a" * 64)
        assert exc.value.code == ErrorCode.AUTH_INVALID_API_KEY

    @pytest.mark.asyncio
    async def test_db_miss_raises(self):
        v = self._make_validator(cache_result=None, db_result=None)
        with pytest.raises(AAIError) as exc:
            await v.validate("aai_live_" + "a" * 64)
        assert exc.value.code == ErrorCode.AUTH_INVALID_API_KEY

    @pytest.mark.asyncio
    async def test_db_hit_populates_cache(self):
        from datetime import datetime, timezone
        db_key = MagicMock()
        db_key.id = "k1"
        db_key.tenant_id = "t1"
        db_key.scopes = ["runs:write"]
        db_key.is_active = True
        db_key.expires_at = None

        tenant = MagicMock()
        tenant.is_suspended = False

        v = self._make_validator(cache_result=None, db_result=db_key, tenant=tenant)
        result = await v.validate("aai_live_" + "a" * 64)
        assert result.tenant_id == "t1"
