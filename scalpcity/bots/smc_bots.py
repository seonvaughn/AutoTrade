"""Smart-money bots: TJR's boot camp model (notes in docs/tjr-bootcamp), one skill per bot.

  market_structure  highs and lows by TJR's two-candle rule; a break of structure is a candle BODY
                    closing beyond the most recent high or low (wicks never count); trend per timeframe
  liquidity         resting highs (buy-side) and lows (sell-side) per timeframe; reports each sweep
  imbalances        fair value gaps (three-candle rule) until filled or closed through
  order_blocks      the move that swept liquidity right before a break of structure
  daily_bias        each morning: the daily structure (last daily break), the weekly, and the 4-hour trend
  news_calendar     no entries on CPI / PPI / FOMC / NFP days; wait after other high-impact releases
  sig_smc           the entry models: sweep -> break -> retrace into an order block or gap in
                    discount/premium -> lower-timeframe break (smc_retrace); or the break itself (smc_bos)

Everything reads closed candles only, and daily candles strictly before the session.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from ..core import calendar as cal
from ..core.config import SMC_TRIGGERS
from ..core.events import (BarClosed, BreakOfStructure, Candle, CandleClosed, LiquiditySweep, SessionEvent,
                           SessionKind, Side, Signal)
from .base import Bot
from .chart_bots import aggregate
from .signal_bots import _ChartSignalBot

STRUCTURE_TFS = ("1m", "5m", "15m", "30m", "1h", "4h")
GAP_TFS = ("1m", "5m", "15m", "1h")
ENTRY_TF = {"5m": "1m", "15m": "5m", "30m": "5m", "1h": "15m"}   # a setup is entered one timeframe lower (Day 35)


def _up(c: Candle) -> bool:
    return c.close > c.open


def _down(c: Candle) -> bool:
    return c.close < c.open


# ---------------------------------------------------------------- pure chart reading
class Structure:
    """TJR's market structure on one timeframe, fed closed candles in order (Day 6).

    A high is an up candle followed by a down candle (price: the higher wick of the two); a low is a down
    candle followed by an up candle. A break of structure is a close beyond the MOST RECENT high or low.
    """

    def __init__(self, keep: int = 500) -> None:
        self.keep = keep
        self.bars: list[Candle] = []
        self.offset = 0                               # absolute index of bars[0]
        self.highs: list[tuple[int, float]] = []      # (absolute index, price)
        self.lows: list[tuple[int, float]] = []
        self.trend = "unknown"
        self.high_broken = False                      # the most recent high was already closed above
        self.low_broken = False
        self.last_break: Optional[tuple] = None       # (Side, index of the broken swing, index of the breaking candle)

    @property
    def last_high(self) -> Optional[float]:
        return self.highs[-1][1] if self.highs else None

    @property
    def last_low(self) -> Optional[float]:
        return self.lows[-1][1] if self.lows else None

    def bar(self, index: int) -> Candle:
        return self.bars[index - self.offset]

    def since(self, index: int) -> list[Candle]:
        return self.bars[max(0, index - self.offset):]

    def update(self, c: Candle) -> list[tuple]:
        """Add a closed candle. Returns breaks: [("bos", Side, level, shift, broken swing index)]."""
        out = []
        if self.highs and not self.high_broken and c.close > self.highs[-1][1]:
            self.high_broken = True
            shift = self.trend != "bullish"
            self.trend = "bullish"
            out.append(("bos", Side.CALL, self.highs[-1][1], shift, self.highs[-1][0]))
            self.last_break = (Side.CALL, self.highs[-1][0], self.offset + len(self.bars))
        elif self.lows and not self.low_broken and c.close < self.lows[-1][1]:
            self.low_broken = True
            shift = self.trend != "bearish"
            self.trend = "bearish"
            out.append(("bos", Side.PUT, self.lows[-1][1], shift, self.lows[-1][0]))
            self.last_break = (Side.PUT, self.lows[-1][0], self.offset + len(self.bars))
        prev = self.bars[-1] if self.bars else None
        i = self.offset + len(self.bars)
        self.bars.append(c)
        if prev is not None:
            if _up(prev) and _down(c):
                at = i if c.high >= prev.high else i - 1
                self.highs.append((at, max(prev.high, c.high)))
                self.high_broken = False
            elif _down(prev) and _up(c):
                at = i if c.low <= prev.low else i - 1
                self.lows.append((at, min(prev.low, c.low)))
                self.low_broken = False
        if len(self.bars) > self.keep:
            drop = len(self.bars) - self.keep
            del self.bars[:drop]
            self.offset += drop
            self.highs = [h for h in self.highs if h[0] >= self.offset][-100:]
            self.lows = [x for x in self.lows if x[0] >= self.offset][-100:]
        return out


def find_gaps(c1: Candle, c2: Candle, c3: Candle) -> Optional[dict]:
    """Day 16: a bullish gap when candle 3's low is above candle 1's high; bearish when candle 3's high is
    below candle 1's low. Candle 2 is the displacement candle."""
    if c3.low > c1.high and _up(c2):
        return {"kind": "bullish", "lo": c1.high, "hi": c3.low}
    if c3.high < c1.low and _down(c2):
        return {"kind": "bearish", "lo": c3.high, "hi": c1.low}
    return None


