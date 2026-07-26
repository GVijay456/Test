"""Schema validation for LLM responses.

When a run step expects structured JSON output (e.g. tool call arguments
or a plan JSON), we validate the LLM response against the expected schema
before returning it to the orchestrator.

Validation is best-effort — a schema violation logs a warning and raises
AAIError so the orchestrator can retry or fail the step cleanly.
"""
from __future__ import annotations

import json
from typing import Any

from aai_core.adapters.llm import LLMResponse
from aai_core.errors import AAIError, ErrorCode


def validate_json_response(response: LLMResponse, schema: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate response.content as JSON against schema.

    Only checks required fields and top-level type — not full JSON Schema.
    Use jsonschema library for strict validation in Phase 2.
    """
    content = response.content.strip()

    # Strip markdown code fences if LLM wrapped the JSON
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(
            line for line in lines
            if not line.startswith("```")
        ).strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AAIError(
            ErrorCode.LLM_SCHEMA_VIOLATION,
            f"LLM response is not valid JSON: {exc}",
            http_status=422,
            detail={"raw_content": response.content[:500]},
        )

    if not isinstance(data, dict):
        raise AAIError(
            ErrorCode.LLM_SCHEMA_VIOLATION,
            f"LLM response must be a JSON object, got {type(data).__name__}",
            http_status=422,
        )

    required = schema.get("required", [])
    missing = [k for k in required if k not in data]
    if missing:
        raise AAIError(
            ErrorCode.LLM_SCHEMA_VIOLATION,
            f"LLM response missing required fields: {missing}",
            http_status=422,
            detail={"missing_fields": missing, "got_keys": list(data.keys())},
        )

    return data


def validate_tool_call_arguments(tool_call: dict[str, Any], input_schema: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate a tool call's arguments JSON string."""
    args_raw = tool_call.get("function", {}).get("arguments", "{}")
    try:
        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
    except json.JSONDecodeError as exc:
        raise AAIError(
            ErrorCode.TOOL_SCHEMA_VIOLATION,
            f"Tool call arguments are not valid JSON: {exc}",
            http_status=422,
        )

    required = input_schema.get("required", [])
    missing = [k for k in required if k not in args]
    if missing:
        raise AAIError(
            ErrorCode.TOOL_SCHEMA_VIOLATION,
            f"Tool call missing required arguments: {missing}",
            http_status=422,
            detail={"missing": missing},
        )

    return args
