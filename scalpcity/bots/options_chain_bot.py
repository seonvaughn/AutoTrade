"""Options Chain Bot — knows option prices.

Answers "what does the chain look like?" for the contract selector, and streams
quotes for every contract we hold so the exit manager and ledger can react.

Sim (replay/backtest): Black-Scholes on trading-time from the replayed underlying
(or real option bars when sim.use_historical_option_bars is on), with a modeled
bid/ask spread and expiry calendar. Crypto: the replayed price ± a modeled spread.
Live/paper: Alpaca or Polygon option snapshots (data.live_data), Alpaca crypto quotes.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional

from ..core import calendar as cal
from ..core.events import CryptoAsset, OptionContract, OptionQuote, PositionOpened, Side, Tick, TradeClosed
from ..core.options_math import bs_delta, bs_price, round_tick
from .base import Bot


class SimChain:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.spot: dict[str, float] = {}
        self.spot_by_minute: dict[str, dict[datetime, float]] = {}  # last price seen in each minute
        self.hist = None
        if cfg.sim.use_historical_option_bars and not cal.is_crypto() and cfg.data.source != "synthetic":
            from ..data.option_bars import HistoricalOptionBars
            self.hist = HistoricalOptionBars(cfg.data.option_bars_dir, cfg.data.source)

    def listed(self, underlying: str, expiry: date) -> bool:
        """Modeled expiry calendar from sim.expiry_weekdays (Fridays for unlisted symbols)."""
        if not cal.is_trading_day(expiry):
            return False
        days = self.cfg.sim.expiry_weekdays.get(underlying, [4])
        if expiry.weekday() in days:
            return True
        nxt = expiry + timedelta(days=1)  # a holiday on a listed weekday moves the expiry one day earlier
        return nxt.weekday() < 5 and not cal.is_trading_day(nxt) and nxt.weekday() in days

    def quote(self, c, ts: datetime) -> Optional[OptionQuote]:
        spot = self.spot.get(c.underlying)
        if spot is None:
            return None
        if c.kind == "crypto":
            half = spot * self.cfg.sim.crypto_half_spread_pct / 100.0
            return OptionQuote(ts, c, spot - half, spot + half, None, None, spot)
        minutes = cal.minutes_to_expiry(ts, c.expiry)
        iv = self.cfg.sim.iv.get(c.underlying, 0.2)
        is_call = c.right is Side.CALL
        mid = None
        if self.hist:
            mid = self._from_last_trade(c, ts, spot, minutes, iv, is_call)
        if mid is None:
            mid = bs_price(spot, c.strike, minutes, iv, is_call) if minutes > 0 else \
                max(0.0, spot - c.strike if is_call else c.strike - spot)
        half = max(self.cfg.sim.min_half_spread, mid * self.cfg.sim.half_spread_pct / 100.0)
        bid = max(0.0, round_tick(mid - half)) if mid - half >= 0.01 else 0.0
        ask = round_tick(mid + half)
        delta = bs_delta(spot, c.strike, max(minutes, 1), iv, is_call)
        return OptionQuote(ts, c, bid, ask, delta, iv, spot)

    def on_spot(self, symbol: str, ts: datetime, price: float) -> None:
        self.spot[symbol] = price
        per = self.spot_by_minute.setdefault(symbol, {})
        per[ts.replace(second=0, microsecond=0)] = price
        if len(per) > 600:
            for k in sorted(per)[:200]:
                del per[k]

    def _from_last_trade(self, c, ts, spot, minutes, iv, is_call) -> Optional[float]:
        """Real option price from its last trade, moved by delta for what the stock did since.

        Using a stale last trade as-is lets a backtest buy at a price from before the move that
        fired the signal; that once turned a losing strategy into a fake +$41k. So the last trade
        is only an anchor: price = last trade + delta * (stock now - stock when it traded)."""
        bar = self.hist.last_bar(c, ts)
        if bar is None:
            return None
        then = self.spot_by_minute.get(c.underlying, {}).get(bar.start)
        if then is None:
            return None  # can't tell how stale it is: use the model price instead
        delta = bs_delta(spot, c.strike, max(minutes, 1), iv, is_call)
        return max(0.01, bar.close + delta * (spot - then))

    def chain(self, underlying: str, expiry: date, right: Side, ts: datetime) -> list[OptionQuote]:
        spot = self.spot.get(underlying)
        if spot is None or not self.listed(underlying, expiry):
            return []
        step = self.cfg.sim.strike_step.get(underlying, 1.0)
        atm = round(spot / step) * step
        quotes = []
        for i in range(-10, 11):
            q = self.quote(OptionContract(underlying, expiry, round(atm + i * step, 2), right), ts)
            if q:
                quotes.append(q)
        return quotes


class OptionsChainBot(Bot):
    name = "options_chain"
    skill = "Option chain + live quotes for held contracts"

    def setup(self) -> None:
        self.sim = None if self.ctx.live else SimChain(self.cfg)
        self.poly = None
        self.watched: dict[str, OptionContract] = {}
        self.holders: dict[str, set[str]] = {}  # occ -> workers holding it (several workers can share a contract)
        self.last_ts: Optional[datetime] = None
        self.on(Tick, self.on_tick)
        self.on(PositionOpened, self.on_opened)
        self.on(TradeClosed, self.on_closed)

    def on_opened(self, e: PositionOpened) -> None:
        self.watched[e.contract.occ] = e.contract
        self.holders.setdefault(e.contract.occ, set()).add(e.worker)

    def on_closed(self, e: TradeClosed) -> None:
        holders = self.holders.get(e.contract.occ, set())
        holders.discard(e.worker)
        if not holders:
            self.holders.pop(e.contract.occ, None)
            self.watched.pop(e.contract.occ, None)

    def on_tick(self, t: Tick) -> None:
        self.last_ts = t.ts
        if not self.sim:
            return
        self.sim.on_spot(t.symbol, t.ts, t.price)
        for c in self.watched.values():
            if c.underlying == t.symbol:
                q = self.sim.quote(c, t.ts)
                if q:
                    self.emit(q)

    async def get_chain(self, underlying: str, expiry: date, right: Side, spot: float) -> list[OptionQuote]:
        if self.sim:
            return self.sim.chain(underlying, expiry, right, self.last_ts)
        return await self._poly().chain(underlying, expiry, right, spot)

    async def quote(self, contract) -> Optional[OptionQuote]:
        if self.sim:
            return self.sim.quote(contract, self.last_ts)
        return await self._poly().quote(contract)

    async def crypto_quote(self, symbol: str) -> Optional[OptionQuote]:
        return await self.quote(CryptoAsset(symbol))

    def quote_now(self, contract) -> Optional[OptionQuote]:
        """Synchronous quote for the simulated broker."""
        return self.sim.quote(contract, self.last_ts) if self.sim else None

    def _poly(self):
        if self.poly is None:
            from ..data.live import live_client
            self.poly = live_client(self.cfg)
        return self.poly

    async def start(self) -> None:
        if self.ctx.live:
            self.spawn(self._poll())

    async def _poll(self) -> None:
        while True:
            await asyncio.sleep(self.cfg.data.quote_poll_seconds)
            if not self.watched:
                continue
            contracts = list(self.watched.values())
            results = await asyncio.gather(*(self._poly().quote(c) for c in contracts), return_exceptions=True)
            for r in results:
                if isinstance(r, OptionQuote):
                    self.bus.publish(r)
                elif isinstance(r, Exception):
                    self.log.warning("quote poll failed: %s", r)
            await self.bus.drain()

    async def stop(self) -> None:
        await super().stop()
        if self.poly:
            await self.poly.close()