def daily_structure(days: list[Candle]) -> str:
    """Trend of a series of higher-timeframe candles by TJR's rules (direction of the last break)."""
    return read_structure(days).trend


def read_structure(days: list[Candle]) -> Structure:
    s = Structure(keep=len(days) + 5)
    for d in days:
        s.update(d)
    return s


def dealing_range(s: Structure) -> Optional[dict]:
    """The current leg of a trend (Day 26/28): for a bearish trend, from the top of the move that broke structure
    down to the lowest low since; mirrored for bullish. Its 50% line splits premium from discount."""
    if not s.last_break or not s.bars:
        return None
    side, broken, _ = s.last_break
    leg = s.since(broken)
    if not leg:
        return None
    if side is Side.PUT:
        top = max(b.high for b in leg)
        bottom = min(b.low for b in leg)
    else:
        bottom = min(b.low for b in leg)
        top = max(b.high for b in leg)
    return {"top": top, "bottom": bottom, "eq": (top + bottom) / 2}


# ---------------------------------------------------------------- bots
class _PerTimeframe(Bot):
    """Feeds 1-minute candles and BarClosed candles through one handler, tagged with their timeframe."""
    TIMEFRAMES: tuple = ()

    def setup(self) -> None:
        self.on(CandleClosed, lambda e: self._feed("1m", e.candle, e.ts, e.backfill))
        self.on(BarClosed, lambda e: e.tf in self.TIMEFRAMES and self._feed(e.tf, e.candle, e.ts, e.backfill))

    def _feed(self, tf: str, c: Candle, ts: datetime, backfill: bool) -> None:
        raise NotImplementedError


class MarketStructureBot(_PerTimeframe):
    name = "market_structure"
    skill = "TJR structure per timeframe: two-candle highs and lows; a break only on a body close beyond the latest one"
    TIMEFRAMES = STRUCTURE_TFS

    def setup(self) -> None:
        super().setup()
        self.s: dict[tuple[str, str], Structure] = {}

    def _feed(self, tf: str, c: Candle, ts: datetime, backfill: bool) -> None:
        st = self.s.setdefault((c.symbol, tf), Structure())
        for _, side, level, shift, _i in st.update(c):
            self.emit(BreakOfStructure(ts, c.symbol, tf, side, level, c, shift, backfill))

    def get(self, symbol: str, tf: str) -> Optional[Structure]:
        return self.s.get((symbol, tf))

    def trend(self, symbol: str, tf: str) -> str:
        st = self.s.get((symbol, tf))
        return st.trend if st else "unknown"


