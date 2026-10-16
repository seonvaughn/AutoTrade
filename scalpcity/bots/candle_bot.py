"""Candle Bot — turns the tick stream into clean 1-minute candles (regular hours only)."""
from __future__ import annotations

from datetime import timedelta

from ..core import calendar as cal
from ..core.events import Candle, CandleClosed, Heartbeat, Tick
from .base import Bot


class CandleBot(Bot):
    name = "candles"
    skill = "Build 1-minute OHLCV candles and announce each close"

    def setup(self) -> None:
        self.bars: dict[str, Candle] = {}
        self.grace = timedelta(seconds=1.5 if self.ctx.live else 0)
        self.on(Tick, self.on_tick)
        self.on(Heartbeat, self.on_heartbeat)

    def on_tick(self, t: Tick) -> None:
        d = t.ts.date()
        if not (cal.session_open(d) <= t.ts < cal.session_close(d)):
            return
        minute = t.ts.replace(second=0, microsecond=0)
        bar = self.bars.get(t.symbol)
        if bar and minute > bar.start:
            self._close(t.symbol, t.ts)
            bar = None
        if bar and minute < bar.start:
            return  # late tick for an already-closed minute
        if bar is None:
            self.bars[t.symbol] = Candle(t.symbol, minute, t.price, t.price, t.price, t.price, t.size)
        else:
            bar.high = max(bar.high, t.price)
            bar.low = min(bar.low, t.price)
            bar.close = t.price
            bar.volume += t.size

    def on_heartbeat(self, hb: Heartbeat) -> None:
        for sym, bar in list(self.bars.items()):
            if hb.ts >= bar.start + timedelta(minutes=1) + self.grace:
                self._close(sym, hb.ts)

    def _close(self, sym: str, ts) -> None:
        bar = self.bars.pop(sym)
        self.emit(CandleClosed(ts, bar))
