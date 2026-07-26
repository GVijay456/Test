"""Parallel tool executor.

When an LLM returns multiple tool_calls in a single response (a pattern that
became standard in 2025–2026), fan them out concurrently with asyncio.gather
rather than running them serially.  This alone can cut wall-clock time by 60–80%
on multi-retrieval steps.

Usage:
    executor = ParallelToolExecutor(registry=tool_registry)
    results  = await executor.execute_all(tool_calls)
    # results is a list aligned 1-to-1 with tool_calls
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from aai_observability import get_logger

log = get_logger(__name__)

# Type alias for a tool callable loaded from the registry
ToolCallable = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class ToolCallResult:
    """Result for one tool call in the parallel batch."""

    __slots__ = ("tool_call_id", "tool_name", "output", "error", "duration_ms")

    def __init__(
        self,
        tool_call_id: str,
        tool_name: str,
        output: dict[str, Any] | None,
        error: str | None,
        duration_ms: int,
    ) -> None:
        self.tool_call_id = tool_call_id
        self.tool_name = tool_name
        self.output = output
        self.error = error
        self.duration_ms = duration_ms

    @property
    def succeeded(self) -> bool:
        return self.error is None


class ParallelToolExecutor:
    """Fan-out multiple tool_calls from a single LLM response.

    Args:
        registry: Mapping from tool name → async callable. The callable
            receives the tool arguments dict and returns the output dict.
        max_concurrency: Hard cap on simultaneous tool invocations (default 10).
            Prevents runaway parallelism if an LLM hallucinates many calls.
        timeout_seconds: Per-tool execution timeout (default 30s).
    """

    def __init__(
        self,
        registry: dict[str, ToolCallable],
        max_concurrency: int = 10,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._registry = registry
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = timeout_seconds

    async def execute_all(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[ToolCallResult]:
        """Execute all tool_calls concurrently and return aligned results.

        Each element in the returned list corresponds to the tool_call at the
        same index.  Failed tools produce a result with error set rather than
        raising, so partial success is visible to the orchestrator.
        """
        if not tool_calls:
            return []

        tasks = [self._execute_one(tc) for tc in tool_calls]
        results: list[ToolCallResult] = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def _execute_one(self, tool_call: dict[str, Any]) -> ToolCallResult:
        call_id = tool_call.get("id", "")
        name = tool_call.get("function", {}).get("name", "") or tool_call.get("name", "")
        raw_args = tool_call.get("function", {}).get("arguments", {}) or tool_call.get("arguments", {})
        arguments: dict[str, Any] = raw_args if isinstance(raw_args, dict) else {}

        fn = self._registry.get(name)
        if fn is None:
            return ToolCallResult(
                tool_call_id=call_id,
                tool_name=name,
                output=None,
                error=f"Tool '{name}' not found in registry",
                duration_ms=0,
            )

        async with self._semaphore:
            t0 = time.monotonic()
            try:
                output = await asyncio.wait_for(fn(arguments), timeout=self._timeout)
                duration_ms = int((time.monotonic() - t0) * 1000)
                log.debug("tool_call_ok", tool=name, call_id=call_id, duration_ms=duration_ms)
                return ToolCallResult(
                    tool_call_id=call_id,
                    tool_name=name,
                    output=output,
                    error=None,
                    duration_ms=duration_ms,
                )
            except asyncio.TimeoutError:
                duration_ms = int((time.monotonic() - t0) * 1000)
                log.warning("tool_call_timeout", tool=name, call_id=call_id, timeout=self._timeout)
                return ToolCallResult(
                    tool_call_id=call_id,
                    tool_name=name,
                    output=None,
                    error=f"Tool '{name}' timed out after {self._timeout}s",
                    duration_ms=duration_ms,
                )
            except Exception as exc:  # noqa: BLE001
                duration_ms = int((time.monotonic() - t0) * 1000)
                log.error("tool_call_failed", tool=name, call_id=call_id, exc_info=exc)
                return ToolCallResult(
                    tool_call_id=call_id,
                    tool_name=name,
                    output=None,
                    error=str(exc),
                    duration_ms=duration_ms,
                )

    def build_tool_results_messages(
        self, results: list[ToolCallResult]
    ) -> list[dict[str, Any]]:
        """Convert results into the tool_results message list for the next LLM turn.

        The returned messages follow the OpenAI tool result format; LiteLLM
        normalises this for non-OpenAI providers automatically.
        """
        return [
            {
                "role": "tool",
                "tool_call_id": r.tool_call_id,
                "content": str(r.output) if r.succeeded else f"Error: {r.error}",
            }
            for r in results
        ]