class LiquidityBot(_PerTimeframe):
    name = "liquidity"
    skill = "Track resting highs and lows on each timeframe and report every sweep of them"
    TIMEFRAMES = STRUCTURE_TFS
    KEEP = 40

    def setup(self) -> None:
        super().setup()
        self.pools: dict[tuple[str, str], dict[str, list[tuple[float, datetime]]]] = {}
        self.seen: dict[tuple[str, str], tuple[int, int]] = {}   # last high/low index already pooled
        self.sweeps: dict[str, list[dict]] = {}
        self.day: dict[str, date] = {}

    def _feed(self, tf: str, c: Candle, ts: datetime, backfill: bool) -> None:
        st = self.bot("market_structure").get(c.symbol, tf)
        key = (c.symbol, tf)
        pools = self.pools.setdefault(key, {"high": [], "low": []})
        if tf == "1m":
            self._prior_day(c)
        # price taking out resting liquidity (wick or close: TJR counts both as "taken")
        for kind in ("high", "low"):
            keep = []
            for level, since in pools[kind]:
                if (kind == "high" and c.high > level) or (kind == "low" and c.low < level):
                    self._record(c, tf, kind, level, ts, backfill)
                else:
                    keep.append((level, since))
            pools[kind] = keep[-self.KEEP:]
        # new resting liquidity: highs and lows the structure confirmed with this candle
        if st:
            last_h, last_l = self.seen.get(key, (-1, -1))
            for i, price in st.highs:
                if i > last_h:
                    pools["high"].append((price, ts))
            for i, price in st.lows:
                if i > last_l:
                    pools["low"].append((price, ts))
            self.seen[key] = (st.highs[-1][0] if st.highs else last_h, st.lows[-1][0] if st.lows else last_l)

    def _prior_day(self, c: Candle) -> None:
        """The prior session's high and low are resting liquidity too (Day 8): tracked as timeframe "D"."""
        d = c.start.date()
        pools = self.pools.setdefault((c.symbol, "D"), {"high": [], "low": []})
        if self.day.get(c.symbol) != d:
            self.day[c.symbol] = d
            kl = self.bot("key_levels")
            past = kl.past_days(c.symbol, d) if kl else []
            if past:
                rec = kl.days[c.symbol][past[-1]]
                pools["high"], pools["low"] = [(rec["h"], c.start)], [(rec["l"], c.start)]
        for kind in ("high", "low"):
            keep = []
            for level, since in pools[kind]:
                if (kind == "high" and c.high > level) or (kind == "low" and c.low < level):
                    self._record(c, "D", kind, level, c.start + timedelta(minutes=1), False)
                else:
                    keep.append((level, since))
            pools[kind] = keep

    def _record(self, c: Candle, tf: str, kind: str, level: float, ts: datetime, backfill: bool) -> None:
        rows = self.sweeps.setdefault(c.symbol, [])
        rows.append({"tf": tf, "kind": kind, "level": level, "ts": ts, "start": c.start,
                     "closed_beyond": c.close > level if kind == "high" else c.close < level})
        if len(rows) > 3000:
            del rows[:1000]
        self.emit(LiquiditySweep(ts, c.symbol, tf, kind, level, c, backfill))

    def swept(self, symbol: str, kind: str, since: datetime, until: datetime, tfs=None) -> list[dict]:
        return [s for s in self.sweeps.get(symbol, []) if s["kind"] == kind and since <= s["start"] <= until
                and (tfs is None or s["tf"] in tfs)]

    def resting_prior_day(self, symbol: str) -> list[tuple[float, str, str]]:
        p = self.pools.get((symbol, "D"), {"high": [], "low": []})
        return [(lv, "high", "D") for lv, _ in p["high"]] + [(lv, "low", "D") for lv, _ in p["low"]]

    def resting(self, symbol: str, tfs) -> list[tuple[float, str, str]]:
        """Untaken liquidity: (price, "high"|"low", timeframe)."""
        out = []
        for tf in tfs:
            p = self.pools.get((symbol, tf))
            if p:
                out += [(lv, "high", tf) for lv, _ in p["high"]] + [(lv, "low", tf) for lv, _ in p["low"]]
        return out


