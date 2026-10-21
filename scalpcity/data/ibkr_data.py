"""Interactive Brokers market data for the futures city: history, live prices and quotes of the front month.

- minute_bars(root, day): regular-hours 1-minute bars of the contract that was the front month that day (expired
  months included), fetched a week at a time and cached as CSV in data.csv_dir/futures/ so restarts are quick.
- live prices: a market-data subscription per front-month contract; every new last price becomes a Tick.
- quote(contract): bid/ask of a held contract.
- ib_daily / ib_premarket: daily candles of the continuous contract, and 04:00-09:30 ET highs and lows.
IB allows about 60 history requests per 10 minutes; the week-at-a-time fetch keeps a 60-session warm-up near 40.
Real-time CME data needs a market-data subscription on the IBKR account (docs/futures-city.md).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Awaitable, Callable, Optional

from ..brokers.ibkr_conn import EXCHANGES, connect, ib_contract
from ..core import calendar as cal
from ..core.events import Candle, OptionQuote, Side
from ..core.futures import front_month
from .bars import read_csv, write_csv

log = logging.getLogger("scalpcity.ibkr_data")


def _et(ts) -> datetime:
    if isinstance(ts, datetime):
        return ts.astimezone(cal.ET) if ts.tzinfo else ts.replace(tzinfo=cal.ET)
    return datetime.combine(ts, time(0), cal.ET)


def _candles(root: str, bars) -> list[Candle]:
    return [Candle(root, _et(b.date), float(b.open), float(b.high), float(b.low), float(b.close), float(b.volume or 0))
            for b in bars]


class IBDataClient:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.dir = Path(cfg.data.csv_dir) / "futures"
        self.tickers: dict[str, object] = {}
        self.qualified: dict[str, object] = {}

    async def _contract(self, c, expired: bool = False):
        if c.occ not in self.qualified:
            ib = await connect(self.cfg)
            got = await ib.qualifyContractsAsync(ib_contract(c, expired=expired))
            if not got or got[0] is None:
                raise RuntimeError(f"Interactive Brokers doesn't know {c.occ}")
            self.qualified[c.occ] = got[0]
        return self.qualified[c.occ]

    async def minute_bars(self, root: str, day: date) -> list[Candle]:
        path = self.dir / root / f"{day}.csv"
        if path.exists():
            return read_csv(path, root)
        today = cal.now_et().date()
        c = front_month(self.cfg, root, day, Side.CALL)
        ib = await connect(self.cfg)
        ibc = await self._contract(c, expired=day < today)
        end = min(cal.session_close(day) + timedelta(days=4), cal.now_et())   # this day and up to 4 after it
        bars = await ib.reqHistoricalDataAsync(ibc, endDateTime=end, durationStr="1 W", barSizeSetting="1 min",
                                               whatToShow="TRADES", useRTH=True)
        await asyncio.sleep(0.5)                     # stay inside IB's history pacing
        by_day: dict[date, list[Candle]] = {}
        for b in _candles(root, bars):
            by_day.setdefault(b.start.date(), []).append(b)
        for d, rows in by_day.items():
            if d < today and front_month(self.cfg, root, d, Side.CALL).occ == c.occ:
                p = self.dir / root / f"{d}.csv"
                p.parent.mkdir(parents=True, exist_ok=True)
                write_csv(p, rows)
        return [b for b in by_day.get(day, []) if cal.session_open(day) <= b.start < cal.session_close(day)]

    async def quote(self, contract) -> Optional[OptionQuote]:
        ib = await connect(self.cfg)
        if contract.occ not in self.tickers:
            self.tickers[contract.occ] = ib.reqMktData(await self._contract(contract))
            await asyncio.sleep(1.0)
        t = self.tickers[contract.occ]
        bid, ask, last = (float(x) if x == x and x is not None else 0.0 for x in (t.bid, t.ask, t.last))
        if bid <= 0 or ask <= 0:
            return None
        return OptionQuote(cal.now_et(), contract, bid, ask, float(contract.way), None, last or (bid + ask) / 2)

    async def close(self) -> None:
        return None


class IBStream:
    """Live last prices of each root's front month -> on_trade(root, ts, price, size)."""

    def __init__(self, cfg, on_trade: Callable[..., Awaitable[None]],
                 on_status: Optional[Callable[[str, str], Awaitable[None]]] = None) -> None:
        self.cfg, self.on_trade, self.on_status = cfg, on_trade, on_status
        self.last: dict[str, float] = {}

    async def run(self) -> None:
        ib = await connect(self.cfg)
        client = IBDataClient(self.cfg)
        roots: dict[int, str] = {}
        for root in self.cfg.symbols:
            c = front_month(self.cfg, root, cal.now_et().date(), Side.CALL)
            t = ib.reqMktData(await client._contract(c))
            roots[id(t)] = root
        queue: asyncio.Queue = asyncio.Queue()

        def on_pending(tickers):
            for t in tickers:
                root = roots.get(id(t))
                price = t.last
                if root and price == price and price and price > 0 and self.last.get(root) != price:
                    self.last[root] = price
                    queue.put_nowait((root, _et(t.time or cal.now_et()), float(price), float(t.lastSize or 0)))
        ib.pendingTickersEvent += on_pending
        if self.on_status:
            await self.on_status("info", f"Interactive Brokers stream connected ({', '.join(self.cfg.symbols)})")
        while True:
            root, ts, price, size = await queue.get()
            await self.on_trade(root, ts, price, size)


