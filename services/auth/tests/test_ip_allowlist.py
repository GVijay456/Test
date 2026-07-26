"""Tests for IP allowlist enforcement."""
import pytest

from auth.core.ip_allowlist import check_ip_allowlist
from aai_core.errors import AAIError, ErrorCode


class TestIPAllowlist:
    def test_empty_allowlist_allows_all(self):
        check_ip_allowlist("1.2.3.4", [])   # no raise

    def test_exact_match_allowed(self):
        check_ip_allowlist("10.0.0.1", ["10.0.0.1"])  # no raise

    def test_non_match_blocked(self):
        with pytest.raises(AAIError) as exc:
            check_ip_allowlist("10.0.0.2", ["10.0.0.1"])
        assert exc.value.code == ErrorCode.AUTH_IP_BLOCKED

    def test_cidr_match_allowed(self):
        check_ip_allowlist("10.0.0.99", ["10.0.0.0/24"])  # no raise

    def test_cidr_non_match_blocked(self):
        with pytest.raises(AAIError):
            check_ip_allowlist("192.168.1.1", ["10.0.0.0/8"])

    def test_multiple_entries(self):
        check_ip_allowlist("172.16.0.5", ["10.0.0.1", "172.16.0.0/16"])

    def test_malformed_entry_skipped(self):
        with pytest.raises(AAIError):
            check_ip_allowlist("1.2.3.4", ["not-an-ip", "5.6.7.8"])

    def test_malformed_client_ip_raises(self):
        with pytest.raises(AAIError) as exc:
            check_ip_allowlist("not-an-ip", ["10.0.0.1"])
        assert exc.value.code == ErrorCode.AUTH_IP_BLOCKED