class ImbalanceBot(_PerTimeframe):
    name = "imbalances"
    skill = "Mark fair value gaps (three-candle imbalances) and track how much of each is still unfilled"
    TIMEFRAMES = GAP_TFS
    MAX_PER_SIDE = 8

    def setup(self) -> None:
        super().setup()
        self.last3: dict[tuple[str, str], list[Candle]] = {}
        self.gaps: dict[str, list[dict]] = {}

    def _feed(self, tf: str, c: Candle, ts: datetime, backfill: bool) -> None:
        if tf == "1m":
            self._fill(c)
        win = self.last3.setdefault((c.symbol, tf), [])
        win.append(c)
        if len(win) > 3:
            del win[0]
        if len(win) == 3:
            g = find_gaps(*win)
            if g and g["hi"] - g["lo"] > 1e-4 * c.close:
                g.update(tf=tf, formed=c.start + (timedelta(minutes=1) if tf == "1m" else timedelta(0)),
                         start=win[0].start, top=g["hi"], bottom=g["lo"])
                gs = self.gaps.setdefault(c.symbol, [])
                gs.append(g)
                same = [x for x in gs if x["tf"] == tf and x["kind"] == g["kind"]]
                if len(same) > self.MAX_PER_SIDE:
                    gs.remove(same[0])

    def _fill(self, c: Candle) -> None:
        keep = []
        for g in self.gaps.get(c.symbol, []):
            if c.start < g["formed"]:
                keep.append(g)
                continue
            if g["kind"] == "bullish":
                if c.close < g["bottom"]:
                    continue                          # closed through it: gone (Day 18)
                g["top"] = min(g["top"], max(c.low, g["bottom"]))
            else:
                if c.close > g["top"]:
                    continue
                g["bottom"] = max(g["bottom"], min(c.high, g["top"]))
            keep.append(g)
        self.gaps[c.symbol] = keep

    def open_gaps(self, symbol: str, kind: str, since: datetime) -> list[dict]:
        """Gaps of one direction formed since `since` that still have an unfilled part."""
        return [dict(g) for g in self.gaps.get(symbol, []) if g["kind"] == kind and g["start"] >= since
                and g["top"] > g["bottom"]]


class OrderBlockBot(Bot):
    name = "order_blocks"
    skill = "Mark the order block: the move that swept liquidity right before a break of structure"

    def setup(self) -> None:
        self.blocks: dict[tuple[str, str], dict] = {}

    def mark(self, symbol: str, tf: str, side: Side, broken_index: int) -> Optional[dict]:
        """Called by the setup reader on a break (read-only use of the structure). For a bearish break the block
        is the last up candle at the top of the leg, from its body start to the high; mirrored for bullish."""
        st = self.bot("market_structure").get(symbol, tf)
        if st is None:
            return None
        leg = st.since(broken_index)[:-1] or st.since(broken_index)
        if not leg:
            return None
        if side is Side.PUT:
            ext_i = max(range(len(leg)), key=lambda j: leg[j].high)
            extreme = leg[ext_i].high
            j = next((k for k in range(ext_i, -1, -1) if _up(leg[k])), ext_i)
            lo = min(leg[j].open, leg[ext_i].open if _up(leg[ext_i]) else leg[ext_i].close)
            ob = {"kind": "bearish", "lo": min(lo, extreme), "hi": extreme}
        else:
            ext_i = min(range(len(leg)), key=lambda j: leg[j].low)
            extreme = leg[ext_i].low
            j = next((k for k in range(ext_i, -1, -1) if _down(leg[k])), ext_i)
            hi = max(leg[j].open, leg[ext_i].open if _down(leg[ext_i]) else leg[ext_i].close)
            ob = {"kind": "bullish", "lo": extreme, "hi": max(hi, extreme)}
        ob.update(tf=tf, extreme=extreme, leg_start=leg[0].start, extreme_at=leg[ext_i].start)
        self.blocks[(symbol, tf)] = ob
        return dict(ob)

    def latest(self, symbol: str, tf: str) -> Optional[dict]:
        ob = self.blocks.get((symbol, tf))
        return dict(ob) if ob else None


