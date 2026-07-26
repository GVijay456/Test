"""Per-provider circuit breaker — CLOSED / OPEN / HALF-OPEN.

States:
  CLOSED    — normal operation; failures increment a counter
  OPEN      — all calls rejected immediately; reset after cool-down window
  HALF-OPEN — one probe call allowed; success → CLOSED, failure → OPEN

Thresholds (configurable per provider):
  failure_threshold   — consecutive failures to trip to OPEN  (default 5)
  success_threshold   — consecutive successes in HALF-OPEN to close (default 2)
  cool_down_seconds   — time in OPEN before moving to HALF-OPEN (default 30)
"""
from __future__ import annotations

import asyncio
import time
from enum import StrEnum
from typing import Any, Callable, Awaitable, TypeVar

from aai_core.errors import AAIError, ErrorCode

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        provider_id: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        cool_down_seconds: float = 30.0,
    ) -> None:
        self.provider_id = provider_id
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._cool_down = cool_down_seconds

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def call(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute fn, tracking success/failure to drive state transitions."""
        async with self._lock:
            await self._maybe_transition()

            if self._state == CircuitState.OPEN:
                raise AAIError(
                    ErrorCode.LLM_CIRCUIT_OPEN,
                    f"Circuit breaker OPEN for provider {self.provider_id!r}. "
                    f"Retry in {self._seconds_until_half_open():.0f}s.",
                    http_status=503,
                    retriable=True,
                    detail={"provider": self.provider_id, "state": self._state},
                )

        try:
            result = await fn(*args, **kwargs)
            await self._on_success()
            return result
        except AAIError as exc:
            if exc.http_status >= 500 or exc.code == ErrorCode.LLM_RATE_LIMITED:
                await self._on_failure()
            raise
        except Exception:
            await self._on_failure()
            raise

    async def _maybe_transition(self) -> None:
        """Check if we should move from OPEN → HALF-OPEN based on cool-down."""
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self._cool_down:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0  # reset on success

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            if self._state == CircuitState.HALF_OPEN:
                # Single failure in HALF-OPEN → back to OPEN
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._failure_count = 0
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self._failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._failure_count = 0

    def _seconds_until_half_open(self) -> float:
        if self._opened_at is None:
            return 0.0
        return max(0.0, self._cool_down - (time.monotonic() - self._opened_at))

    def reset(self) -> None:
        """Force-reset to CLOSED — for testing and admin use."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
