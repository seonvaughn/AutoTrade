"""Chart-reading bots: timeframes, higher-timeframe study, structure, zones, and their triggers."""
import asyncio
from datetime import date, datetime, timedelta

from scalpcity.bots.chart_bots import aggregate, find_swings, latest_leg, trend_of
from scalpcity.core import calendar as cal
from scalpcity.core.events import (BarClosed, Candle, CandleClosed, EntryVetoed, Heartbeat, ResearchCleared, Side,
                                   Signal, StructureBreak, Tick, WorkerSignal)
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

D = date(2026, 10, 15)


LEGACY_TRIGGERS = ["vwap_cross", "ema50_cross", "orb", "zone_reaction", "structure_break", "fib_pullback"]


def system(research=False):
    cfg = make_cfg()
    for w in cfg.workers:                  # the chart bots are only built for towers that trade their triggers
        w.triggers = list(LEGACY_TRIGGERS)
    cfg.research.enabled = research
    return Orchestrator(cfg, db_path=":memory:", dashboard=False)


def c(t, o, h, low, cl, sym="QQQ"):
    return Candle(sym, t, o, h, low, cl, 100)


def emit(o, *events):
    async def go():
        for e in events:
            await o.bus.emit(e)
    asyncio.run(go())


def collect(o, ty):
    out = []
    o.bus.subscribe(ty, out.append, "t")
    return out


def zigzag(points, t0=None):
    """Candles whose highs/lows follow the given turning points (one candle per point)."""
    t0 = t0 or cal.at(D, "09:30")
    return [c(t0 + timedelta(minutes=5 * i), p, p + 0.2, p - 0.2, p) for i, p in enumerate(points)]


# ---------------------------------------------------------------- pure chart reading
def test_trend_from_swings():
    up = zigzag([100, 101, 102, 101, 100.5, 101.5, 103, 104, 102.5, 101.8, 102.6, 104.5, 105, 104, 103])
    assert trend_of(find_swings(up)) == "bullish"
    down = zigzag([105, 104, 103, 104, 104.5, 103.5, 102, 101, 102.5, 103.2, 102.4, 100.5, 100, 101, 102])
    assert trend_of(find_swings(down)) == "bearish"
    assert trend_of(find_swings(zigzag([100, 100, 100]))) == "unknown"


def test_fibonacci_levels_of_latest_leg():
    bars = zigzag([100, 101, 102, 101, 100.5, 101.5, 103, 104, 102.5, 101.8, 102.6, 104.5, 105, 104, 103])
    sw = find_swings(bars)
    leg = latest_leg(bars, sw, "bullish")
    lo, hi = leg["from"], leg["to"]
    assert leg["direction"] == "up" and hi == max(b.high for b in bars)
    assert abs(leg["levels"][0.5] - (hi - 0.5 * (hi - lo))) < 1e-6
    assert leg["levels"][0.786] < leg["levels"][0.618] < leg["levels"][0.5] < leg["levels"][0.382]


def test_aggregate_by_week():
    days = [date(2026, 10, 5) + timedelta(days=i) for i in range(10) if (date(2026, 10, 5) + timedelta(days=i)).weekday() < 5]
    daily = [c(datetime.combine(d, datetime.min.time(), cal.ET), 100 + i, 101 + i, 99 + i, 100.5 + i)
             for i, d in enumerate(days)]
    weeks = aggregate(daily, key=lambda b: b.start.date().isocalendar()[:2])
    assert len(weeks) == 2 and weeks[0].open == 100 and weeks[0].high == 105 and weeks[1].close == 107.5


# ---------------------------------------------------------------- timeframes
def test_minute_candles_build_5m_and_15m():
    o = system()
    bars = collect(o, BarClosed)
    mins = [CandleClosed(cal.at(D, "09:30") + timedelta(minutes=i + 1),
                         c(cal.at(D, "09:30") + timedelta(minutes=i), 100 + i, 100.5 + i, 99.5 + i, 100.2 + i))
            for i in range(15)]
    emit(o, *mins)
    five = [b for b in bars if b.tf == "5m"]
    fifteen = [b for b in bars if b.tf == "15m"]
    assert [b.candle.start for b in five] == [cal.at(D, t) for t in ("09:30", "09:35", "09:40")]
    assert (five[0].candle.open, five[0].candle.high, five[0].candle.low, five[0].candle.close) == (100, 104.5, 99.5, 104.2)
    assert len(fifteen) == 1 and fifteen[0].candle.close == 114.2


