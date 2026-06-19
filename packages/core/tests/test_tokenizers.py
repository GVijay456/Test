"""Tests for tokenizer registry."""
from aai_core.tokenizers import get_tokenizer


class TestTokenizerRegistry:
    def test_estimate_fallback(self):
        tok = get_tokenizer("unknown-model-xyz")
        count = tok.count("hello world")
        assert count > 0

    def test_count_messages(self):
        tok = get_tokenizer("unknown-model")
        msgs = [{"role": "user", "content": "hello"}]
        total = tok.count_messages(msgs)
        assert total > 0

    def test_tiktoken_openai(self):
        # tiktoken may not be installed in CI, so we accept either tokenizer
        tok = get_tokenizer("gpt-4o")
        count = tok.count("The quick brown fox")
        assert count > 0

    def test_same_model_returns_cached(self):
        tok1 = get_tokenizer("gpt-4o-mini")
        tok2 = get_tokenizer("gpt-4o-mini")
        assert tok1 is tok2
