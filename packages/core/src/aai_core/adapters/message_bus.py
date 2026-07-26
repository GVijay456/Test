"""Message bus adapter ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Awaitable


@dataclass
class Message:
    subject: str                        # e.g. "runs.events.tenant_abc"
    data: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)
    sequence: int | None = None         # filled by broker on publish
    reply_to: str | None = None


Handler = Callable[[Message], Awaitable[None]]


class MessageBus(ABC):
    """Plug-and-play message bus interface.

    Implementations: NATSJetStreamBus (default), KafkaBus, SQSBus.
    """

    @property
    @abstractmethod
    def bus_id(self) -> str:
        """Unique string like 'nats', 'kafka', 'sqs'."""

    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish a message. At-least-once delivery."""

    @abstractmethod
    async def subscribe(
        self,
        subject: str,
        queue_group: str,
        handler: Handler,
    ) -> None:
        """Subscribe to a subject with a competing consumer queue group."""

    @abstractmethod
    async def stream(
        self,
        subject: str,
        start_sequence: int | None = None,
    ) -> AsyncIterator[Message]:
        """Consume messages from a durable stream (for SSE fan-out)."""

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if bus is reachable."""
