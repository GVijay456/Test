"""Tests for internal JWT minting and verification."""
import time

import pytest

from auth.core.jwt_minter import InternalJWTMinter
from aai_core.adapters.auth import AuthResult
from aai_core.errors import AAIError, ErrorCode


class TestInternalJWTMinter:
    def _minter(self, ttl: int = 300) -> InternalJWTMinter:
        return InternalJWTMinter(secret="test-secret-32chars-padding!!!!!", ttl_seconds=ttl)

    def test_mint_and_decode(self):
        minter = self._minter()
        auth = AuthResult(tenant_id="t1", user_id="u1", scopes=["runs:write"])
        token = minter.mint(auth)
        claims = minter.decode(token)
        assert claims["tenant_id"] == "t1"
        assert claims["sub"] == "u1"
        assert "runs:write" in claims["scopes"]

    def test_api_key_user_sub(self):
        minter = self._minter()
        auth = AuthResult(tenant_id="t1", user_id=None, scopes=[])
        token = minter.mint(auth)
        claims = minter.decode(token)
        assert claims["sub"] == "api-key"

    def test_expired_raises(self):
        minter = self._minter(ttl=1)
        auth = AuthResult(tenant_id="t1", user_id="u1", scopes=[])
        token = minter.mint(auth)
        time.sleep(2)
        with pytest.raises(AAIError) as exc:
            minter.decode(token)
        assert exc.value.code == ErrorCode.AUTH_JWT_INVALID

    def test_wrong_secret_raises(self):
        minter_a = self._minter()
        minter_b = InternalJWTMinter(secret="completely-different-secret!!!!!")
        auth = AuthResult(tenant_id="t1", user_id="u1", scopes=[])
        token = minter_a.mint(auth)
        with pytest.raises(AAIError):
            minter_b.decode(token)

    def test_token_has_expiry(self):
        minter = self._minter(ttl=300)
        auth = AuthResult(tenant_id="t1", user_id="u1", scopes=[])
        token = minter.mint(auth)
        claims = minter.decode(token)
        assert claims["exp"] > int(time.time())
        assert claims["exp"] <= int(time.time()) + 300 + 2  # +2 for test timing
