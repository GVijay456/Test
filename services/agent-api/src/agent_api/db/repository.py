"""DB queries for agent run lifecycle."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aai_core.domain import RunStatus, StepStatus

from .models import Agent, AgentRun, RunStep


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Agents ──────────────────────────────────────────────────────────────

    async def get_agent(self, agent_id: str, tenant_id: str) -> Agent | None:
        r = await self._s.execute(
            select(Agent).where(Agent.id == agent_id, Agent.tenant_id == tenant_id, Agent.is_active.is_(True))
        )
        return r.scalar_one_or_none()

    # ── Runs ─────────────────────────────────────────────────────────────────

    async def get_run(self, run_id: str, tenant_id: str) -> AgentRun | None:
        r = await self._s.execute(
            select(AgentRun).where(AgentRun.id == run_id, AgentRun.tenant_id == tenant_id)
        )
        return r.scalar_one_or_none()

    async def get_run_by_idempotency_key(self, key: str, tenant_id: str) -> AgentRun | None:
        r = await self._s.execute(
            select(AgentRun).where(
                AgentRun.idempotency_key == key,
                AgentRun.tenant_id == tenant_id,
            )
        )
        return r.scalar_one_or_none()

    async def create_run(
        self,
        tenant_id: str,
        agent_id: str,
        input_data: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> AgentRun:
        run = AgentRun(
            tenant_id=tenant_id,
            agent_id=agent_id,
            input=input_data,
            idempotency_key=idempotency_key,
            status=RunStatus.PENDING,
        )
        self._s.add(run)
        await self._s.commit()
        await self._s.refresh(run)
        return run

    async def update_run_status(
        self,
        run_id: str,
        status: RunStatus,
        error: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> None:
        values: dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        if status == RunStatus.RUNNING:
            values["started_at"] = datetime.now(timezone.utc)
        if status in (RunStatus.DONE, RunStatus.FAILED, RunStatus.CANCELLED):
            values["completed_at"] = datetime.now(timezone.utc)
        if error is not None:
            values["error"] = error
        if output is not None:
            values["output"] = output

        await self._s.execute(
            update(AgentRun).where(AgentRun.id == run_id).values(**values)
        )
        await self._s.commit()

    async def write_checkpoint(
        self,
        run_id: str,
        step_index: int,
        checkpoint_data: dict[str, Any],
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Write durable checkpoint before each step — enables resumption."""
        await self._s.execute(
            update(AgentRun)
            .where(AgentRun.id == run_id)
            .values(
                checkpoint_step=step_index,
                checkpoint_data=checkpoint_data,
                total_input_tokens=AgentRun.total_input_tokens + input_tokens,
                total_output_tokens=AgentRun.total_output_tokens + output_tokens,
                total_cost_usd=AgentRun.total_cost_usd + cost_usd,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._s.commit()

    # ── Steps ─────────────────────────────────────────────────────────────────

    async def create_step(
        self,
        run_id: str,
        tenant_id: str,
        step_index: int,
        step_type: str,
    ) -> RunStep:
        step = RunStep(
            run_id=run_id,
            tenant_id=tenant_id,
            step_index=step_index,
            step_type=step_type,
            status=StepStatus.PENDING,
        )
        self._s.add(step)
        await self._s.commit()
        await self._s.refresh(step)
        return step

    async def update_step(
        self,
        step_id: str,
        status: StepStatus,
        output_snapshot: dict[str, Any] | None = None,
        error: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        duration_ms: int | None = None,
        model: str | None = None,
    ) -> None:
        values: dict[str, Any] = {
            "status": status,
        }
        if status == StepStatus.RUNNING:
            values["started_at"] = datetime.now(timezone.utc)
        if status in (StepStatus.DONE, StepStatus.FAILED):
            values["completed_at"] = datetime.now(timezone.utc)
        if output_snapshot is not None:
            values["output_snapshot"] = output_snapshot
        if error is not None:
            values["error"] = error
        if prompt_tokens:
            values["prompt_tokens"] = prompt_tokens
        if completion_tokens:
            values["completion_tokens"] = completion_tokens
        if cost_usd:
            values["cost_usd"] = cost_usd
        if duration_ms is not None:
            values["duration_ms"] = duration_ms
        if model is not None:
            values["model"] = model

        await self._s.execute(update(RunStep).where(RunStep.id == step_id).values(**values))
        await self._s.commit()

    async def list_steps(self, run_id: str) -> list[RunStep]:
        r = await self._s.execute(
            select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.step_index)
        )
        return list(r.scalars())
