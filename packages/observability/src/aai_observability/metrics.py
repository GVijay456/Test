"""Platform-wide Prometheus / OTEL metrics.

All services import AAIMetrics and use the shared instrument names so
Grafana dashboards work across the fleet without config changes.

Instruments follow the OpenMetrics naming convention:
  aai_<subsystem>_<name>_<unit>
"""
from __future__ import annotations

from opentelemetry import metrics

_meter = metrics.get_meter("aai.platform", version="0.1.0")


class AAIMetrics:
    # ── HTTP / gateway ────────────────────────────────────────────────────
    http_requests_total = _meter.create_counter(
        "aai_http_requests_total",
        description="Total HTTP requests by service, method, path, status",
        unit="1",
    )
    http_request_duration = _meter.create_histogram(
        "aai_http_request_duration_seconds",
        description="HTTP request latency",
        unit="s",
    )

    # ── Agent runs ────────────────────────────────────────────────────────
    runs_created_total = _meter.create_counter(
        "aai_runs_created_total",
        description="Total agent runs created",
        unit="1",
    )
    runs_completed_total = _meter.create_counter(
        "aai_runs_completed_total",
        description="Total agent runs completed by status",
        unit="1",
    )
    run_duration = _meter.create_histogram(
        "aai_run_duration_seconds",
        description="Agent run wall-clock time",
        unit="s",
    )
    run_steps_total = _meter.create_counter(
        "aai_run_steps_total",
        description="Total steps executed by type",
        unit="1",
    )

    # ── LLM ───────────────────────────────────────────────────────────────
    llm_requests_total = _meter.create_counter(
        "aai_llm_requests_total",
        description="Total LLM requests by provider and model",
        unit="1",
    )
    llm_tokens_total = _meter.create_counter(
        "aai_llm_tokens_total",
        description="Total LLM tokens by direction (prompt/completion) and model",
        unit="1",
    )
    llm_cost_usd_total = _meter.create_counter(
        "aai_llm_cost_usd_total",
        description="Total LLM cost in USD",
        unit="USD",
    )
    llm_latency = _meter.create_histogram(
        "aai_llm_latency_seconds",
        description="LLM request latency by provider and model",
        unit="s",
    )
    llm_circuit_trips_total = _meter.create_counter(
        "aai_llm_circuit_trips_total",
        description="Circuit breaker trips by provider",
        unit="1",
    )

    # ── Auth ─────────────────────────────────────────────────────────────
    auth_validations_total = _meter.create_counter(
        "aai_auth_validations_total",
        description="Auth validation attempts by type (api_key/jwt) and result",
        unit="1",
    )
    auth_cache_hits_total = _meter.create_counter(
        "aai_auth_cache_hits_total",
        description="Auth Redis cache hits vs misses",
        unit="1",
    )

    # ── Memory / RAG ─────────────────────────────────────────────────────
    rag_retrievals_total = _meter.create_counter(
        "aai_rag_retrievals_total",
        description="RAG retrieval requests by collection",
        unit="1",
    )
    rag_retrieval_latency = _meter.create_histogram(
        "aai_rag_retrieval_latency_seconds",
        description="RAG retrieval latency",
        unit="s",
    )
