"""Chart-reading bots — each studies one thing across timeframes.

  timeframes   builds 30s / 5m / 15m / 30m / 1h candles next to the 1-minute ones
  htf_levels   reads daily candles: prior week / month / 52-week highs and lows, daily + weekly trend
  structure    swing highs and lows per timeframe: trend (higher highs and lows, or lower), breaks of
               structure, Fibonacci retracements of the latest swing
  zones        supply and demand zones: the quiet base right before a strong, decisive move

Everything here looks only at closed candles, so nothing peeks at the future. A swing point is
confirmed only after SWING_K candles have closed on each side of it.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from ..core import calendar as cal
from ..core.events import (BarClosed, Candle, CandleClosed, Heartbeat, KeyLevel, Side, StructureBreak, Tick)
from .base import Bot

INTRADAY = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
SWING_K = 2                 # a swing high needs SWING_K lower highs on each side (fractal)
FIB_RATIOS = (0.382, 0.5, 0.618, 0.786)


# ---------------------------------------------------------------- pure chart reading
def find_swings(bars: list[Candle], k: int = SWING_K) -> list[tuple[int, str, float]]:
    """Confirmed swing points: (index, "high"|"low", price)."""
    out = []
    for i in range(k, len(bars) - k):
        hi, lo = bars[i].high, bars[i].low
        if all(hi > bars[j].high for j in range(i - k, i)) and all(hi >= bars[j].high for j in range(i + 1, i + k + 1)):
            out.append((i, "high", hi))
        if all(lo < bars[j].low for j in range(i - k, i)) and all(lo <= bars[j].low for j in range(i + 1, i + k + 1)):
            out.append((i, "low", lo))
    return out


def trend_of(swings: list[tuple[int, str, float]]) -> str:
    """bullish = higher highs and higher lows; bearish = lower highs and lower lows; else range."""
    highs = [p for _, kind, p in swings if kind == "high"][-2:]
    lows = [p for _, kind, p in swings if kind == "low"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "unknown"
    if highs[1] > highs[0] and lows[1] > lows[0]:
        return "bullish"
    if highs[1] < highs[0] and lows[1] < lows[0]:
        return "bearish"
    return "range"


def latest_leg(bars: list[Candle], swings: list[tuple[int, str, float]], trend: str) -> Optional[dict]:
    """The last impulse leg in the trend's direction, with its Fibonacci retracement levels."""
    if trend == "bullish":
        lows = [s for s in swings if s[1] == "low"]
        if not lows:
            return None
        i, _, low = lows[-1]
        high = max(b.high for b in bars[i:])
        if high <= low:
            return None
        return {"direction": "up", "from": low, "to": high,
                "levels": {r: round(high - r * (high - low), 4) for r in FIB_RATIOS}, "id": (i, round(low, 4))}
    if trend == "bearish":
        highs = [s for s in swings if s[1] == "high"]
        if not highs:
            return None
        i, _, high = highs[-1]
        low = min(b.low for b in bars[i:])
        if high <= low:
            return None
        return {"direction": "down", "from": high, "to": low,
                "levels": {r: round(low + r * (high - low), 4) for r in FIB_RATIOS}, "id": (i, round(high, 4))}
    return None


def aggregate(bars: list[Candle], key) -> list[Candle]:
    """Merge consecutive candles that share key(candle) into one candle."""
    out: list[Candle] = []
    last_key = object()
    for b in bars:
        k = key(b)
        if out and k == last_key:
            c = out[-1]
            c.high, c.low, c.close, c.volume = max(c.high, b.high), min(c.low, b.low), b.close, c.volume + b.volume
        else:
            out.append(Candle(b.symbol, b.start, b.open, b.high, b.low, b.close, b.volume))
        last_key = k
    return out


