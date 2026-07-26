"""SSE streaming for agent run events.

Architecture: orchestrator publishes events to NATS subject
  aai.runs.events.{tenant_id}.{run_id}

SSE endpoint subscribes to that subject and fans out to the HTTP client.
Multiple SSE clients can subscribe to the same run simultaneously.
Supports resume-from-sequence via Last-Event-ID header.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from typing import Any, AsyncIterator


@dataclass
class SSEEvent:
    """A single SSE event emitted to the client."""
    type: str                           # e.g. "run_started", "step_done", "token"
    data: dict[str, Any] = field(default_factory=dict)
    id: str | None = None              # sequence ID for Last-Event-ID resume
    retry: int | None = None           # reconnect delay hint (ms)

    def to_sse_bytes(self) -> str:
        lines = []
        if self.id is not None:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.type}")
        lines.append(f"data: {json.dumps(self.data)}")
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        lines.append("")  # blank line terminates event
        return "\n".join(lines) + "\n"


# Standard event types
class RunEvent:
    RUN_STARTED    = "run_started"
    RUN_DONE       = "run_done"
    RUN_FAILED     = "run_failed"
    RUN_CANCELLED  = "run_cancelled"
    STEP_STARTED   = "step_started"
    STEP_DONE      = "step_done"
    STEP_FAILED    = "step_failed"
    TOKEN          = "token"            # LLM streaming token
    TOOL_CALL      = "tool_call"
    TOOL_RESULT    = "tool_result"
    HITL_REQUESTED = "hitl_requested"
    ERROR          = "error"
    HEARTBEAT      = "heartbeat"


class RunSSEStream:
    """In-process event bus for a single run's SSE stream.

    Orchestrator calls emit(); SSE endpoint iterates subscribe().
    For multi-pod deployments, replace with NATS subscriber.
    """

    def __init__(self, run_id: str, heartbeat_interval: float = 15.0) -> None:
        self._run_id = run_id
        self._queue: asyncio.Queue[SSEEvent | None] = asyncio.Queue()
        self._heartbeat_interval = heartbeat_interval
        self._closed = False

    async def emit(self, event: SSEEvent) -> None:
        """Publish an event to all subscribers."""
        if not self._closed:
            await self._queue.put(event)

    async def close(self) -> None:
        """Signal end-of-stream to all subscribers."""
        self._closed = True
        await self._queue.put(None)  # sentinel

    async def subscribe(self) -> AsyncIterator[SSEEvent]:
        """Yield events until the stream is closed or client disconnects."""
        heartbeat_task = asyncio.create_task(self._heartbeat())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=self._heartbeat_interval,
                    )
                    if event is None:   # sentinel → stream ended
                        break
                    yield event
                except asyncio.TimeoutError:
                    yield SSEEvent(type=RunEvent.HEARTBEAT, data={"run_id": self._run_id})
        finally:
            heartbeat_task.cancel()

    async def _heartbeat(self) -> None:
        """Keep-alive — prevents proxy/load-balancer from closing idle SSE connections."""
        while not self._closed:
            await asyncio.sleep(self._heartbeat_interval)
