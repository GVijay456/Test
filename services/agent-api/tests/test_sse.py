"""Tests for SSE streaming."""
import asyncio
import pytest

from agent_api.streaming.sse import RunSSEStream, SSEEvent, RunEvent as EventType


class TestSSEEvent:
    def test_to_sse_bytes_format(self):
        ev = SSEEvent(type="run_started", data={"run_id": "r1"}, id="1")
        s = ev.to_sse_bytes()
        assert "id: 1\n" in s
        assert "event: run_started\n" in s
        assert '"run_id": "r1"' in s
        assert s.endswith("\n\n")

    def test_no_id(self):
        ev = SSEEvent(type="token", data={"delta": "hello"})
        s = ev.to_sse_bytes()
        assert "id:" not in s

    def test_retry_included(self):
        ev = SSEEvent(type="error", data={}, retry=3000)
        assert "retry: 3000" in ev.to_sse_bytes()


class TestRunSSEStream:
    @pytest.mark.asyncio
    async def test_emit_and_receive(self):
        stream = RunSSEStream(run_id="r1", heartbeat_interval=999)
        await stream.emit(SSEEvent(type=EventType.RUN_STARTED, data={"run_id": "r1"}))
        await stream.close()

        events = []
        async for ev in stream.subscribe():
            events.append(ev)

        assert len(events) == 1
        assert events[0].type == EventType.RUN_STARTED

    @pytest.mark.asyncio
    async def test_multiple_events_in_order(self):
        stream = RunSSEStream(run_id="r1", heartbeat_interval=999)

        for i in range(5):
            await stream.emit(SSEEvent(type="token", data={"i": i}))
        await stream.close()

        events = []
        async for ev in stream.subscribe():
            events.append(ev)

        assert len(events) == 5
        for i, ev in enumerate(events):
            assert ev.data["i"] == i

    @pytest.mark.asyncio
    async def test_close_stops_iteration(self):
        stream = RunSSEStream(run_id="r1", heartbeat_interval=999)
        await stream.close()

        events = []
        async for ev in stream.subscribe():
            events.append(ev)

        assert events == []

    @pytest.mark.asyncio
    async def test_producer_consumer_concurrent(self):
        stream = RunSSEStream(run_id="r1", heartbeat_interval=999)
        received = []

        async def consumer():
            async for ev in stream.subscribe():
                received.append(ev.type)

        async def producer():
            await asyncio.sleep(0.01)
            await stream.emit(SSEEvent(type="step_started", data={}))
            await stream.emit(SSEEvent(type="step_done", data={}))
            await stream.close()

        await asyncio.gather(consumer(), producer())
        assert received == ["step_started", "step_done"]
