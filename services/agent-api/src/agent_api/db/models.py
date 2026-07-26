"""SQLAlchemy ORM models — agent_runs, run_steps, agents."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index,
    Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    tool_ids: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="[]")
    preferred_llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    max_tokens_per_step: Mapped[int] = mapped_column(Integer, nullable=False, server_default="4096")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")
    max_steps: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    max_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="300")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_agents_tenant", "tenant_id", "is_active"),
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    input: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resumption checkpoint
    checkpoint_step: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    checkpoint_data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    # Cost
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")

    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_runs_tenant_status", "tenant_id", "status"),
        Index("ix_runs_agent", "agent_id"),
    )


class RunStep(Base):
    __tablename__ = "run_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")

    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")
    thinking_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    thinking_blocks: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="[]")

    tool_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tool_input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    input_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    output_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_steps_run_idx", "run_id", "step_index"),
    )
