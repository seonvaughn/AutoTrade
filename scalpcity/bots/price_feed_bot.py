"""Price Feed Bot — the only bot that brings market prices into the system.

Replay: walks recorded/synthetic 1-minute bars, emitting open -> high/low -> close
ticks inside every minute plus heartbeats, so the rest of the bots see exactly
what they would see live. Live: Alpaca real-time trades or Polygon per-second aggregates.
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

from ..core import calendar as cal
from ..core.events import Alert, Candle, CandleClosed, Heartbeat, Tick
from ..data.bars import BarLoader
from .base import Bot


class PriceFeedBot(Bot):
    name = "price_feed"
    skill = "Stream underlying prices (replayed or live) into the bus"

    def setup(self) -> None:
        self.loader = BarLoader(self.cfg.data.source, self.cfg.data.csv_dir)
        self.days: list[date] = []
        self.pace = 0.0  # seconds of wall time per market minute (0 = as fast as possible)
        self.progress = None  # optional callback(day, minute_index, total)
        self.stopped = False

    # ------------------------------------------------------------- replay
    async def replay(self, days: list[date], pace: float = 0.0) -> None:
        symbols = self.cfg.symbols
        if not days:
            return
        warm = sorted((b for d in self.warm_days(days[0]) for s in symbols for b in self.loader.load(s, d)),
                      key=lambda b: b.start)
        await self._history(warm)

        for d in days:
            bars = {s: {b.start: b for b in self.loader.load(s, d)} for s in symbols}
            if not any(bars.values()):
                await self.bus.emit(Alert(cal.session_open(d), "warning", f"no data for {d}, skipped"))
                continue
            minutes = sorted({m for per in bars.values() for m in per})
            await self.bus.emit(Heartbeat(cal.session_open(d) - timedelta(seconds=1)))
            for i, m in enumerate(minutes):
                if self.stopped:
                    return
                await self._replay_minute(m, [per[m] for per in bars.values() if m in per])
                if self.progress:
                    self.progress(d, i, len(minutes))
                if pace > 0:
                    await asyncio.sleep(pace)
            await self.bus.emit(Heartbeat(cal.session_close(d)))

    async def _history(self, bars) -> None:
        """Deliver past candles one at a time, each followed by everything it triggers, so time-ordered
        consumers (the edge tracker scoring past signals) see history in the order it happened."""
        for b in bars:
            self.emit(CandleClosed(b.start + timedelta(minutes=1), b, backfill=True))
            await self.bus.drain()

    def warm_days(self, first: date) -> list[date]:
        """Past sessions replayed (as history) before trading: the research bots study these."""
        out, d = [], first
        for _ in range(max(1, self.cfg.research.lookback_days, self.cfg.research.edge_lookback_days)):
            d = cal.prev_trading_day(d)
            out.append(d)
        return sorted(out)

    STEPS = 12  # one tick every 5 seconds

    @staticmethod
    def path(c: Candle, steps: int) -> list[float]:
        """A continuous price path through the bar: open -> low -> high -> close for
        up bars (open -> high -> low -> close for down bars), walked in equal steps
        so stops and targets trigger near their levels instead of jumping past them."""
        a, b = (c.low, c.high) if c.close >= c.open else (c.high, c.low)
        l1, l2, l3 = abs(a - c.open), abs(b - a), abs(c.close - b)
        total = (l1 + l2 + l3) or 1.0
        # anchor indexes for the two extremes, spaced by distance, always distinct and inside the path
        ia = min(max(1, round((steps - 1) * l1 / total)), steps - 3)
        ib = min(max(ia + 1, round((steps - 1) * (l1 + l2) / total)), steps - 2)
        anchors = [(0, c.open), (ia, a), (ib, b), (steps - 1, c.close)]
        out = []
        for (i0, p0), (i1, p1) in zip(anchors, anchors[1:]):
            for i in range(i0, i1):
                out.append(p0 + (p1 - p0) * (i - i0) / (i1 - i0))
        out.append(c.close)
        return [round(p, 4) for p in out]

    async def _replay_minute(self, m, candles: list[Candle]) -> None:
        paths = {c.symbol: self.path(c, self.STEPS) for c in candles}
        for k in range(self.STEPS):
            ts = m + timedelta(seconds=min(59, 1 + 5 * k))
            for c in candles:
                self.emit(Tick(ts, c.symbol, paths[c.symbol][k], c.volume / self.STEPS))
            self.emit(Heartbeat(ts))
            await self.bus.drain()
        await self.bus.emit(Heartbeat(m + timedelta(minutes=1)))

    # ------------------------------------------------------------- live
    async def start(self) -> None:
        if not self.ctx.live:
            return
        from ..data.live import live_client

        await self._backfill(live_client(self.cfg))
        d = self.cfg.data
        if d.live_data == "alpaca":
            from ..data.alpaca_data import AlpacaStream
            stream = AlpacaStream(self.cfg.symbols, self._on_trade, d.alpaca_stock_feed, self._on_status)
        else:
            from ..data.polygon import PolygonStream
            stream = PolygonStream(self.cfg.symbols, self._on_agg, d.polygon_feed, self._on_status)
        self.spawn(stream.run())

    async def _backfill(self, client) -> None:
        """Past sessions + today-so-far: indicators are right on a mid-day start, and the research bots
        have history to study before the first trade."""
        today = cal.now_et().date()
        days = self.warm_days(today) + ([today] if cal.is_trading_day(today) else [])
        cutoff = cal.now_et().replace(second=0, microsecond=0)
        try:
            bars = []
            for d in days:
                for s in self.cfg.symbols:
                    bars += [b for b in await client.minute_bars(s, d) if b.start + timedelta(minutes=1) <= cutoff]
            await self._history(sorted(bars, key=lambda b: b.start))
            self.log.info("backfilled %d bars", len(bars))
        finally:
            await client.close()

    async def _on_agg(self, sym, ts, o, h, low, c, v) -> None:
        self.emit(Tick(ts, sym, h, 0.0))
        self.emit(Tick(ts, sym, low, 0.0))
        await self.bus.emit(Tick(ts, sym, c, v))

    async def _on_trade(self, sym, ts, price, size) -> None:
        await self.bus.emit(Tick(ts, sym, price, size))

    async def _on_status(self, level: str, text: str) -> None:
        await self.bus.emit(Alert(cal.now_et(), level, text))
