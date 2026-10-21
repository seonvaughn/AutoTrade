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


NTZ_TFS = (2, 5, 10)            # minutes: the chart he watches 09:30-10:00, 10:00-11:00, after 11:00
SMA_LEN = 200
LEVEL_SESSIONS = 10             # sessions of hourly closes searched for "bends"


class OpeningRangeNTZBot(_ChartSignalBot):
    """docs/videos/boring-orb-ntz.md: the 15-minute opening range, traded only outside the no-trading zone, with the
    200 SMA, on the retest.

      NTZ        min(pre-market low, yesterday's low) .. max(pre-market high, yesterday's high)
      chart      2m before 10:00, 5m until 11:00, 10m after; its 200 SMA (carried across days) is the direction
      break      a candle on that chart closes beyond both the opening range and the NTZ, on the SMA's side
      retest     a later candle touches that edge and closes back beyond it: enter at its close (the next candle's
                 open: "you jump a candle after the retest"); a close back inside cancels the break
      stop       the other side of the opening range
      target     the nearest hourly level (a bend in hourly closes) at least smc.min_rr x risk away; none, no trade
    One signal per ticker per day. Without pre-market data there is no NTZ, and no signal."""
    name = "sig_orb_ntz"
    skill = ("15m opening range retest, only outside the no-trading zone (pre-market + yesterday's range) and on "
             "the 200 SMA's side; stop across the range, target the next hourly level")
    trigger = "orb_ntz_retest"

    def setup(self) -> None:
        super().setup()
        self.pre: dict[str, dict[str, list[float]]] = {}       # symbol -> day -> [pre-market high, low]
        self.bars: dict[tuple[str, int], Optional[list]] = {}  # (symbol, tf) -> building [start, o, h, l, c]
        self.closes: dict[tuple[str, int], list[float]] = {}   # (symbol, tf) -> last SMA_LEN closes
        self.hours: dict[str, list[tuple[date, float]]] = {}   # symbol -> hourly closes (day, close)
        self.hour_bar: dict[str, list] = {}
        self.st: dict[str, dict] = {}
        self.requested: set[date] = set()
        self.on(CandleClosed, self.on_minute)

    async def start(self) -> None:
        from ..data.premarket import load_premarket
        if self.ctx.span:
            first, last = self.ctx.span
            source = self.cfg.data.source
        elif self.ctx.live:                                    # the studied history; today's comes at the open
            last = cal.now_et().date() - timedelta(days=1)
            first, source = last - timedelta(days=100), "alpaca"
        else:
            return
        self.pre = await load_premarket(self.cfg.symbols, first, last, source, self.cfg.data.daily_dir)

    async def _fetch_today(self, d: date) -> None:
        from ..data.premarket import load_premarket
        got = await load_premarket(self.cfg.symbols, d, d, "alpaca", self.cfg.data.daily_dir)
        for sym, days in got.items():
            self.pre.setdefault(sym, {}).update(days)

    def ntz(self, symbol: str, d: date) -> Optional[tuple[float, float]]:
        s = self.st.get(symbol)
        pm = self.pre.get(symbol, {}).get(d.isoformat())
        if not s or s["day"] != d or not pm or s["yhi"] is None:
            return None
        return min(pm[1], s["ylo"]), max(pm[0], s["yhi"])

    def on_minute(self, e: CandleClosed) -> None:
        c = e.candle
        d = c.start.date()
        open_ = cal.session_open(d)
        m = int((c.start - open_).total_seconds() // 60)
        if m < 0:
            return
        s = self.st.get(c.symbol)
        if self.ctx.live and d not in self.requested and d == cal.now_et().date() \
                and cal.now_et() >= open_ + timedelta(minutes=RANGE_MINUTES + 1):
            self.requested.add(d)               # today's pre-market, once Alpaca's free plan serves it (15 min old)
            self.spawn(self._fetch_today(d))
        if s is None or s["day"] != d:
            y = (s["hi"], s["lo"]) if s else (None, None)
            s = self.st[c.symbol] = {"day": d, "hi": c.high, "lo": c.low, "yhi": y[0], "ylo": y[1], "orh": None,
                                     "orl": None, "locked": False, "dir": None, "fired": False}
        s["hi"], s["lo"] = max(s["hi"], c.high), min(s["lo"], c.low)
        if m < RANGE_MINUTES:
            s["orh"] = c.high if s["orh"] is None else max(s["orh"], c.high)
            s["orl"] = c.low if s["orl"] is None else min(s["orl"], c.low)
            s["locked"] = m == RANGE_MINUTES - 1
        self._hourly(c, m)
        for n in NTZ_TFS:
            bar = self._aggregate(c, m, n)
            if bar is None:
                continue
            closes = self.closes.setdefault((c.symbol, n), [])
            closes.append(bar.close)
            del closes[:-SMA_LEN]
            start_m = m + 1 - n
            active = 2 if start_m < 30 else 5 if start_m < 90 else 10
            if n == active and len(closes) == SMA_LEN:
                self._on_bar(e, bar, sum(closes) / SMA_LEN, s)

    def _aggregate(self, c: Candle, m: int, n: int) -> Optional[Candle]:
        key = (c.symbol, n)
        b = self.bars.get(key)
        if m % n == 0 or b is None:
            b = self.bars[key] = [c.start, c.open, c.high, c.low, c.close]
        else:
            b[2], b[3], b[4] = max(b[2], c.high), min(b[3], c.low), c.close
        if (m + 1) % n:
            return None
        self.bars[key] = None
        return Candle(c.symbol, b[0], b[1], b[2], b[3], b[4], 0)

    def _hourly(self, c: Candle, m: int) -> None:
        last_minute = c.start + timedelta(minutes=1) >= cal.session_close(c.start.date())
        if (m + 1) % 60 == 0 or last_minute:
            hours = self.hours.setdefault(c.symbol, [])
            hours.append((c.start.date(), c.close))
            days = sorted({d for d, _ in hours})
            if len(days) > LEVEL_SESSIONS + 1:
                keep = days[-(LEVEL_SESSIONS + 1):]
                self.hours[c.symbol] = [h for h in hours if h[0] >= keep[0]]

    def levels(self, symbol: str, d: date) -> list[float]:
        """Hourly levels: every bend (a local high or low) of the hourly line chart, sessions before `d`."""
        closes = [cl for day, cl in self.hours.get(symbol, []) if day < d]
        return [closes[i] for i in range(1, len(closes) - 1)
                if (closes[i] - closes[i - 1]) * (closes[i + 1] - closes[i]) < 0]

    def _on_bar(self, e: CandleClosed, bar: Candle, sma: float, s: dict) -> None:
        if not s["locked"] or s["fired"]:
            return
        box = self.ntz(bar.symbol, bar.start.date())
        if box is None:
            return
        up, dn = max(s["orh"], box[1]), min(s["orl"], box[0])
        tol = 0.1 * (self.atr.get(bar.symbol) or 0.0)
        if s["dir"] is None:
            if bar.close > up and bar.close > sma:
                s["dir"] = Side.CALL
            elif bar.close < dn and bar.close < sma:
                s["dir"] = Side.PUT
            return
        way = 1 if s["dir"] is Side.CALL else -1
        edge = up if way > 0 else dn
        if way * (bar.close - edge) <= 0:
            s["dir"] = None                                    # closed back inside: the break failed
            return
        touched = bar.low <= edge + tol if way > 0 else bar.high >= edge - tol
        if not touched or way * (bar.close - sma) <= 0:
            return
        stop = s["orl"] if way > 0 else s["orh"]
        risk = abs(bar.close - stop)
        room = self.cfg.smc.min_rr * risk
        ahead = sorted((lv for lv in self.levels(bar.symbol, bar.start.date()) if way * (lv - bar.close) >= room),
                       key=lambda lv: abs(lv - bar.close))
        if risk <= 0 or not ahead:
            return
        s["fired"] = True
        tf = int((e.ts - bar.start).total_seconds() // 60)
        info = {"model": self.trigger, "setup_tf": "15m", "entry_tf": f"{tf}m", "range": [s["orl"], s["orh"]],
                "ntz": list(box), "sma200": round(sma, 2)}
        self.emit(Signal(e.ts, bar.symbol, self.trigger, s["dir"], bar.close, edge, self.atr.get(bar.symbol),
                         ema50=self.ema.get(bar.symbol), vwap=self.vwap.get(bar.symbol), backfill=e.backfill,
                         stop=stop, target=ahead[0], setup=info))
