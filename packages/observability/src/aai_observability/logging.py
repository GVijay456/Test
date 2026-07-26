"""Structured JSON logging via structlog.

Every log line includes: timestamp, level, service, trace_id, span_id,
request_id, run_id, tenant_id — injected from context vars automatically.

Usage:
    from aai_observability import get_logger
    log = get_logger()
    log.info("event_name", run_id="...", cost_usd=0.03)
"""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog
from opentelemetry import trace

# Context vars — set at request middleware level
_run_id_var: ContextVar[str] = ContextVar("run_id", default="")
_tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="")
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def _add_otel_context(logger, method, event_dict):
    """Inject current trace/span IDs into every log record."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def _add_app_context(logger, method, event_dict):
    """Inject run/tenant/request IDs from context vars."""
    if run_id := _run_id_var.get():
        event_dict["run_id"] = run_id
    if tenant_id := _tenant_id_var.get():
        event_dict["tenant_id"] = tenant_id
    if request_id := _request_id_var.get():
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Configure structlog for the service. Call once at startup."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_otel_context,
            _add_app_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    )
    # Also configure stdlib logging to go through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(level.upper()),
    )


def get_logger(name: str = "") -> structlog.BoundLogger:
    return structlog.get_logger(name)


def set_run_context(
    run_id: str = "",
    tenant_id: str = "",
    request_id: str = "",
) -> None:
    """Set context vars for the current async task/request."""
    if run_id:
        _run_id_var.set(run_id)
    if tenant_id:
        _tenant_id_var.set(tenant_id)
    if request_id:
        _request_id_var.set(request_id)