def test_30s_candles_from_ticks_and_from_history():
    o = system()
    bars = collect(o, BarClosed)
    t0 = cal.at(D, "10:00")
    emit(o, Tick(t0 + timedelta(seconds=1), "QQQ", 100), Tick(t0 + timedelta(seconds=20), "QQQ", 101),
         Tick(t0 + timedelta(seconds=31), "QQQ", 100.5), Heartbeat(t0 + timedelta(seconds=60)))
    halves = [b.candle for b in bars if b.tf == "30s"]
    assert [(h.start, h.open, h.high, h.close) for h in halves] == [(t0, 100, 101, 101),
                                                                     (t0 + timedelta(seconds=30), 100.5, 100.5, 100.5)]
    bars.clear()
    emit(o, CandleClosed(t0 + timedelta(minutes=2), c(t0 + timedelta(minutes=1), 100, 102, 99, 101), backfill=True))
    hist = [b for b in bars if b.tf == "30s"]
    assert len(hist) == 2 and all(b.backfill for b in hist) and hist[0].candle.open == 100 and hist[1].candle.close == 101


# ---------------------------------------------------------------- higher timeframes (no look-ahead)
def test_htf_study_uses_only_past_days():
    o = system()
    htf = o.ctx.bots["htf_levels"]
    days = [d for d in (date(2025, 10, 1) + timedelta(days=i) for i in range(380)) if d.weekday() < 5]
    htf.daily["QQQ"] = [c(datetime.combine(d, datetime.min.time(), cal.ET), 100, 100 + i * 0.01, 99, 100)
                        for i, d in enumerate(days)]
    s = htf.study("QQQ", D)
    lv = {x.label: x.price for x in s["levels"]}
    before = [b for b in htf.daily["QQQ"] if b.start.date() < D]
    assert lv["52-week high"] == max(b.high for b in before if b.start.date() >= D - timedelta(days=365))
    assert lv["52-week high"] < max(b.high for b in htf.daily["QQQ"])            # later days never leak in
    week = [b for b in before if b.start.date().isocalendar()[:2] == date(2026, 10, 8).isocalendar()[:2]]
    assert lv["prior week high"] == max(b.high for b in week)
    assert set(s["trend"]) == {"D", "W"}


# ---------------------------------------------------------------- structure + zones
def test_structure_break_on_close_beyond_swing_high():
    o = system()
    breaks = collect(o, StructureBreak)
    bars = zigzag([100, 101, 103, 101, 100.5, 101.6, 102.5, 103.5])
    emit(o, *[BarClosed(b.start + timedelta(minutes=5), "5m", b) for b in bars])
    assert len(breaks) == 1 and breaks[0].side is Side.CALL and abs(breaks[0].level - 103.2) < 1e-6


def _make_demand_zone(o, sym="QQQ"):
    t0 = cal.at(D, "09:30")
    bars = [c(t0, 100, 100.5, 99.5, 100.1, sym),                                    # normal candle (seeds ATR = 1)
            c(t0 + timedelta(minutes=15), 100, 100.3, 99.8, 100.05, sym),           # quiet base
            c(t0 + timedelta(minutes=30), 100.1, 102.6, 100.0, 102.5, sym)]         # impulse up: range 2.6 >= 2 ATR
    emit(o, *[BarClosed(b.start + timedelta(minutes=15), "15m", b) for b in bars])


def test_demand_zone_found_touched_and_broken():
    o = system()
    _make_demand_zone(o)
    z = o.ctx.bots["zones"].zones("QQQ")
    assert len(z) == 1 and z[0]["kind"] == "demand" and (z[0]["lo"], z[0]["hi"]) == (99.8, 100.3)
    t = cal.at(D, "11:00")
    emit(o, CandleClosed(t + timedelta(minutes=1), c(t, 100.6, 100.7, 100.2, 100.5)))     # dips into the zone
    assert o.ctx.bots["zones"].zones("QQQ")[0]["touches"] == 1
    emit(o, CandleClosed(t + timedelta(minutes=2), c(t + timedelta(minutes=1), 100.0, 100.1, 99.5, 99.6)))
    assert o.ctx.bots["zones"].zones("QQQ") == []                                         # closed through it


