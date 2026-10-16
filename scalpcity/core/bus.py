"""Deterministic async event bus.

`publish` only enqueues. `drain` delivers events FIFO, and each event goes to its
subscribers in the order they subscribed. Events published while draining go to
the back of the queue. This makes a replayed day produce exactly the same
sequence of decisions every run, and it is the same code path used live.

Handler exceptions are caught and turned into BotError events, so a single
faulty bot can't take the whole system down.
"""
from __future__ import annotations

import inspect
import logging
from collections import defaultdict, deque
from typing import Any, Callable

from .events import BotError, Event

log = logging.getLogger("scalpcity.bus")

Handler = Callable[[Any], Any]


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[type, list[tuple[str, Handler]]] = defaultdict(list)
        self._queue: deque[Event] = deque()
        self._draining = False
        self.delivered = 0
        self.published: dict[str, int] = defaultdict(int)  # event type -> count (for the dashboard crew view)
        self.activity: dict[str, list] = {}  # owner -> [events handled, last event type, last event ts]

    def subscribe(self, event_type: type, handler: Handler, owner: str = "?") -> None:
        self._subs[event_type].append((owner, handler))

    def unsubscribe(self, owner: str) -> None:
        """Detach every handler of one bot (used to isolate bots in tests or to disable one)."""
        for ty in self._subs:
            self._subs[ty] = [(o, h) for o, h in self._subs[ty] if o != owner]

    def publish(self, event: Event) -> None:
        self.published[type(event).__name__] += 1
        self._queue.append(event)

    async def emit(self, event: Event) -> None:
        """Publish and deliver (used by sources: feeds, timers, the web UI)."""
        self.publish(event)
        await self.drain()

    async def drain(self) -> None:
        if self._draining:
            return  # the active drain loop will pick the event up
        self._draining = True
        try:
            while self._queue:
                event = self._queue.popleft()
                for owner, handler in list(self._subs.get(type(event), ())):
                    a = self.activity.get(owner)
                    if a is None:
                        a = self.activity[owner] = [0, "", None]
                    a[0] += 1
                    a[1] = type(event).__name__
                    a[2] = event.ts
                    try:
                        result = handler(event)
                        if inspect.isawaitable(result):
                            await result
                    except Exception as exc:  # noqa: BLE001 - isolate faulty bots
                        log.exception("bot %s failed on %s", owner, type(event).__name__)
                        if not isinstance(event, BotError):
                            self._queue.append(BotError(event.ts, owner, f"{type(exc).__name__}: {exc}"))
                self.delivered += 1
        finally:
            self._draining = False
