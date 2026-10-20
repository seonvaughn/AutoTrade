"""15-minute opening range (docs/videos/15m-opening-range.md): one bot, three entry models.

  1. mark the high and low of the first 15-minute candle of the New York session (09:30-09:45 ET)
  2. wait for a 5-minute candle to close above the range high (longs) or below the range low (shorts)
  3. enter on the 1-minute chart (until the worker's end time; the video trades the first 2 hours):
     orb15_breakout  displacement: a 1m gap forms beyond the range; enter on the candle that completes it,
                     stop below the middle (displacement) candle, target 1:2
     orb15_retest    price comes back to the broken edge, holds it (a 1m candle touches it and closes back
                     beyond it), then a 1m break of structure in the break's direction; stop at the retest
                     swing, target 1:2
     orb15_reversal  the break fails (a 5m candle closes back inside the range: no continuation, a range
                     day), then a 1m break of structure that shifts the trend back the other way; stop beyond the
                     furthest point of the failed break, target the opposite high/low of day (at least 1R away)

Each signal carries its own stop and target; the research gate, morning study and lessons book judge it like any
other planned trade. Closed candles only.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ..core import calendar as cal
from ..core.events import BarClosed, BreakOfStructure, Candle, CandleClosed, Side, Signal
from .signal_bots import _ChartSignalBot

ORB_TRIGGERS = ("orb15_breakout", "orb15_retest", "orb15_reversal")
RANGE_MINUTES = 15


class OpeningRange15Bot(_ChartSignalBot):
    name = "sig_orb15"
    skill = ("15-minute opening range: a 5m close beyond it, then a 1m entry (breakout gap, retest, or reversal "
             "of a failed break); fixed 1:2 or high/low of day")
    trigger = "orb15_breakout"

    def setup(self) -> None:
        super().setup()
        self.day: dict[str, date] = {}
        self.st: dict[str, dict] = {}
        self.on(CandleClosed, self.on_minute)
        self.on(BarClosed, self.on_bar)
        self.on(BreakOfStructure, self.on_bos)
        used = {t for w in self.cfg.workers if w.enabled for t in w.triggers}
        self.wanted = set(ORB_TRIGGERS) & used or set(ORB_TRIGGERS)

    def _state(self, c: Candle) -> dict:
        d = c.start.date()
        if self.day.get(c.symbol) != d:
            self.day[c.symbol] = d
            self.st[c.symbol] = {"hi": None, "lo": None, "locked": False, "dir": None, "broke_at": None,
                                 "last3": [], "fired": set(), "retest": None, "failed": False,
                                 "dhi": c.high, "dlo": c.low, "ext": None}
        return self.st[c.symbol]

    # ---- step 1: the range, and the day's running high/low
    def on_minute(self, e: CandleClosed) -> None:
        c = e.candle
        s = self._state(c)
        s["dhi"], s["dlo"] = max(s["dhi"], c.high), min(s["dlo"], c.low)
        open_ = cal.session_open(c.start.date())
        if c.start < open_ + timedelta(minutes=RANGE_MINUTES):
            s["hi"] = c.high if s["hi"] is None else max(s["hi"], c.high)
            s["lo"] = c.low if s["lo"] is None else min(s["lo"], c.low)
            if c.start + timedelta(minutes=1) >= open_ + timedelta(minutes=RANGE_MINUTES):
                s["locked"] = True
            return
        if not s["locked"] or s["dir"] is None:
            return
        way = 1 if s["dir"] is Side.CALL else -1
        ext = c.high if way > 0 else c.low           # the furthest the break got: the reversal's stop
        s["ext"] = ext if s["ext"] is None else (max(s["ext"], ext) if way > 0 else min(s["ext"], ext))
        if s["failed"]:
            return
        self._breakout(e, s, way)
        self._retest_watch(c, s, way)

    # ---- step 2: a 5-minute close beyond the range (and a failed break for the reversal)
    def on_bar(self, e: BarClosed) -> None:
        if e.tf != "5m":
            return
        c = e.candle
        s = self.st.get(c.symbol)
        if not s or not s["locked"] or self.day.get(c.symbol) != c.start.date():
            return
        if s["dir"] is None:
            if c.close > s["hi"]:
                s["dir"], s["broke_at"] = Side.CALL, e.ts
            elif c.close < s["lo"]:
                s["dir"], s["broke_at"] = Side.PUT, e.ts
            return
        if not s["failed"] and s["lo"] <= c.close <= s["hi"]:
            s["failed"] = True                         # the break failed: a 5m close back inside the range

    # ---- step 3, model 1: displacement gap beyond the range
    def _breakout(self, e: CandleClosed, s: dict, way: int) -> None:
        c = e.candle
        win = s["last3"]
        win.append(c)
        if len(win) > 3:
            del win[0]
        if len(win) < 3 or "orb15_breakout" in s["fired"] or win[0].start < s["broke_at"] - timedelta(minutes=5):
            return
        c1, c2, c3 = win
        edge = s["hi"] if way > 0 else s["lo"]
        if way > 0 and c3.low > c1.high and c2.close > c2.open and c3.close > edge:
            stop = c2.low
        elif way < 0 and c3.high < c1.low and c2.close < c2.open and c3.close < edge:
            stop = c2.high
        else:
            return
        self._fire("orb15_breakout", e.ts, c, s["dir"], edge, stop, c3.close + way * 2 * abs(c3.close - stop),
                   s, e.backfill)

    # ---- model 2: retest of the broken edge
    def _retest_watch(self, c: Candle, s: dict, way: int) -> None:
        if "orb15_retest" in s["fired"]:
            return
        atr = self.atr.get(c.symbol) or 0.0
        edge = s["hi"] if way > 0 else s["lo"]
        tol = 0.1 * atr
        touched = (c.low <= edge + tol) if way > 0 else (c.high >= edge - tol)
        held = (c.close > edge) if way > 0 else (c.close < edge)
        if touched and held:
            ext = c.low if way > 0 else c.high
            r = s["retest"]
            s["retest"] = {"ext": ext if r is None else (min(r["ext"], ext) if way > 0 else max(r["ext"], ext))}
        elif s["retest"] and not held:
            s["retest"] = None                         # closed back inside the range: the retest failed

    def on_bos(self, e: BreakOfStructure) -> None:
        if e.tf != "1m":
            return
        s = self.st.get(e.symbol)
        if not s or s["dir"] is None or self.day.get(e.symbol) != e.candle.start.date():
            return
        c, atr = e.candle, (self.atr.get(e.symbol) or 0.0)
        if not s["failed"] and s["retest"] and e.side is s["dir"] and "orb15_retest" not in s["fired"]:
            way = 1 if s["dir"] is Side.CALL else -1
            stop = s["retest"]["ext"] - way * 0.1 * atr
            self._fire("orb15_retest", e.ts, c, s["dir"], s["hi"] if way > 0 else s["lo"], stop,
                       c.close + way * 2 * abs(c.close - stop), s, e.backfill)
        elif s["failed"] and s["ext"] is not None and e.side is not s["dir"] and e.shift \
                and "orb15_reversal" not in s["fired"]:
            side = e.side                              # back the other way after the failed break
            way = 1 if side is Side.CALL else -1
            stop = s["ext"] - way * 0.1 * atr
            target = s["dhi"] if way > 0 else s["dlo"]  # back to the high (or low) of day
            if abs(c.close - stop) > 0 and way * (target - c.close) >= abs(c.close - stop):
                self._fire("orb15_reversal", e.ts, c, side, e.level, stop, target, s, e.backfill)

    def _fire(self, trigger: str, ts, c: Candle, side: Side, level: float, stop: float, target: float,
              s: dict, backfill: bool) -> None:
        s["fired"].add(trigger)
        if trigger not in self.wanted:
            return
        info = {"model": trigger, "setup_tf": "15m", "entry_tf": "1m", "range": [s["lo"], s["hi"]],
                "broke": s["dir"].value if s["dir"] else None}
        self.emit(Signal(ts, c.symbol, trigger, side, c.close, level, self.atr.get(c.symbol),
                         ema50=self.ema.get(c.symbol), vwap=self.vwap.get(c.symbol), backfill=backfill,
                         stop=stop, target=target, setup=info))

    def range(self, symbol: str) -> Optional[dict]:
        s = self.st.get(symbol)
        return {k: s[k] for k in ("hi", "lo", "locked", "dir", "failed")} if s else None
