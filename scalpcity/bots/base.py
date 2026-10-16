from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from ..core.bus import EventBus
from ..core.config import Config
from ..core.events import Event
from ..core.storage import Storage

if TYPE_CHECKING:
    from ..brokers.base import Broker


@dataclass
class Context:
    """Shared wiring handed to every bot. Bots act through events; `bots` is only
    used for read-only queries (e.g. the contract selector asking for a chain)."""
    cfg: Config
    bus: EventBus
    storage: Storage
    broker: "Broker"
    live: bool                     # True: wall-clock driven (paper/live); False: replay/backtest
    bots: dict[str, Any] = field(default_factory=dict)


class Bot:
    name = "bot"
    skill = ""

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.cfg = ctx.cfg
        self.bus = ctx.bus
        self.log = logging.getLogger(f"scalpcity.{self.name}")
        self._tasks: list[asyncio.Task] = []
        ctx.bots[self.name] = self
        self.setup()

    def setup(self) -> None:
        """Subscribe to events here."""

    def on(self, event_type: type, handler) -> None:
        self.bus.subscribe(event_type, handler, self.name)

    def emit(self, event: Event) -> None:
        self.bus.publish(event)

    async def start(self) -> None:
        """Start background tasks (live mode timers, sockets, servers)."""

    def spawn(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro, name=self.name)
        self._tasks.append(task)
        return task

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

    def bot(self, name: str) -> Optional[Any]:
        return self.ctx.bots.get(name)
