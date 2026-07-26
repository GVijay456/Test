"""Add thinking_tokens and thinking_blocks to run_steps.

Supports reasoning models (o3, Claude extended thinking, DeepSeek R1) that
emit thinking blocks alongside the main response.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "run_steps",
        sa.Column(
            "thinking_tokens",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "run_steps",
        sa.Column(
            "thinking_blocks",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("run_steps", "thinking_blocks")
    op.drop_column("run_steps", "thinking_tokens")