async def ib_daily(cfg, start: date, end: date) -> dict[str, list[Candle]]:
    """Daily candles of each root's continuous contract (regular hours), for the daily bias and levels."""
    from ib_async import ContFuture
    out: dict[str, list[Candle]] = {}
    try:
        ib = await connect(cfg)
        for root in cfg.symbols:
            cf = (await ib.qualifyContractsAsync(ContFuture(root, EXCHANGES.get(root, "CME"), currency="USD")))[0]
            years = max(1, (end - start).days // 365 + 1)
            bars = await ib.reqHistoricalDataAsync(cf, endDateTime="", durationStr=f"{years} Y", barSizeSetting="1 day",
                                                   whatToShow="TRADES", useRTH=True)
            out[root] = [b for b in _candles(root, bars) if start <= b.start.date() <= end]
    except Exception as exc:  # noqa: BLE001 - the study degrades gracefully without daily data
        log.warning("daily candles from Interactive Brokers unavailable (%s); higher-timeframe study skipped", exc)
    return out


async def ib_premarket(cfg, start: date, end: date) -> dict[str, dict[str, list[float]]]:
    """Highs and lows from 04:00 to 09:30 ET per day (the futures trade overnight), the last 20 sessions at most."""
    out: dict[str, dict[str, list[float]]] = {}
    days = cal.trading_days(max(start, end - timedelta(days=30)), end)
    if not days:
        return out
    try:
        ib = await connect(cfg)
        client = IBDataClient(cfg)
        for root in cfg.symbols:
            got: dict[str, list[float]] = {}
            for week_end in sorted({min(d + timedelta(days=(4 - d.weekday()) % 7), end) for d in days}):
                c = front_month(cfg, root, week_end, Side.CALL)
                ibc = await client._contract(c, expired=week_end < cal.now_et().date())
                stop = min(datetime.combine(week_end, time(9, 30), cal.ET), cal.now_et())
                bars = await ib.reqHistoricalDataAsync(ibc, endDateTime=stop, durationStr="1 W",
                                                       barSizeSetting="30 mins", whatToShow="TRADES", useRTH=False)
                await asyncio.sleep(0.5)
                for b in _candles(root, bars):
                    d = b.start.date()
                    if time(4, 0) <= b.start.time() < time(9, 30) and start <= d <= end:
                        hi_lo = got.setdefault(d.isoformat(), [b.high, b.low])
                        hi_lo[0], hi_lo[1] = max(hi_lo[0], b.high), min(hi_lo[1], b.low)
            out[root] = got
    except Exception as exc:  # noqa: BLE001 - the NTZ trigger stands down without pre-market data
        log.warning("pre-market from Interactive Brokers unavailable (%s)", exc)
    return out
