"""Tokenizer registry — auto-select by model name."""
from __future__ import annotations

import re
from .base import Tokenizer


class _TiktokenTokenizer(Tokenizer):
    """tiktoken for OpenAI / GPT-4 family."""

    @property
    def model_pattern(self) -> str:
        return r"^(gpt-|o1|o3|text-embedding)"

    def __init__(self, encoding: str = "cl100k_base") -> None:
        import tiktoken
        # May raise on first use if BPE file cannot be downloaded
        self._enc = tiktoken.get_encoding(encoding)

    def count(self, text: str) -> int:
        return len(self._enc.encode(text))

    def _lazy_init(self, encoding: str) -> None:
        import tiktoken
        if not hasattr(self, "_enc"):
            self._enc = tiktoken.get_encoding(encoding)


class _EstimateTokenizer(Tokenizer):
    """Fallback — char/4 heuristic. Accurate to ±15%."""

    @property
    def model_pattern(self) -> str:
        return r".*"    # matches everything as fallback

    def count(self, text: str) -> int:
        return max(1, len(text) // 4)


class TokenizerRegistry:
    """Maps model names to Tokenizer instances.

    Tokenizers are instantiated lazily and cached.
    New tokenizers can be registered at startup without changing this file.
    """

    def __init__(self) -> None:
        self._registered: list[Tokenizer] = []
        self._cache: dict[str, Tokenizer] = {}

    def register(self, tokenizer: Tokenizer) -> None:
        self._registered.insert(0, tokenizer)  # later registrations take priority

    def get(self, model: str) -> Tokenizer:
        if model in self._cache:
            return self._cache[model]
        for tok in self._registered:
            if re.match(tok.model_pattern, model):
                self._cache[model] = tok
                return tok
        fallback = _EstimateTokenizer()
        self._cache[model] = fallback
        return fallback


_registry = TokenizerRegistry()

# Register built-ins — order matters: last registered wins for overlapping patterns
_registry.register(_EstimateTokenizer())  # lowest priority fallback

try:
    _registry.register(_TiktokenTokenizer())
except Exception:
    # tiktoken optional; also catches network errors when BPE file is unavailable
    pass


def get_tokenizer(model: str) -> Tokenizer:
    """Global convenience function."""
    return _registry.get(model)
