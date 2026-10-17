"""Research bots: key levels from past sessions, trigger edge scoring, and the evidence gate."""
import asyncio
from datetime import date, timedelta

from scalpcity.core import calendar as cal
from scalpcity.core.events import (Candle, CandleClosed, EntryVetoed, KeyLevels, PositionOpened, ResearchCleared,
                                   Side, Signal, WorkerSignal)
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg
from tests.test_system import DAYS

D1, D2, D3 = date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15)


def system(enabled=True, **research):
    cfg = make_cfg()
    cfg.research.enabled = enabled
    for k, v in research.items():
        setattr(cfg.research, k, v)
    return Orchestrator(cfg, db_path=":memory:", dashboard=False)


def bar(d, hhmm, o, h, low, c, sym="QQQ"):
    return Candle(sym, cal.at(d, hhmm), o, h, low, c, 1000)


def feed(o, candles, backfill=True):
    async def go():
        for c in candles:
            await o.bus.emit(CandleClosed(c.start + timedelta(minutes=1), c, backfill=backfill))
    asyncio.run(go())


def collect(o, ty):
    out = []
    o.bus.subscribe(ty, out.append, "t")
    return out


# ---------------------------------------------------------------- key levels
def test_key_levels_from_past_sessions():
    o = system()
    feed(o, [bar(D1, "09:30", 100, 104, 99, 103), bar(D1, "15:59", 103, 103.5, 101, 102),
             bar(D2, "09:30", 102, 106, 101, 105), bar(D2, "15:59", 105, 105, 97.5, 98)])
    levels = {lv.label: lv.price for lv in o.ctx.bots["key_levels"].levels("QQQ", D3)}
    assert levels["prior day high · 2-day high"] == 106          # same price: one level, both reasons
    assert levels["prior day low · 2-day low"] == 97.5 and levels["prior day close"] == 98
    assert o.ctx.bots["key_levels"].levels("QQQ", D1) == []          # nothing before the first day


def test_turning_points_found_twice_become_a_level():
    o = system()
    candles = []
    for d in (D1, D2):  # each day: a 15-min swing high near 110 between lower bars
        for hhmm, hi in (("09:30", 105), ("09:45", 110), ("10:00", 106)):
            candles.append(bar(d, hhmm, 104, hi, 103, 104))
    feed(o, candles)
    levels = o.ctx.bots["key_levels"].levels("QQQ", D3)
    tp = [lv for lv in levels if "turning point ×2" in lv.label]
    assert tp and tp[0].strength == 2 and abs(tp[0].price - 110) < 0.01


def test_levels_published_once_on_first_live_candle():
    o = system()
    out = collect(o, KeyLevels)
    feed(o, [bar(D2, "10:00", 100, 101, 99, 100)])
    feed(o, [bar(D3, "09:30", 100, 101, 99, 100), bar(D3, "09:31", 100, 101, 99, 100)], backfill=False)
    assert len(out) == 1 and out[0].day == D3 and out[0].levels


# ---------------------------------------------------------------- edge tracker
def _sig(d, hhmm, side=Side.CALL, close=100.0, atr=1.0, trigger="vwap_cross", backfill=True):
    return Signal(cal.at(d, hhmm), "QQQ", trigger, side, close, 100.0, atr, backfill=backfill)


def score(o, signal, candles):
    async def go():
        await o.bus.emit(signal)
        for c in candles:
            await o.bus.emit(CandleClosed(c.start + timedelta(minutes=1), c, backfill=True))
    asyncio.run(go())
    rows = o.ctx.bots["edge_tracker"].results[("QQQ", "vwap_cross")]
    return rows[-1][2:]


def test_edge_outcomes():
    # target +1.0 ATR, stop -0.7 ATR (defaults); ATR 1.0, entry 100
    assert score(system(), _sig(D1, "10:00"), [bar(D1, "10:01", 100, 101.2, 99.8, 101)]) == ("win", round(1 / 0.7, 3))
    assert score(system(), _sig(D1, "10:00"), [bar(D1, "10:01", 100, 100.2, 99.2, 99.5)]) == ("loss", -1.0)
    assert score(system(), _sig(D1, "10:00"), [bar(D1, "10:01", 100, 101.5, 99.0, 100)]) == ("loss", -1.0)  # both: worst
    put = _sig(D1, "10:00", side=Side.PUT)
    assert score(system(), put, [bar(D1, "10:01", 100, 100.1, 98.9, 99)]) == ("win", round(1 / 0.7, 3))
    o = system(horizon_minutes=2)   # window ends when the 10:01 candle closes at 10:02
    assert score(o, _sig(D1, "10:00"), [bar(D1, "10:01", 100, 100.3, 99.9, 100.2)]) == ("timeout", round(0.2 / 0.7, 3))
    o = system()
    assert score(o, _sig(D1, "15:58"), [bar(D2, "09:30", 100, 100, 100, 100)])[0] == "timeout"   # day ended


