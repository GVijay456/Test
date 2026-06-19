"""Tests for error codes and AAIError."""
from aai_core.errors import AAIError, ErrorCode


class TestAAIError:
    def test_basic_construction(self):
        err = AAIError(ErrorCode.AUTH_INVALID_API_KEY, "bad key", http_status=401)
        assert err.code == ErrorCode.AUTH_INVALID_API_KEY
        assert err.http_status == 401
        assert err.retriable is False

    def test_to_dict(self):
        err = AAIError(ErrorCode.RUN_NOT_FOUND, "not found", http_status=404)
        d = err.to_dict()
        assert d["error"]["code"] == "AAI-2001"
        assert d["error"]["message"] == "not found"

    def test_not_found_convenience(self):
        err = AAIError.not_found("run", "abc-123")
        assert err.code == ErrorCode.RUN_NOT_FOUND
        assert err.http_status == 404

    def test_rate_limited_is_retriable(self):
        err = AAIError.rate_limited(retry_after=30)
        assert err.retriable is True
        assert err.detail["retry_after"] == 30
        assert err.http_status == 429

    def test_error_codes_format(self):
        for code in ErrorCode:
            assert code.startswith("AAI-"), f"{code} does not follow AAI-XXXX format"