# ---------------------------------------------------------------- new triggers
def test_zone_reaction_fires_once_on_strong_30s_close():
    o = system()
    sigs = collect(o, Signal)
    _make_demand_zone(o)
    t = cal.at(D, "11:00")
    h1 = c(t, 100.4, 100.45, 100.2, 100.25)          # dips into the zone (hi 100.3)
    h2 = c(t + timedelta(seconds=30), 100.25, 100.6, 100.25, 100.55)   # closes up, above the prior high
    emit(o, BarClosed(t + timedelta(seconds=30), "30s", h1), BarClosed(t + timedelta(seconds=60), "30s", h2))
    h3 = c(t + timedelta(seconds=60), 100.3, 100.9, 100.28, 100.8)
    emit(o, BarClosed(t + timedelta(seconds=90), "30s", h3))
    zr = [s for s in sigs if s.trigger == "zone_reaction"]
    assert [(s.side, s.level) for s in zr] == [(Side.CALL, 100.3)]                  # once per zone per day


def test_structure_break_and_fib_pullback_triggers():
    o = system()
    sigs = collect(o, Signal)
    t = cal.at(D, "11:00")
    emit(o, StructureBreak(t, "QQQ", "5m", Side.PUT, 99.0, c(t, 99.2, 99.3, 98.7, 98.8)),
         StructureBreak(t, "QQQ", "15m", Side.PUT, 99.0, c(t, 99.2, 99.3, 98.7, 98.8)))   # only 5m trades
    assert [(s.trigger, s.side) for s in sigs] == [("structure_break", Side.PUT)]
    st = o.ctx.bots["structure"]
    st.fib = lambda sym, tf: {"direction": "up", "from": 100, "to": 110, "id": (1, 100),
                              "levels": {0.382: 106.18, 0.5: 105.0, 0.618: 103.82, 0.786: 102.14}}
    emit(o, CandleClosed(t + timedelta(minutes=1), c(t, 104.6, 104.8, 104.4, 104.5)),
         CandleClosed(t + timedelta(minutes=2), c(t + timedelta(minutes=1), 104.5, 105.2, 104.3, 105.1)))
    fib = [s for s in sigs if s.trigger == "fib_pullback"]
    assert len(fib) == 1 and fib[0].side is Side.CALL and fib[0].level == 103.82


# ---------------------------------------------------------------- research gate: timeframes and zones
def _proven(o, trigger="vwap_cross"):
    o.ctx.bots["edge_tracker"].results[("QQQ", trigger)] = [(date(2026, 10, 14), "CALL", "win", 1.4)] * 8


def gate(o, side=Side.CALL, close=100.0):
    ok, vetoes = collect(o, ResearchCleared), collect(o, EntryVetoed)
    sig = Signal(cal.at(D, "11:30"), "QQQ", "vwap_cross", side, close, 99.9, 0.5)
    emit(o, WorkerSignal(sig.ts, "QQQ OG", sig))
    return ok, vetoes


def test_gate_refuses_trades_against_the_bigger_trend():
    o = system(research=True)
    _proven(o)
    o.ctx.bots["structure"].read[("QQQ", "1h")] = ([], "bearish")
    ok, vetoes = gate(o)
    assert not ok and "against the 1h trend (bearish)" in vetoes[0].reason
    o.ctx.bots["structure"].read[("QQQ", "1h")] = ([], "range")                    # range doesn't block
    ok, vetoes = gate(o)
    assert ok and ok[0].evidence["trend"]["1h"] == "range"


def test_gate_treats_opposing_zones_as_obstacles():
    o = system(research=True)
    _proven(o)
    o.ctx.bots["zones"].active["QQQ"] = [{"kind": "supply", "tf": "1h", "lo": 100.2, "hi": 100.6, "id": "z",
                                          "touches": 0, "inside": False, "since": ""}]
    ok, vetoes = gate(o, close=100.0)
    assert not ok and "1h supply zone" in vetoes[0].reason                         # 0.4 ATR away
    ok, vetoes = gate(o, close=100.4)
    assert not ok and vetoes[0].reason.startswith("inside a 1h supply zone")