def test_edge_stats_window_and_proof():
    o = system(min_samples=3)
    et = o.ctx.bots["edge_tracker"]
    et.results[("QQQ", "vwap_cross")] = [(date(2026, 9, 1), "CALL", "win", 1.4)] * 5 + \
        [(D1, "CALL", "win", 1.4), (D2, "CALL", "loss", -1.0), (D2, "PUT", "win", 1.4)]
    st = et.stats("QQQ", "vwap_cross", D3)
    assert st["n"] == 3 and st["wins"] == 2 and st["losses"] == 1    # September is outside the 5-session window
    assert st["proven"] and abs(st["avg_r"] - (1.4 - 1.0 + 1.4) / 3) < 1e-3


# ---------------------------------------------------------------- gate
def gate(o, sig):
    ok = collect(o, ResearchCleared)
    vetoes = collect(o, EntryVetoed)
    asyncio.run(o.bus.emit(WorkerSignal(sig.ts, "QQQ OG", sig)))
    return ok, vetoes


def test_gate_vetoes_unproven_trigger():
    o = system()
    ok, vetoes = gate(o, _sig(D3, "10:00", backfill=False))
    assert not ok and "not proven" in vetoes[0].reason


def test_gate_vetoes_trigger_without_edge():
    o = system(min_samples=2)
    o.ctx.bots["edge_tracker"].results[("QQQ", "vwap_cross")] = [(D2, "CALL", "loss", -1.0)] * 4
    ok, vetoes = gate(o, _sig(D3, "10:00", backfill=False))
    assert not ok and vetoes[0].reason.startswith("no edge") and "0/4" in vetoes[0].reason


def test_gate_vetoes_when_a_level_is_too_close_and_clears_with_room():
    o = system(min_samples=2)
    o.ctx.bots["edge_tracker"].results[("QQQ", "vwap_cross")] = [(D2, "CALL", "win", 1.4)] * 4
    feed(o, [bar(D2, "10:00", 100, 100.4, 99, 100)])                 # prior day high 100.4
    ok, vetoes = gate(o, _sig(D3, "10:00", close=100.0, atr=1.0, backfill=False))
    assert not ok and "prior day high" in vetoes[0].reason and "0.4 ATR" in vetoes[0].reason
    ok, vetoes = gate(o, _sig(D3, "10:01", side=Side.PUT, close=100.0, atr=0.5, backfill=False))
    assert vetoes == [] and ok and ok[0].evidence["next_level"]["label"] == "prior day low"  # 99 is 2 ATR below


def test_gate_off_passes_through():
    o = system(enabled=False)
    ok, vetoes = gate(o, _sig(D3, "10:00", backfill=False))
    assert ok and ok[0].evidence == {"gate": "off"} and not vetoes


# ---------------------------------------------------------------- whole system
def test_every_trade_has_cleared_research_first():
    o = system(min_samples=3)
    cleared, opened, vetoed = collect(o, ResearchCleared), collect(o, PositionOpened), collect(o, EntryVetoed)
    report = asyncio.run(o.replay(DAYS[:3]))
    assert vetoed, "with fake prices most triggers should fail the evidence check"
    cleared_keys = {(c.worker, c.signal.ts) for c in cleared}
    for p in opened:
        assert (p.worker, p.signal.ts) in cleared_keys          # nothing trades without evidence
    assert o.ctx.bots["ledger"].holdings() == {}
    assert any(k.startswith("research") for k in report["blocked_entries"])


def test_history_is_scored_in_order_not_as_empty_timeouts():
    # regression: history was queued all at once, so past signals only saw candles from later days
    o = system()
    asyncio.run(o.replay(DAYS[-1:]))           # 5 warm-up sessions of history, then one day
    rows = [r for rs in o.ctx.bots["edge_tracker"].results.values() for r in rs]
    assert len(rows) > 20
    decided = [r for r in rows if r[2] in ("win", "loss")]
    assert len(decided) > len(rows) / 2         # most past signals reach target or stop within 20 min


def test_backtest_never_buys_at_a_stale_option_price():
    # regression: the last option trade was used as-is, so a signal fired after a stock move could
    # "buy" at the price from before the move (a fake +$41k backtest). It must be moved by delta.
    from scalpcity.core.events import Candle as C, OptionContract
    o = system(enabled=False)
    sim = o.ctx.bots["options_chain"].sim
    contract = OptionContract("QQQ", D3, 100.0, Side.CALL)

    class Bars:  # one trade at 10:00 for 2.00, nothing since
        def last_bar(self, c, ts):
            return C(c.occ, cal.at(D3, "10:00"), 2.0, 2.0, 2.0, 2.0, 1)
    sim.hist = Bars()
    sim.on_spot("QQQ", cal.at(D3, "10:00") + timedelta(seconds=50), 100.0)   # stock when the option traded
    sim.on_spot("QQQ", cal.at(D3, "10:07"), 101.0)                            # stock now, $1 higher
    call = sim.quote(contract, cal.at(D3, "10:07"))
    put = sim.quote(OptionContract("QQQ", D3, 100.0, Side.PUT), cal.at(D3, "10:07"))
    assert call.mid > 2.4                    # ~2.00 + ~0.6 delta * $1, not the stale 2.00
    assert put.mid < 1.9                     # puts move the other way (delta about -0.17 here)
