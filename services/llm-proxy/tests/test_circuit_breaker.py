"""Tests for circuit breaker state machine."""
from __future__ import annotations

import asyncio
import pytest

from llm_proxy.circuit_breaker.breaker import CircuitBreaker, CircuitState
from aai_core.errors import AAIError, ErrorCode


async def _ok() -> str:
    return "ok"


async def _fail() -> None:
    raise AAIError(ErrorCode.LLM_PROVIDER_ERROR, "boom", http_status=502)


class TestCircuitBreaker:
    def _breaker(self, threshold: int = 3, cool_down: float = 0.1) -> CircuitBreaker:
        return CircuitBreaker(
            provider_id="test",
            failure_threshold=threshold,
            success_threshold=2,
            cool_down_seconds=cool_down,
        )

    def test_initial_state_closed(self):
        cb = self._breaker()
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_stays_closed(self):
        cb = self._breaker()
        result = await cb.call(_ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failures_trip_to_open(self):
        cb = self._breaker(threshold=3)
        for _ in range(3):
            with pytest.raises(AAIError):
                await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_rejects_immediately(self):
        cb = self._breaker(threshold=1)
        with pytest.raises(AAIError):
            await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

        with pytest.raises(AAIError) as exc:
            await cb.call(_ok)
        assert exc.value.code == ErrorCode.LLM_CIRCUIT_OPEN

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_cooldown(self):
        cb = self._breaker(threshold=1, cool_down=0.05)
        with pytest.raises(AAIError):
            await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.1)
        # Trigger transition check
        try:
            await cb.call(_ok)
        except Exception:
            pass
        assert cb.state in (CircuitState.HALF_OPEN, CircuitState.CLOSED)

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self):
        cb = self._breaker(threshold=1, cool_down=0.05)
        with pytest.raises(AAIError):
            await cb.call(_fail)
        await asyncio.sleep(0.1)

        # Two successes in HALF-OPEN → CLOSED (success_threshold=2)
        await cb.call(_ok)
        await cb.call(_ok)
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self):
        cb = self._breaker(threshold=1, cool_down=0.05)
        with pytest.raises(AAIError):
            await cb.call(_fail)
        await asyncio.sleep(0.1)

        # Force into HALF-OPEN by attempting a call
        try:
            await cb.call(_ok)  # first success
        except Exception:
            pass

        cb._state = CircuitState.HALF_OPEN  # force state for test

        with pytest.raises(AAIError):
            await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

    def test_reset_clears_state(self):
        cb = self._breaker()
        cb._state = CircuitState.OPEN
        cb._failure_count = 10
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    @pytest.mark.asyncio
    async def test_success_resets_failure_counter(self):
        cb = self._breaker(threshold=3)
        # 2 failures (not enough to trip)
        for _ in range(2):
            with pytest.raises(AAIError):
                await cb.call(_fail)
        assert cb.state == CircuitState.CLOSED

        # Success resets count
        await cb.call(_ok)

        # 2 more failures — still below threshold (counter was reset)
        for _ in range(2):
            with pytest.raises(AAIError):
                await cb.call(_fail)
        assert cb.state == CircuitState.CLOSED
