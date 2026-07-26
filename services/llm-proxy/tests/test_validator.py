"""Tests for LLM response validator."""
import pytest

from llm_proxy.validator import validate_json_response, validate_tool_call_arguments
from aai_core.adapters.llm import LLMResponse
from aai_core.errors import AAIError, ErrorCode


def _resp(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="gpt-4o-mini",
        prompt_tokens=10,
        completion_tokens=20,
        finish_reason="stop",
    )


class TestValidateJSONResponse:
    def test_valid_json_no_schema(self):
        result = validate_json_response(_resp('{"key": "value"}'), {})
        assert result["key"] == "value"

    def test_valid_json_with_required(self):
        schema = {"required": ["name", "score"]}
        result = validate_json_response(_resp('{"name": "Alice", "score": 9}'), schema)
        assert result["name"] == "Alice"

    def test_missing_required_raises(self):
        schema = {"required": ["name", "score"]}
        with pytest.raises(AAIError) as exc:
            validate_json_response(_resp('{"name": "Alice"}'), schema)
        assert exc.value.code == ErrorCode.LLM_SCHEMA_VIOLATION
        assert "score" in exc.value.detail["missing_fields"]

    def test_invalid_json_raises(self):
        with pytest.raises(AAIError) as exc:
            validate_json_response(_resp("this is not json"), {})
        assert exc.value.code == ErrorCode.LLM_SCHEMA_VIOLATION

    def test_strips_markdown_fences(self):
        content = '```json\n{"result": 42}\n```'
        result = validate_json_response(_resp(content), {})
        assert result["result"] == 42

    def test_strips_plain_code_fence(self):
        content = '```\n{"x": 1}\n```'
        result = validate_json_response(_resp(content), {})
        assert result["x"] == 1

    def test_array_response_raises(self):
        with pytest.raises(AAIError) as exc:
            validate_json_response(_resp("[1, 2, 3]"), {})
        assert exc.value.code == ErrorCode.LLM_SCHEMA_VIOLATION


class TestValidateToolCallArguments:
    def test_valid_args(self):
        tc = {"function": {"name": "search", "arguments": '{"query": "hello"}'}}
        schema = {"required": ["query"]}
        result = validate_tool_call_arguments(tc, schema)
        assert result["query"] == "hello"

    def test_missing_required_arg(self):
        tc = {"function": {"name": "search", "arguments": '{}'}}
        schema = {"required": ["query"]}
        with pytest.raises(AAIError) as exc:
            validate_tool_call_arguments(tc, schema)
        assert exc.value.code == ErrorCode.TOOL_SCHEMA_VIOLATION

    def test_invalid_json_args(self):
        tc = {"function": {"name": "search", "arguments": "not json"}}
        with pytest.raises(AAIError):
            validate_tool_call_arguments(tc, {})

    def test_dict_args_pass_through(self):
        tc = {"function": {"name": "search", "arguments": {"query": "hello"}}}
        result = validate_tool_call_arguments(tc, {"required": ["query"]})
        assert result["query"] == "hello"