class DailyBiasBot(Bot):
    name = "daily_bias"
    skill = "Each morning: daily bias from the last daily break, plus the weekly and 4-hour trend"

    def setup(self) -> None:
        self.cache: dict[tuple[str, date], dict] = {}

    def bias(self, symbol: str, day: date) -> dict:
        key = (symbol, day)
        if key not in self.cache:
            htf = self.bot("htf_levels")
            past = [b for b in (htf.daily.get(symbol, []) if htf else []) if b.start.date() < day]
            weeks = aggregate(past, key=lambda b: b.start.date().isocalendar()[:2])
            ds = read_structure(past[-250:])
            rng = dealing_range(ds)
            self.cache[key] = {"D": ds.trend, "W": daily_structure(weeks[-120:]) if weeks else "unknown",
                               "days": len(past), "D_range": {k: round(v, 4) for k, v in rng.items()} if rng else None}
        out = dict(self.cache[key])
        ms = self.bot("market_structure")
        out["4h"] = ms.trend(symbol, "4h") if ms else "unknown"
        return out


class NewsCalendarBot(Bot):
    name = "news_calendar"
    skill = "Keep entries out on CPI, PPI, FOMC and jobs-report days, and right after other big releases"

    def setup(self) -> None:
        n = self.cfg.news
        self.days = {datetime.strptime(str(d), "%Y-%m-%d").date(): label for d, label in n.blackout_days.items()}
        self.events = [(datetime.strptime(str(t), "%Y-%m-%d %H:%M").replace(tzinfo=cal.ET), label)
                       for t, label in n.events.items()]
        self.derisk = {datetime.strptime(str(d), "%Y-%m-%d").date(): label for d, label in n.derisk_days.items()}

    def size_factor(self, day: date) -> tuple[float, str]:
        """Day 39: half size on high-impact news days that aren't blackouts, holiday eves, half days."""
        if not self.cfg.news.enabled:
            return 1.0, ""
        label = self.derisk.get(day) or ("half day" if cal.close_shift(day) < timedelta(0) else "")
        if not label:
            label = next((lb for at, lb in self.events if at.date() == day), "")
        return (0.5, label) if label else (1.0, "")

    def blocked(self, ts: datetime) -> Optional[str]:
        n = self.cfg.news
        if not n.enabled:
            return None
        label = self.days.get(ts.date())
        if label:
            return f"news day ({label}): no trades"
        for at, label in self.events:
            if at.date() == ts.date() and at - timedelta(minutes=5) <= ts < at + timedelta(minutes=n.wait_minutes):
                return f"{label} at {at:%H:%M}: waiting {n.wait_minutes} min for price to settle"
        return None

    def week(self, day: date) -> list[str]:
        start = day - timedelta(days=day.weekday())
        out = [f"{d:%a %m-%d} {label}" for d, label in sorted(self.days.items()) if start <= d < start + timedelta(days=7)]
        out += [f"{t:%a %m-%d %H:%M} {label}" for t, label in sorted(self.events) if start <= t.date() < start + timedelta(days=7)]
        return out


