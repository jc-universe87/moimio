"""In-process pub/sub for real-time event streams.

v1.0-pre #8/#9: small fan-out broker for Server-Sent Events. Used to
notify all clients viewing a given event surface (Check-in, Organise)
when state changes. No external dependencies — pure asyncio.

v0.84 #32: structured logging added to publish + subscribe so admins
can grep `docker compose logs backend` for `pubsub_publish` and
`pubsub_subscribe` to verify the pipeline end-to-end. Useful for
diagnosing "real-time sync isn't working" reports — if publish logs
show `delivered=0`, no clients are subscribed (frontend issue); if
publish shows `delivered>=1` but the second device doesn't update,
the issue is downstream (Caddy buffering, EventSource error, etc.).

Design constraints
──────────────────
- One backend container is the v1.0 deployment topology. Inter-process
  pub/sub (Redis, NATS, etc.) is post-1.0; the same Broker interface
  can be backed by Redis later without changing the call sites.
- Publishers fire-and-forget. A blocked subscriber (slow client, dropped
  TCP connection) must not stall the publisher. We use a bounded queue
  per subscriber and drop the oldest message on overflow rather than
  applying back-pressure.
- A topic is a string, conventionally `<surface>:<event_id>`, e.g.
  "checkin:550e8400-e29b-41d4-a716-446655440000".

Usage
─────
    from app.core.pubsub import broker

    # Publisher
    await broker.publish(f"checkin:{event_id}", {"participant_id": ..., ...})

    # Subscriber (typically inside an SSE endpoint)
    async with broker.subscribe(f"checkin:{event_id}") as queue:
        while True:
            msg = await queue.get()
            yield format_sse(msg)
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class Broker:
    """Per-process topic-based message broker.

    Internally: dict[topic -> set[queue]]. Each subscribe() adds a
    bounded queue; publish() pushes the message into every queue on
    that topic, dropping the oldest item if a queue is full.
    """

    # Per-subscriber queue size. Keeps memory bounded if a client stalls
    # while events keep arriving. 256 is comfortable for normal load
    # (a 200-person event ticked one-per-second is < 4 minutes of buffer).
    _QUEUE_SIZE = 256

    def __init__(self) -> None:
        self._topics: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, message: Any) -> int:
        """Send `message` to every subscriber on `topic`. Returns the
        number of subscribers reached. Never blocks the publisher: a
        full queue drops its oldest entry to make room.
        """
        async with self._lock:
            queues = list(self._topics.get(topic, ()))
        delivered = 0
        for q in queues:
            try:
                q.put_nowait(message)
                delivered += 1
            except asyncio.QueueFull:
                # Drop the oldest item, retry once. If even that fails
                # (shouldn't), give up on this subscriber — they'll see
                # a stale view until the next message arrives.
                try:
                    q.get_nowait()
                    q.put_nowait(message)
                    delivered += 1
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass
        # v0.84 #32: log delivery count for diagnostics. INFO level so it
        # shows in normal `docker compose logs backend` output.
        kind = (message.get("kind") or message.get("type")) if isinstance(message, dict) else None
        logger.info("pubsub_publish", topic=topic, kind=kind, subscribers=len(queues), delivered=delivered)
        return delivered

    @asynccontextmanager
    async def subscribe(self, topic: str):
        """Async context manager yielding an asyncio.Queue. The queue
        receives every message published to `topic` while the context
        is open; on exit, the subscription is cleaned up.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._QUEUE_SIZE)
        async with self._lock:
            self._topics.setdefault(topic, set()).add(queue)
            sub_count = len(self._topics[topic])
        # v0.84 #32: log subscription lifecycle for diagnostics.
        logger.info("pubsub_subscribe", topic=topic, total_subscribers=sub_count)
        try:
            yield queue
        finally:
            async with self._lock:
                subs = self._topics.get(topic)
                if subs is not None:
                    subs.discard(queue)
                    remaining = len(subs)
                    if not subs:
                        # Last subscriber gone — free the topic entry.
                        self._topics.pop(topic, None)
                else:
                    remaining = 0
            logger.info("pubsub_unsubscribe", topic=topic, remaining_subscribers=remaining)


# Module-level singleton. Import from anywhere in the app:
#   from app.core.pubsub import broker
broker = Broker()
