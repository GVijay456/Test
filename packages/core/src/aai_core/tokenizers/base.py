"""Tokenizer abstraction — count tokens without importing provider SDKs."""
from __future__ import annotations

from abc import ABC, abstractmethod


class Tokenizer(ABC):
    @property
    @abstractmethod
    def model_pattern(self) -> str:
        """Regex matched against model name to select this tokenizer."""

    @abstractmethod
    def count(self, text: str) -> int:
        """Return token count for the given text."""

    def count_messages(self, messages: list[dict]) -> int:
        """Count tokens across a messages list (chat format)."""
        total = 0
        for m in messages:
            total += self.count(str(m.get("content", "")))
            total += 4  # per-message overhead
        total += 2  # priming tokens
        return total
