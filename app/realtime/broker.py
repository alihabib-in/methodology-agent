"""In-process pub/sub broker for real-time events.

Keeps one asyncio queue per connected WebSocket and fans events out by
``session_id``. Publishing is thread-safe so synchronous (threadpool) API
endpoints can broadcast without blocking.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from app.core.logging import get_logger
from app.realtime.events import EventEnvelope, build_envelope

logger = get_logger(__name__)


class Subscription:
    def __init__(self, session_id: str, queue: asyncio.Queue) -> None:
        self.session_id = session_id
        self.queue = queue


class EventBroker:
    def __init__(self) -> None:
        self._subs: dict[str, list[Subscription]] = {}
        self._lock = threading.Lock()
        self._sequences: dict[str, int] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, session_id: str) -> Subscription:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        sub = Subscription(session_id, queue)
        self._loop = asyncio.get_running_loop()
        with self._lock:
            self._subs.setdefault(session_id, []).append(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        with self._lock:
            subs = self._subs.get(sub.session_id)
            if subs and sub in subs:
                subs.remove(sub)
            if subs is not None and not subs:
                self._subs.pop(sub.session_id, None)

    def publish(
        self,
        event_type: str,
        session_id: str | None = None,
        meeting_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if not session_id:
            return
        with self._lock:
            seq = self._sequences.get(session_id, 0) + 1
            self._sequences[session_id] = seq
            subs = list(self._subs.get(session_id, []))

        if not subs:
            return

        envelope = build_envelope(
            event_type,
            session_id=session_id,
            meeting_id=meeting_id,
            payload=payload or {},
            sequence=seq,
        )
        data = envelope.model_dump()
        for sub in subs:
            self._put(sub, data)

    def _put(self, sub: Subscription, data: dict[str, Any]) -> None:
        loop = self._loop or asyncio.get_event_loop()
        try:
            loop.call_soon_threadsafe(self._safe_put, sub, data)
        except RuntimeError:
            pass

    def _safe_put(self, sub: Subscription, data: dict[str, Any]) -> None:
        try:
            sub.queue.put_nowait(data)
        except asyncio.QueueFull:
            logger.warning(
                "realtime queue full for session %s; dropping event", sub.session_id
            )
