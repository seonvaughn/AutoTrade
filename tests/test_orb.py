"""15-minute opening range (docs/videos/15m-opening-range.md): range, 5m close beyond it, 1m entries."""
import asyncio
from datetime import date, timedelta

from scalpcity.core import calendar as cal
from scalpcity.core.config import WorkerConfig
from scalpcity.core.events import Candle, CandleClosed, Side, Signal
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

D = date(2026, 10, 15)


def system(triggers):
    cfg = make_cfg(workers=[WorkerConfig(name="QQQ OG", symbol="QQQ", triggers=list(triggers),
                                         daily_goal=10_000, max_daily_loss=10_000)])
    return Orchestrator(cfg, db_path=":memory:", dashboard=False)


def run(o, path):
    """path: list of (open, high, low, close) one-minute candles from 09:30."""
    sigs = []
    o.bus.subscribe(Signal, sigs.append, "t")
    t0 = cal.at(D, "09:30")

    async def go():
        for i, (op, hi, lo, cl) in enumerate(path):
            c = Candle("QQQ", t0 + timedelta(minutes=i), op, hi, lo, cl, 100)
            await o.bus.emit(CandleClosed(c.start + timedelta(minutes=1), c))
    asyncio.run(go())
    return [s for s in sigs if s.trigger.startswith("orb15")]


def flat(p, n, wiggle=0.2):
    return [(p, p + wiggle, p - wiggle, p + (wiggle / 2 if i % 2 else -wiggle / 2)) for i in range(n)]


RANGE = [(100, 100.5, 99.5, 100.2)] + flat(100, 14, 0.3)                # 09:30-09:44: range 99.5-100.5


def test_breakout_needs_a_5m_close_beyond_the_range_then_a_1m_gap():
    o = system(["orb15_breakout"])
    path = RANGE + flat(100.2, 5, 0.1)                                   # 09:45-09:49: inside
    path += [(100.2, 100.6, 100.1, 100.4)] * 4 + [(100.4, 100.8, 100.3, 100.7)]  # 5m bar closes 100.7 > 100.5
    path += [(100.7, 100.8, 100.6, 100.75), (100.75, 101.4, 100.74, 101.3), (101.3, 101.6, 101.0, 101.5)]
    sigs = run(o, path)
    assert len(sigs) == 1
    s = sigs[0]
    assert s.trigger == "orb15_breakout" and s.side is Side.CALL
    assert s.stop == 100.74 and abs(s.target - (101.5 + 2 * (101.5 - 100.74))) < 1e-9   # below the gap's middle, 1:2


def test_no_signal_without_the_5m_close():
    o = system(["orb15_breakout", "orb15_retest", "orb15_reversal"])
    path = RANGE + flat(100.2, 20, 0.2)                                  # never closes a 5m bar beyond 100.5
    assert run(o, path) == []


def test_retest_holds_the_edge_then_breaks_structure():
    o = system(["orb15_retest"])
    path = RANGE + flat(100.2, 5, 0.1)
    path += [(100.2, 100.6, 100.1, 100.4)] * 4 + [(100.4, 100.8, 100.3, 100.7)]   # 5m close above the range
    path += [(100.7, 100.9, 100.6, 100.85), (100.85, 100.9, 100.6, 100.65),       # up, down: a 1m high at 100.9
             (100.65, 100.7, 100.45, 100.6),                                       # touches 100.5, closes above
             (100.6, 100.8, 100.55, 100.75),                                       # down then up: a 1m low
             (100.75, 101.1, 100.7, 101.0)]                                        # closes above 100.9: the break
    sigs = run(o, path)
    assert [s.trigger for s in sigs] == ["orb15_retest"]
    s = sigs[0]
    assert s.side is Side.CALL and s.stop < 100.45 and s.target > s.close
