"""Signal bots — one per trigger from the video:

  1. "A candle closes across the VWAP"            -> VWAPCrossBot
  2. "A candle closes across the 50 EMA"          -> EMACrossBot
  3. "Price breaks out of the first 15 minutes"   -> ORBBot

"Closing above it means it's going to buy a call, and closing below means it
buys a put."  Each bot also publishes a live "charge %" (how close price is to
its trigger, in ATR units) which drives the green/red beams on the dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..core.events import IndicatorValue, SetupUpdate, Side, Signal, Tick
from .base import Bot

CHARGE_WINDOW_ATR = 1.0  # price this many ATRs away = 0% charged; on the level = 100%


@dataclass
class _Prev:
    day: date
    close: float
    level: float


class _SignalBot(Bot):
    trigger = ""

    def setup(self) -> None:
        self.atr: dict[str, float] = {}
        self.vwap: dict[str, float] = {}
        self.ema: dict[str, float] = {}
        self.last_charge: dict[str, tuple[Side, int]] = {}
        self.on(IndicatorValue, self.on_indicator)
        self.on(Tick, self.on_tick)

    def on_indicator(self, ev: IndicatorValue) -> None:
        if ev.name == "atr":
            if ev.ready:
                self.atr[ev.symbol] = ev.value
            return
        if ev.name == "vwap":
            self.vwap[ev.symbol] = ev.value
        elif ev.name == "ema50" and ev.ready:
            self.ema[ev.symbol] = ev.value
        self.handle(ev)

    def handle(self, ev: IndicatorValue) -> None:
        raise NotImplementedError

    def fire(self, ev: IndicatorValue, side: Side, level: float) -> None:
        c = ev.candle
        self.emit(Signal(ev.ts, c.symbol, self.trigger, side, c.close, level, self.atr.get(c.symbol),
                         ema50=self.ema.get(c.symbol), vwap=self.vwap.get(c.symbol)))
        self.last_charge.pop(c.symbol, None)

    # -- live charge meter
    def levels_for(self, symbol: str, price: float) -> tuple[Side, float] | None:
        raise NotImplementedError

    def on_tick(self, t: Tick) -> None:
        atr = self.atr.get(t.symbol)
        lv = self.levels_for(t.symbol, t.price)
        if not atr or lv is None:
            return
        side, level = lv
        dist = abs(t.price - level) / atr
        charge = int(max(0.0, 1.0 - dist / CHARGE_WINDOW_ATR) * 100)
        prev = self.last_charge.get(t.symbol)
        if prev and prev[0] == side and abs(prev[1] - charge) < 2:
            return
        self.last_charge[t.symbol] = (side, charge)
        self.emit(SetupUpdate(t.ts, t.symbol, self.trigger, side, level, round(dist, 2), charge))


class _CrossBot(_SignalBot):
    indicator = ""

    def setup(self) -> None:
        super().setup()
        self.prev: dict[str, _Prev] = {}
        self.level: dict[str, float] = {}

    def handle(self, ev: IndicatorValue) -> None:
        if ev.name != self.indicator or not ev.ready:
            return
        c, level = ev.candle, ev.value
        day = c.start.date()
        prev = self.prev.get(c.symbol)
        if prev and prev.day == day and not ev.backfill:
            if prev.close <= prev.level and c.close > level:
                self.fire(ev, Side.CALL, level)
            elif prev.close >= prev.level and c.close < level:
                self.fire(ev, Side.PUT, level)
        self.prev[c.symbol] = _Prev(day, c.close, level)
        self.level[c.symbol] = level

    def levels_for(self, symbol: str, price: float):
        level = self.level.get(symbol)
        if level is None:
            return None
        return (Side.PUT if price > level else Side.CALL), level


class VWAPCrossBot(_CrossBot):
    name = "sig_vwap_cross"
    skill = "Fire when a 1-min candle closes across VWAP (above = CALL, below = PUT)"
    trigger = "vwap_cross"
    indicator = "vwap"


class EMACrossBot(_CrossBot):
    name = "sig_ema50_cross"
    skill = "Fire when a 1-min candle closes across the 50 EMA (above = CALL, below = PUT)"
    trigger = "ema50_cross"
    indicator = "ema50"


class ORBBot(_SignalBot):
    name = "sig_orb"
    skill = "Fire when a 1-min candle closes outside the 15-minute opening range (once per side per day)"
    trigger = "orb"

    def setup(self) -> None:
        super().setup()
        self.day: dict[str, date] = {}
        self.fired: dict[str, set[Side]] = {}
        self.prev_close: dict[str, float] = {}
        self.range: dict[str, tuple[float, float]] = {}

    def handle(self, ev: IndicatorValue) -> None:
        if ev.name != "opening_range":
            return
        c = ev.candle
        day = c.start.date()
        if self.day.get(c.symbol) != day:
            self.day[c.symbol] = day
            self.fired[c.symbol] = set()
            self.range.pop(c.symbol, None)
            self.prev_close.pop(c.symbol, None)
        prev = self.prev_close.get(c.symbol)
        self.prev_close[c.symbol] = c.close
        if not ev.ready or ev.low is None:
            return
        just_locked = c.symbol not in self.range
        hi, lo = ev.value, ev.low
        self.range[c.symbol] = (hi, lo)
        if just_locked or prev is None or ev.backfill:
            return  # the candle that completes the range can't break it
        fired = self.fired[c.symbol]
        if Side.CALL not in fired and prev <= hi < c.close:
            fired.add(Side.CALL)
            self.fire(ev, Side.CALL, hi)
        elif Side.PUT not in fired and prev >= lo > c.close:
            fired.add(Side.PUT)
            self.fire(ev, Side.PUT, lo)

    def levels_for(self, symbol: str, price: float):
        rng = self.range.get(symbol)
        if not rng:
            return None
        hi, lo = rng
        if not (lo <= price <= hi):
            return None
        fired = self.fired.get(symbol, set())
        options = []
        if Side.CALL not in fired:
            options.append((hi - price, Side.CALL, hi))
        if Side.PUT not in fired:
            options.append((price - lo, Side.PUT, lo))
        if not options:
            return None
        _, side, level = min(options)
        return side, level
