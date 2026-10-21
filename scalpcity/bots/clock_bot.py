"""Clock Bot — knows the market session and announces every transition."""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

from ..core import calendar as cal
from ..core.events import Heartbeat, SessionEvent, SessionKind
from .base import Bot


class ClockBot(Bot):
    name = "clock"
    skill = "Session state: new day, open, entry cutoff, flatten, close (holidays and half days aware)"

    def setup(self) -> None:
        self.day: date | None = None
        self.done: set[SessionKind] = set()
        self.now = None
        self.on(Heartbeat, self.on_heartbeat)

    def times(self, d: date) -> dict[SessionKind, object]:
        close = cal.session_close(d)
        shift = cal.close_shift(d)  # negative on half days
        return {
            SessionKind.OPEN: cal.session_open(d),
            SessionKind.ENTRY_CUTOFF: min(cal.at(d, self.cfg.entry_cutoff) + shift, close - timedelta(minutes=30)),
            SessionKind.FLATTEN: min(cal.at(d, self.cfg.flatten_time) + shift, close - timedelta(minutes=5)),
            SessionKind.CLOSED: close,
        }

    def on_heartbeat(self, hb: Heartbeat) -> None:
        self.now = hb.ts
        d = hb.ts.date()
        if not cal.is_trading_day(d):
            return
        if d != self.day:
            if self.day is not None:
                # events the last session didn't reach (e.g. no heartbeat after the close) fire now
                for kind, when in self.times(self.day).items():
                    if kind not in self.done and hb.ts >= when:
                        self.done.add(kind)
                        self.emit(SessionEvent(hb.ts, kind, self.day))
            self.day, self.done = d, set()
            self.emit(SessionEvent(hb.ts, SessionKind.NEW_DAY, d))
        for kind, when in self.times(d).items():
            if kind not in self.done and hb.ts >= when:
                self.done.add(kind)
                self.emit(SessionEvent(hb.ts, kind, d))

    def is_open(self) -> bool:
        return SessionKind.OPEN in self.done and SessionKind.CLOSED not in self.done

    def entries_allowed(self) -> bool:
        return self.is_open() and SessionKind.ENTRY_CUTOFF not in self.done

    async def start(self) -> None:
        if self.ctx.live:
            self.spawn(self._tick())

    async def _tick(self) -> None:
        while True:
            await self.bus.emit(Heartbeat(cal.now_et()))
            await asyncio.sleep(1.0)