# ---------------------------------------------------------------- bots
class TimeframeBot(Bot):
    name = "timeframes"
    skill = "Build 30-second, 5-, 15-, 30-minute and 1-hour candles alongside the 1-minute ones"

    def setup(self) -> None:
        self.open: dict[tuple[str, str], tuple[int, Candle, bool]] = {}  # (sym, tf) -> (bucket, candle, backfill)
        self.half: dict[str, tuple[datetime, Candle]] = {}               # live/replay 30s candle being built
        self.on(CandleClosed, self.on_candle)
        self.on(Tick, self.on_tick)
        self.on(Heartbeat, self.on_heartbeat)

    def on_candle(self, e: CandleClosed) -> None:
        c = e.candle
        d = c.start.date()
        idx = int((c.start - cal.session_open(d)).total_seconds() // 60)
        last_minute = c.start + timedelta(minutes=1) >= cal.session_close(d)
        for tf, n in INTRADAY.items():
            bucket = d.toordinal() * 10_000 + idx // n
            cur = self.open.get((c.symbol, tf))
            if cur and cur[0] != bucket:
                self._emit(tf, cur[1], cur[2], e.ts)
                cur = None
            if cur is None:
                start = cal.session_open(d) + timedelta(minutes=(idx // n) * n)
                cur = (bucket, Candle(c.symbol, start, c.open, c.high, c.low, c.close, c.volume), e.backfill)
            else:
                b = cur[1]
                b.high, b.low, b.close, b.volume = max(b.high, c.high), min(b.low, c.low), c.close, b.volume + c.volume
            self.open[(c.symbol, tf)] = cur
            if (idx + 1) % n == 0 or last_minute:
                self._emit(tf, cur[1], cur[2], e.ts)
                del self.open[(c.symbol, tf)]
        if e.backfill:  # history has no ticks: split the minute along the replay's price path
            from .price_feed_bot import PriceFeedBot
            path = PriceFeedBot.path(c, 12)
            for half, seg in ((0, path[:7]), (1, path[6:])):
                start = c.start + timedelta(seconds=30 * half)
                bar = Candle(c.symbol, start, seg[0], max(seg), min(seg), seg[-1], c.volume / 2)
                self.emit(BarClosed(start + timedelta(seconds=30), "30s", bar, backfill=True))

    def _emit(self, tf: str, c: Candle, backfill: bool, ts) -> None:
        self.emit(BarClosed(ts, tf, c, backfill))

    def on_tick(self, t: Tick) -> None:
        d = t.ts.date()
        if not (cal.session_open(d) <= t.ts < cal.session_close(d)):
            return
        start = t.ts.replace(second=0 if t.ts.second < 30 else 30, microsecond=0)
        cur = self.half.get(t.symbol)
        if cur and start < cur[0]:
            return                           # late tick for a 30s candle that already closed
        if cur and cur[0] != start:
            self.emit(BarClosed(cur[0] + timedelta(seconds=30), "30s", cur[1]))
            cur = None
        if cur is None:
            self.half[t.symbol] = (start, Candle(t.symbol, start, t.price, t.price, t.price, t.price, t.size))
        else:
            b = cur[1]
            b.high, b.low, b.close, b.volume = max(b.high, t.price), min(b.low, t.price), t.price, b.volume + t.size

    def on_heartbeat(self, hb: Heartbeat) -> None:
        grace = timedelta(seconds=1.5 if self.ctx.live else 0)
        for sym, (start, bar) in list(self.half.items()):
            if hb.ts >= start + timedelta(seconds=30) + grace:
                del self.half[sym]
                self.emit(BarClosed(start + timedelta(seconds=30), "30s", bar))


class HigherTimeframeBot(Bot):
    name = "htf_levels"
    skill = "Read daily candles: prior week, month and 52-week highs and lows, and the daily and weekly trend"

    def setup(self) -> None:
        self.daily: dict[str, list[Candle]] = {}
        self.cache: dict[tuple[str, date], dict] = {}

    async def start(self) -> None:
        if self.ctx.span:
            first, last = self.ctx.span
        elif self.ctx.live:
            first = last = cal.now_et().date()
        else:
            return
        from ..data.daily import load_daily
        self.daily = await load_daily(self.cfg.symbols, first - timedelta(days=400), last,
                                      self.cfg.data.source if not self.ctx.live else "alpaca", self.cfg.data.daily_dir)

    def study(self, symbol: str, day: date) -> dict:
        """Everything learned from daily candles strictly before `day`."""
        key = (symbol, day)
        if key in self.cache:
            return self.cache[key]
        past = [b for b in self.daily.get(symbol, []) if b.start.date() < day]
        out: dict = {"levels": [], "trend": {"D": "unknown", "W": "unknown"}, "days": len(past)}
        if past:
            this_week = day.isocalendar()[:2]
            weeks = aggregate([b for b in past if b.start.date().isocalendar()[:2] != this_week],
                              key=lambda b: b.start.date().isocalendar()[:2])
            months = aggregate([b for b in past if (b.start.year, b.start.month) != (day.year, day.month)],
                               key=lambda b: (b.start.year, b.start.month))
            year = [b for b in past if b.start.date() >= day - timedelta(days=365)]
            lv = []
            if weeks:
                lv += [KeyLevel(weeks[-1].high, "prior week high", 2), KeyLevel(weeks[-1].low, "prior week low", 2)]
            if months:
                lv += [KeyLevel(months[-1].high, "prior month high", 3), KeyLevel(months[-1].low, "prior month low", 3)]
            if year:
                lv += [KeyLevel(max(b.high for b in year), "52-week high", 4),
                       KeyLevel(min(b.low for b in year), "52-week low", 4)]
            out["levels"] = lv
            out["trend"] = {"D": trend_of(find_swings(past[-120:])), "W": trend_of(find_swings(weeks[-60:]))}
        self.cache[key] = out
        return out


class StructureBot(Bot):
    name = "structure"
    skill = "Read swing highs and lows per timeframe: trend, breaks of structure, Fibonacci retracements"
    KEEP = 300

    def setup(self) -> None:
        self.bars: dict[tuple[str, str], list[Candle]] = {}
        self.read: dict[tuple[str, str], tuple[list, str]] = {}   # (sym, tf) -> (swings, trend)
        self.broken: dict[tuple[str, str], set] = {}
        self.on(BarClosed, self.on_bar)

    def on_bar(self, e: BarClosed) -> None:
        if e.tf not in INTRADAY:
            return
        key = (e.candle.symbol, e.tf)
        bars = self.bars.setdefault(key, [])
        prev_close = bars[-1].close if bars else None
        prior = self.read.get(key, ([], "unknown"))[0]
        bars.append(e.candle)
        if len(bars) > self.KEEP:
            del bars[: len(bars) - self.KEEP]
        swings = find_swings(bars)
        self.read[key] = (swings, trend_of(swings))
        # break of structure: this close crosses the last swing confirmed *before* this candle
        c = e.candle
        done = self.broken.setdefault(key, set())
        last_high = next((p for _, k, p in reversed(prior) if k == "high"), None)
        last_low = next((p for _, k, p in reversed(prior) if k == "low"), None)
        if prev_close is not None and last_high is not None and prev_close <= last_high < c.close \
                and ("high", last_high) not in done:
            done.add(("high", last_high))
            self.emit(StructureBreak(e.ts, c.symbol, e.tf, Side.CALL, last_high, c, e.backfill))
        elif prev_close is not None and last_low is not None and prev_close >= last_low > c.close \
                and ("low", last_low) not in done:
            done.add(("low", last_low))
            self.emit(StructureBreak(e.ts, c.symbol, e.tf, Side.PUT, last_low, c, e.backfill))

    def trend(self, symbol: str, tf: str, day: Optional[date] = None) -> str:
        if tf in ("D", "W"):
            htf = self.bot("htf_levels")
            return htf.study(symbol, day)["trend"][tf] if htf and day else "unknown"
        return self.read.get((symbol, tf), ([], "unknown"))[1]

    def fib(self, symbol: str, tf: str) -> Optional[dict]:
        bars = self.bars.get((symbol, tf))
        if not bars:
            return None
        swings, trend = self.read[(symbol, tf)]
        return latest_leg(bars, swings, trend)


class ZonesBot(Bot):
    name = "zones"
    skill = "Find supply and demand zones: the quiet base right before a strong move, until price breaks through"
    TIMEFRAMES = ("15m", "30m", "1h")
    MAX_PER_SIDE = 4

    def setup(self) -> None:
        self.prev: dict[tuple[str, str], Candle] = {}
        self.atr: dict[tuple[str, str], float] = {}
        self.active: dict[str, list[dict]] = {}
        self.on(BarClosed, self.on_bar)
        self.on(CandleClosed, self.on_minute)

    def on_bar(self, e: BarClosed) -> None:
        if e.tf not in self.TIMEFRAMES:
            return
        c, key = e.candle, (e.candle.symbol, e.tf)
        rng = c.high - c.low
        atr = self.atr.get(key)
        base = self.prev.get(key)
        self.prev[key] = c
        self.atr[key] = rng if atr is None else atr + (rng - atr) / 14
        if atr is None or base is None or rng <= 0:
            return
        r = self.cfg.research
        body = abs(c.close - c.open)
        base_rng = base.high - base.low
        quiet = base_rng > 0 and abs(base.close - base.open) <= 0.5 * base_rng
        if rng >= r.zone_impulse_atr * atr and body >= 0.6 * rng and quiet:
            kind = "demand" if c.close > c.open else "supply"
            zone = {"kind": kind, "tf": e.tf, "lo": base.low, "hi": base.high, "since": c.start.isoformat(),
                    "touches": 0, "inside": False, "id": f"{e.tf}-{base.start.isoformat()}"}
            zs = [z for z in self.active.setdefault(c.symbol, []) if z["id"] != zone["id"]]
            zs.append(zone)
            same = [z for z in zs if z["kind"] == kind]
            if len(same) > self.MAX_PER_SIDE:
                zs.remove(same[0])
            self.active[c.symbol] = zs

    def on_minute(self, e: CandleClosed) -> None:
        c = e.candle
        keep = []
        for z in self.active.get(c.symbol, []):
            if (z["kind"] == "demand" and c.close < z["lo"]) or (z["kind"] == "supply" and c.close > z["hi"]):
                continue                     # price closed through it: the zone failed
            inside = c.low <= z["hi"] and c.high >= z["lo"]
            if inside and not z["inside"]:
                z["touches"] += 1
            z["inside"] = inside
            keep.append(z)
        self.active[c.symbol] = keep

    def zones(self, symbol: str) -> list[dict]:
        return [dict(z) for z in self.active.get(symbol, [])]