class SmartMoneyEntryBot(_ChartSignalBot):
    name = "sig_smc"
    skill = ("TJR entry: liquidity sweep, break of structure, retrace into an order block or gap in discount/premium, "
             "then a lower-timeframe break")
    trigger = "smc_retrace"

    def setup(self) -> None:
        super().setup()
        self.setups: dict[tuple[str, str], dict] = {}     # (symbol, setup timeframe) -> setup
        self.on(BreakOfStructure, self.on_break)
        self.on(CandleClosed, self.on_minute)
        self.on(SessionEvent, self.on_session)
        used = {t for w in self.cfg.workers if w.enabled for t in w.triggers}
        self.wanted = (used & SMC_TRIGGERS) or {"smc_retrace"}

    def on_session(self, e: SessionEvent) -> None:
        if e.kind is SessionKind.NEW_DAY:
            self.setups.clear()

    def on_break(self, e: BreakOfStructure) -> None:
        for (sym, tf), s in list(self.setups.items()):
            if sym == e.symbol and ENTRY_TF[tf] == e.tf:
                self.on_entry_break(e, s)
        if e.tf in self.cfg.smc.setup_timeframes:
            self.on_setup_break(e)

    # -- step 1: sweep then break on a setup timeframe
    def on_setup_break(self, e: BreakOfStructure) -> None:
        m = self.cfg.smc
        sym, key = e.symbol, (e.symbol, e.tf)
        st = self.bot("market_structure").get(sym, e.tf)
        swings = (st.lows if e.side is Side.PUT else st.highs) if st else []
        broken = next((i for i, p in reversed(swings) if p == e.level), None)
        if broken is None:
            return
        ob = self.bot("order_blocks").mark(sym, e.tf, e.side, broken)
        if ob is None:
            return
        kind = "high" if e.side is Side.PUT else "low"
        order = list(STRUCTURE_TFS)
        tfs = set(order[order.index(e.tf):]) | {"D"}      # liquidity worth the name: this timeframe or higher
        sweeps = self.bot("liquidity").swept(sym, kind, ob["leg_start"], e.candle.start, tfs)
        sweeps = [x for x in sweeps if (x["level"] <= ob["extreme"] if kind == "high" else x["level"] >= ob["extreme"])]
        if m.require_sweep and not sweeps:
            self.setups.pop(key, None)                # a break without a sweep: not the model (Days 12, 30)
            return
        atr = self.atr.get(sym)
        if not atr:
            return
        way = -1 if e.side is Side.PUT else 1
        stop = ob["extreme"] - way * m.stop_buffer_atr * atr
        rank = order + ["D"]
        best = max(sweeps, key=lambda x: rank.index(x["tf"])) if sweeps else None
        setup = {"side": e.side, "tf": e.tf, "extreme": ob["extreme"], "stop": stop, "ob": ob, "created": e.ts,
                 "range_end": e.candle.low if way < 0 else e.candle.high, "armed": None, "fired": False,
                 "sweep": {"tf": best["tf"], "level": best["level"]} if best else None,
                 "bos": {"tf": e.tf, "level": e.level}, "leg_start": ob["leg_start"]}
        self.setups[key] = setup
        if "smc_bos" in self.wanted:                  # model 1: enter on the break itself (riskiest, Day 30)
            self._fire("smc_bos", e.ts, e.candle, setup, e.level, e.backfill)

    # -- step 2: retrace into discount/premium and an order block or gap
    def on_minute(self, e: CandleClosed) -> None:
        c = e.candle
        for key in [k for k in self.setups if k[0] == c.symbol]:
            if self._track(self.setups[key], e):
                del self.setups[key]

    def _track(self, s: dict, e: CandleClosed) -> bool:
        """Update one setup with a closed minute; True when it is finished and should be dropped."""
        c = e.candle
        way = -1 if s["side"] is Side.PUT else 1
        if (way < 0 and c.close > s["extreme"]) or (way > 0 and c.close < s["extreme"]):
            return True                               # closed beyond the swept extreme: invalidated (Day 38)
        since = s["armed"]["at"] if s["armed"] else s["created"]
        if s["fired"] or e.ts - since > timedelta(minutes=self.cfg.smc.max_setup_minutes):
            return True                               # traded, or nothing happened in time
        if s["armed"]:
            return False
        if way < 0:
            s["range_end"] = min(s["range_end"], c.low)
            eq = (s["extreme"] + s["range_end"]) / 2
            if c.high < eq:
                return False                          # not in premium yet
            zone_lo, zone_hi = eq, c.high
        else:
            s["range_end"] = max(s["range_end"], c.high)
            eq = (s["extreme"] + s["range_end"]) / 2
            if c.low > eq:
                return False                          # not in discount yet
            zone_lo, zone_hi = c.low, eq
        hits = []
        ob = s["ob"]
        if ob["lo"] <= zone_hi and ob["hi"] >= zone_lo:
            hits.append(f"{ob['tf']} order block")
        kind = "bearish" if way < 0 else "bullish"
        for g in self.bot("imbalances").open_gaps(c.symbol, kind, s["leg_start"]):
            if g["bottom"] <= zone_hi and g["top"] >= zone_lo:
                hits.append(f"{g['tf']} fair value gap")
        if hits:
            s["armed"] = {"at": e.ts, "eq": round(eq, 4), "poi": sorted(set(hits))}
        return False

    # -- step 3: the break one timeframe lower, back in the trade's direction
    def on_entry_break(self, e: BreakOfStructure, s: dict) -> None:
        if not s["armed"] or s["fired"] or e.side is not s["side"] or e.ts < s["armed"]["at"]:
            return
        if "smc_retrace" in self.wanted:
            self._fire("smc_retrace", e.ts, e.candle, s, e.level, e.backfill)
        s["fired"] = True

    def _fire(self, trigger: str, ts, c: Candle, s: dict, level: float, backfill: bool) -> None:
        target, label = self.target(c.symbol, s["side"], c.close, s["stop"])
        info = {"model": trigger, "setup_tf": s["tf"], "entry_tf": ENTRY_TF[s["tf"]], "sweep": s["sweep"], "bos": s["bos"], "extreme": s["extreme"],
                "order_block": {k: s["ob"][k] for k in ("tf", "lo", "hi")}, "poi": (s["armed"] or {}).get("poi"),
                "equilibrium": (s["armed"] or {}).get("eq"), "target_label": label}
        self.emit(self._signal(trigger, ts, c, s["side"], level, backfill, s["stop"], target, info))

    def _signal(self, trigger, ts, c, side, level, backfill, stop, target, info) -> Signal:
        return Signal(ts, c.symbol, trigger, side, c.close, level, self.atr.get(c.symbol),
                      ema50=self.ema.get(c.symbol), vwap=self.vwap.get(c.symbol), backfill=backfill,
                      stop=stop, target=target, setup=info)

    def target(self, symbol: str, side: Side, entry: float, stop: float) -> tuple[Optional[float], str]:
        """Day 37: the first resting liquidity in the trade's direction at least min_rr away; if none is, the
        nearest one (the research gate then refuses the poor reward)."""
        risk = abs(entry - stop)
        kind = "high" if side is Side.CALL else "low"
        liq = self.bot("liquidity")
        pools = [(p, tf) for p, k, tf in liq.resting(symbol, self.cfg.smc.target_timeframes) + liq.resting_prior_day(symbol)
                 if k == kind and ((p > entry) if side is Side.CALL else (p < entry))]
        if not pools or risk <= 0:
            return None, "no resting liquidity ahead"
        pools.sort(key=lambda x: abs(x[0] - entry))
        for p, tf in pools:
            if abs(p - entry) >= self.cfg.smc.min_rr * risk:
                return p, f"{tf} {'highs' if kind == 'high' else 'lows'}"
        p, tf = pools[-1]
        return p, f"{tf} {'highs' if kind == 'high' else 'lows'}"
