"""Initial agent-api schema — agents, agent_runs, run_steps.

Revision ID: 0001
Revises:
Create Date: 2026-06-19
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("system_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("tool_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("preferred_llm_model", sa.String(128), nullable=True),
        sa.Column("max_tokens_per_step", sa.Integer, nullable=False, server_default="4096"),
        sa.Column("temperature", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("max_steps", sa.Integer, nullable=False, server_default="50"),
        sa.Column("max_duration_seconds", sa.Integer, nullable=False, server_default="300"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agents_tenant", "agents", ["tenant_id", "is_active"])

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(255), nullable=True, unique=True),
        sa.Column("input", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("output", postgresql.JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("checkpoint_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("checkpoint_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("total_input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_runs_tenant_status", "agent_runs", ["tenant_id", "status"])
    op.create_index("ix_runs_agent", "agent_runs", ["agent_id"])

    op.create_table(
        "run_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("step_index", sa.Integer, nullable=False),
        sa.Column("step_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("tool_id", sa.String(36), nullable=True),
        sa.Column("tool_input", postgresql.JSONB, nullable=True),
        sa.Column("tool_output", postgresql.JSONB, nullable=True),
        sa.Column("input_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("output_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_steps_run_idx", "run_steps", ["run_id", "step_index"])


def downgrade() -> None:
    op.drop_table("run_steps")
    op.drop_table("agent_runs")
    op.drop_table("agents")
