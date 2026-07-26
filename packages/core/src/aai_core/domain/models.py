"""Core domain models — schema_version on all persisted types."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TenantTier(StrEnum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"       # HITL waiting
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(StrEnum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    AGENT_SPAWN = "agent_spawn"
    HUMAN_INPUT = "human_input"


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class _Base(BaseModel):
    schema_version: int = 1

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------

class Tenant(_Base):
    id: str = Field(default_factory=_new_id)
    slug: str                               # URL-safe unique identifier
    display_name: str
    tier: TenantTier = TenantTier.STARTER

    # Limits (None = unlimited / controlled by tier defaults)
    max_runs_per_day: int | None = None
    max_concurrent_runs: int = 10
    max_tokens_per_run: int = 100_000
    max_run_duration_seconds: int = 3600

    # Feature flags
    byollm_enabled: bool = False
    knowledge_graph_enabled: bool = False
    hitl_enabled: bool = False

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @field_validator("slug")
    @classmethod
    def _slug_safe(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("slug must be alphanumeric with hyphens/underscores only")
        return v.lower()


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class ToolInputSchema(_Base):
    """JSON-Schema fragment describing one tool's input."""
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class Tool(_Base):
    id: str = Field(default_factory=_new_id)
    tenant_id: str
    name: str                   # machine name, e.g. "legal_kb_search"
    display_name: str
    description: str            # fed to LLM in tool manifest
    input_schema: ToolInputSchema = Field(default_factory=ToolInputSchema)
    output_schema: dict[str, Any] = Field(default_factory=dict)

    plugin_id: str | None = None
    version: str = "1.0.0"
    is_active: bool = True

    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class Agent(_Base):
    id: str = Field(default_factory=_new_id)
    tenant_id: str
    name: str
    description: str = ""

    system_prompt: str = ""
    tool_ids: list[str] = Field(default_factory=list)

    # LLM routing preference — overrides platform default
    preferred_llm_model: str | None = None
    max_tokens_per_step: int = 4096
    temperature: float = 0.0

    # Safety
    max_steps: int = 50
    max_duration_seconds: int = 300

    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# AgentRun
# ---------------------------------------------------------------------------

class AgentRun(_Base):
    id: str = Field(default_factory=_new_id)
    tenant_id: str
    agent_id: str

    status: RunStatus = RunStatus.PENDING
    idempotency_key: str | None = None

    # Input / output
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] | None = None
    error: str | None = None

    # Resumption
    checkpoint_step: int = 0        # last completed step index
    checkpoint_data: dict[str, Any] = Field(default_factory=dict)

    # Cost tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# RunStep
# ---------------------------------------------------------------------------

class RunStep(_Base):
    id: str = Field(default_factory=_new_id)
    run_id: str
    tenant_id: str

    step_index: int
    step_type: StepType
    status: StepStatus = StepStatus.PENDING

    # LLM call fields
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    thinking_tokens: int = 0
    thinking_blocks: list[dict[str, Any]] = Field(default_factory=list)

    # Tool call fields
    tool_id: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: dict[str, Any] | None = None

    # Generic payload
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    output_snapshot: dict[str, Any] = Field(default_factory=dict)

    error: str | None = None
    duration_ms: int | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
