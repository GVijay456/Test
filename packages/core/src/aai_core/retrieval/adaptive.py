"""Adaptive retrieval — skip RAG when the source document fits in context.

Modern context windows (128k–2M tokens) often make RAG retrieval unnecessary
for small or medium corpora.  Skipping retrieval removes latency, avoids
chunking artefacts, and eliminates false-negative recall from vector search.

Decision flow:
    1. Estimate token count of the full source document(s).
    2. If total fits within the remaining context budget → load full document.
    3. Otherwise → invoke RAG retrieval pipeline.

Usage:
    strategy = AdaptiveRetrieval(tokenizer_registry=registry)
    decision  = strategy.decide(doc_token_estimate=3_500, context_budget=8_000)
    if decision == RetrievalStrategy.FULL_CONTEXT:
        text = load_full_document(doc_id)
    else:
        chunks = await rag_retrieve(query)
"""
from __future__ import annotations

from enum import StrEnum
from typing import Protocol


class RetrievalStrategy(StrEnum):
    FULL_CONTEXT = "full_context"   # load entire document
    RAG = "rag"                     # chunked vector retrieval


class TokenEstimator(Protocol):
    def estimate(self, text: str) -> int:
        """Return approximate token count for *text*."""
        ...


class AdaptiveRetrieval:
    """Decides whether to use full-context loading or RAG retrieval.

    Args:
        rag_overhead_tokens: Token budget consumed by RAG plumbing (retrieved
            chunks, citations, reranker output).  Subtract from context_budget
            before comparing against doc size to avoid over-promising.
        safety_margin: Fraction of context_budget to keep free for generation
            and other messages (default 0.15 = 15%).
    """

    def __init__(
        self,
        rag_overhead_tokens: int = 500,
        safety_margin: float = 0.15,
    ) -> None:
        self._rag_overhead = rag_overhead_tokens
        self._safety_margin = safety_margin

    def decide(
        self,
        doc_token_estimate: int,
        context_budget: int,
    ) -> RetrievalStrategy:
        """Return the retrieval strategy for a document of *doc_token_estimate* tokens.

        Args:
            doc_token_estimate: Estimated token count of the full document.
            context_budget: Remaining context window tokens available for
                retrieval content (after system prompt, history, tools, etc.).
        """
        usable_budget = int(context_budget * (1.0 - self._safety_margin))
        if doc_token_estimate <= usable_budget:
            return RetrievalStrategy.FULL_CONTEXT
        return RetrievalStrategy.RAG

    def decide_batch(
        self,
        doc_token_estimates: list[int],
        context_budget: int,
    ) -> RetrievalStrategy:
        """Return strategy for a collection of documents (uses total token sum)."""
        return self.decide(sum(doc_token_estimates), context_budget)
