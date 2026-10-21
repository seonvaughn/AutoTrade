"""Indicator bots — each one computes exactly one study on closed 1-minute candles.

They are registered ATR first, so by the time a signal bot sees a VWAP/EMA/range
value for a candle, the ATR for that same candle is already known.
"""
from __future__ import annotations

from datetime import date, timedelta

from ..core import calendar as cal

from ..core.events import CandleClosed, IndicatorValue
from .base import Bot


class ATRBot(Bot):
    name = "atr"
    skill = "Average True Range (Wilder, 14) — the yardstick for distance and 'charge %'"
    period = 14

    def setup(self) -> None:
        self.state: dict[str, dict] = {}
        self.on(CandleClosed, self.on_candle)

    def on_candle(self, ev: CandleClosed) -> None:
        c = ev.candle
        s = self.state.setdefault(c.symbol, {"prev": None, "trs": [], "atr": None})
        pc = s["prev"]
        tr = c.high - c.low if pc is None else max(c.high - c.low, abs(c.high - pc), abs(c.low - pc))
        s["prev"] = c.close
        if s["atr"] is None:
            s["trs"].append(tr)
            if len(s["trs"]) >= self.period:
                s["atr"] = sum(s["trs"]) / len(s["trs"])
        else:
            s["atr"] = (s["atr"] * (self.period - 1) + tr) / self.period
        value = s["atr"] if s["atr"] is not None else sum(s["trs"]) / len(s["trs"])
        self.emit(IndicatorValue(ev.ts, "atr", c.symbol, value, c, ev.backfill, ready=s["atr"] is not None))


class VWAPBot(Bot):
    name = "vwap"
    skill = "Session VWAP, reset every morning at 9:30"

    def setup(self) -> None:
        self.state: dict[str, tuple[date, float, float]] = {}
        self.on(CandleClosed, self.on_candle)

    def on_candle(self, ev: CandleClosed) -> None:
        c = ev.candle
        day = c.start.date()
        d, pv, v = self.state.get(c.symbol, (None, 0.0, 0.0))
        if d != day:
            pv, v = 0.0, 0.0
        vol = c.volume if c.volume > 0 else 1.0
        pv += c.typical * vol
        v += vol
        self.state[c.symbol] = (day, pv, v)
        self.emit(IndicatorValue(ev.ts, "vwap", c.symbol, pv / v, c, ev.backfill))


class EMABot(Bot):
    name = "ema50"
    skill = "50-period EMA of 1-minute closes (continues across days, seeded with an SMA)"
    period = 50

    def setup(self) -> None:
        self.state: dict[str, dict] = {}
        self.on(CandleClosed, self.on_candle)

    def on_candle(self, ev: CandleClosed) -> None:
        c = ev.candle
        s = self.state.setdefault(c.symbol, {"closes": [], "ema": None})
        if s["ema"] is None:
            s["closes"].append(c.close)
            if len(s["closes"]) >= self.period:
                s["ema"] = sum(s["closes"]) / len(s["closes"])
            value = sum(s["closes"]) / len(s["closes"])
        else:
            k = 2.0 / (self.period + 1)
            s["ema"] = c.close * k + s["ema"] * (1 - k)
            value = s["ema"]
        self.emit(IndicatorValue(ev.ts, "ema50", c.symbol, value, c, ev.backfill, ready=s["ema"] is not None))


class OpeningRangeBot(Bot):
    name = "opening_range"
    skill = "High/low of the first 15 minutes of the session (9:30-9:45 ET); locks after"
    minutes = 15

    def setup(self) -> None:
        self.state: dict[str, dict] = {}
        self.on(CandleClosed, self.on_candle)

    def on_candle(self, ev: CandleClosed) -> None:
        c = ev.candle
        day = c.start.date()
        s = self.state.get(c.symbol)
        if s is None or s["day"] != day:
            s = self.state[c.symbol] = {"day": day, "hi": None, "lo": None, "locked": False}
        end = cal.session_open(day) + timedelta(minutes=self.minutes)
        if not s["locked"]:
            if c.start < end:
                s["hi"] = c.high if s["hi"] is None else max(s["hi"], c.high)
                s["lo"] = c.low if s["lo"] is None else min(s["lo"], c.low)
            if c.start >= end - timedelta(minutes=1) and s["hi"] is not None:
                s["locked"] = True
        hi = s["hi"] if s["hi"] is not None else c.high
        lo = s["lo"] if s["lo"] is not None else c.low
        self.emit(IndicatorValue(ev.ts, "opening_range", c.symbol, hi, c, ev.backfill, low=lo, ready=s["locked"]))

    def range(self, symbol: str):
        s = self.state.get(symbol)
        return (s["hi"], s["lo"], s["locked"]) if s else (None, None, False)
