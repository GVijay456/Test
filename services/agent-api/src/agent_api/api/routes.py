"""Agent API routes.

POST /v1/runs              — create + enqueue a run
GET  /v1/runs/{id}         — get run status
GET  /v1/runs/{id}/stream  — SSE stream of run events
POST /v1/runs/{id}/cancel  — cancel a run
GET  /internal/health/live
GET  /internal/health/ready
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from aai_core.domain import RunStatus
from aai_core.errors import AAIError, ErrorCode

from ..db.repository import RunRepository
from ..state_machine.run_fsm import RunEvent, RunStateMachine
from ..streaming.sse import RunEvent as SSEEventType, RunSSEStream, SSEEvent

router = APIRouter()


# ── Request / response models ─────────────────────────────────────────────────

class CreateRunRequest(BaseModel):
    agent_id: str
    input: dict[str, Any] = {}
    idempotency_key: str | None = None


class RunResponse(BaseModel):
    id: str
    tenant_id: str
    agent_id: str
    status: str
    checkpoint_step: int
    total_cost_usd: float
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


def _run_to_response(run) -> RunResponse:
    return RunResponse(
        id=run.id,
        tenant_id=run.tenant_id,
        agent_id=run.agent_id,
        status=run.status,
        checkpoint_step=run.checkpoint_step,
        total_cost_usd=run.total_cost_usd,
        created_at=run.created_at.isoformat(),
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        output=run.output,
        error=run.error,
    )


def _get_tenant_id(request: Request) -> str:
    """Extract tenant_id from the internal JWT claims (set by auth middleware)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant context")
    return tenant_id


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/v1/runs", response_model=RunResponse, status_code=201)
async def create_run(body: CreateRunRequest, request: Request):
    tenant_id = _get_tenant_id(request)
    repo: RunRepository = request.app.state.run_repo_factory()

    # Idempotency: return existing run if key already used
    if body.idempotency_key:
        existing = await repo.get_run_by_idempotency_key(body.idempotency_key, tenant_id)
        if existing is not None:
            return _run_to_response(existing)

    # Verify agent exists for this tenant
    agent = await repo.get_agent(body.agent_id, tenant_id)
    if agent is None:
        raise AAIError.not_found("agent", body.agent_id)

    run = await repo.create_run(
        tenant_id=tenant_id,
        agent_id=body.agent_id,
        input_data=body.input,
        idempotency_key=body.idempotency_key,
    )

    # Publish to orchestrator via NATS
    bus = request.app.state.message_bus
    await bus.publish_run_created(run.id, tenant_id, body.agent_id, body.input)

    return _run_to_response(run)


@router.get("/v1/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, request: Request):
    tenant_id = _get_tenant_id(request)
    repo: RunRepository = request.app.state.run_repo_factory()
    run = await repo.get_run(run_id, tenant_id)
    if run is None:
        raise AAIError.not_found("run", run_id)
    return _run_to_response(run)


@router.get("/v1/runs/{run_id}/stream")
async def stream_run(run_id: str, request: Request):
    """SSE endpoint — streams run events until completion or disconnect."""
    tenant_id = _get_tenant_id(request)

    # Get or create stream for this run
    streams: dict[str, RunSSEStream] = request.app.state.run_streams
    if run_id not in streams:
        # Run may already be done — fall back to polling DB for status
        repo: RunRepository = request.app.state.run_repo_factory()
        run = await repo.get_run(run_id, tenant_id)
        if run is None:
            raise AAIError.not_found("run", run_id)

        if run.status in (RunStatus.DONE, RunStatus.FAILED, RunStatus.CANCELLED):
            async def _done_stream():
                event = SSEEvent(
                    type=SSEEventType.RUN_DONE if run.status == RunStatus.DONE else SSEEventType.RUN_FAILED,
                    data={"run_id": run_id, "status": run.status, "output": run.output},
                )
                yield event.to_sse_bytes()
            return StreamingResponse(_done_stream(), media_type="text/event-stream")

        stream = RunSSEStream(run_id=run_id)
        streams[run_id] = stream

    stream = streams[run_id]

    async def _event_generator():
        async for event in stream.subscribe():
            yield event.to_sse_bytes()
            if event.type in (SSEEventType.RUN_DONE, SSEEventType.RUN_FAILED, SSEEventType.RUN_CANCELLED):
                break

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",     # disable nginx buffering
        },
    )


@router.post("/v1/runs/{run_id}/cancel")
async def cancel_run(run_id: str, request: Request):
    tenant_id = _get_tenant_id(request)
    repo: RunRepository = request.app.state.run_repo_factory()
    run = await repo.get_run(run_id, tenant_id)
    if run is None:
        raise AAIError.not_found("run", run_id)

    fsm = RunStateMachine(RunStatus(run.status))
    if not fsm.can(RunEvent.CANCEL):
        raise AAIError(
            ErrorCode.RUN_CANCELLED,
            f"Run in status {run.status!r} cannot be cancelled",
            http_status=409,
        )

    await repo.update_run_status(run_id, RunStatus.CANCELLED)

    # Signal orchestrator via NATS
    bus = request.app.state.message_bus
    await bus.publish_run_cancelled(run_id, tenant_id)

    return {"cancelled": True, "run_id": run_id}


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/internal/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/internal/health/ready")
async def readiness(request: Request):
    checks: dict[str, str] = {}
    try:
        request.app.state.db_engine
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "error"
    return {"status": "ok" if all(v == "ok" for v in checks.values()) else "degraded", "checks": checks}
