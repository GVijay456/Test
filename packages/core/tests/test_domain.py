"""Tests for core domain models."""
import pytest
from pydantic import ValidationError

from aai_core.domain import AgentRun, RunStatus, Tenant, TenantTier, Tool


class TestTenant:
    def test_defaults(self):
        t = Tenant(slug="acme", display_name="Acme Corp")
        assert t.tier == TenantTier.STARTER
        assert t.schema_version == 1
        assert t.max_concurrent_runs == 10
        assert t.byollm_enabled is False

    def test_slug_normalized_to_lowercase(self):
        t = Tenant(slug="AcmeCorp", display_name="Acme")
        assert t.slug == "acmecorp"

    def test_slug_rejects_special_chars(self):
        with pytest.raises(ValidationError):
            Tenant(slug="acme corp!", display_name="Acme")

    def test_slug_allows_hyphens(self):
        t = Tenant(slug="acme-corp", display_name="Acme")
        assert t.slug == "acme-corp"


class TestAgentRun:
    def test_initial_state(self):
        run = AgentRun(tenant_id="t1", agent_id="a1")
        assert run.status == RunStatus.PENDING
        assert run.checkpoint_step == 0
        assert run.total_cost_usd == 0.0
        assert run.schema_version == 1

    def test_id_is_unique(self):
        r1 = AgentRun(tenant_id="t1", agent_id="a1")
        r2 = AgentRun(tenant_id="t1", agent_id="a1")
        assert r1.id != r2.id

    def test_status_transitions(self):
        run = AgentRun(tenant_id="t1", agent_id="a1")
        run.status = RunStatus.RUNNING
        assert run.status == RunStatus.RUNNING


class TestTool:
    def test_defaults(self):
        tool = Tool(tenant_id="t1", name="search", display_name="Search", description="Searches")
        assert tool.is_active is True
        assert tool.version == "1.0.0"
        assert tool.input_schema.type == "object"
