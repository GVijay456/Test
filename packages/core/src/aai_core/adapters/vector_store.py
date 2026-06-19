"""Vector store adapter ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class SearchResult:
    document: Document
    score: float                # cosine similarity 0-1


class VectorStore(ABC):
    """Plug-and-play vector store interface.

    Implementations: QdrantStore (default), PgVectorStore, PineconeStore.
    """

    @property
    @abstractmethod
    def store_id(self) -> str:
        """Unique string like 'qdrant', 'pgvector', 'pinecone'."""

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        documents: list[Document],
        tenant_id: str,
    ) -> None:
        """Upsert documents into a tenant-scoped collection."""

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        tenant_id: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return top_k results for the query embedding."""

    @abstractmethod
    async def delete(
        self,
        collection: str,
        document_ids: list[str],
        tenant_id: str,
    ) -> None:
        """Delete documents by ID."""

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if store is reachable."""
