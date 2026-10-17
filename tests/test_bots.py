"""Unit tests for individual bots, driven through a real bus."""
import asyncio
from datetime import date, datetime, timedelta

import pytest

from scalpcity.core import calendar as cal
from scalpcity.core.events import (Candle, CandleClosed, Fill, Heartbeat, IndicatorValue, KillSwitch, OptionContract,
                                   OptionQuote, OrderApproved, OrderIntent, OrderRejected, OrderSide, PositionOpened,
                                   Purpose, Side, Signal, SignalSkipped, TradeClosed, WorkerSignal, WorkerStatus)
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

D = date(2026, 10, 2)


def t(hhmm: str, sec: int = 0) -> datetime:
    return cal.at(D, hhmm) + timedelta(seconds=sec)


def system(cfg=None, mute=("health",)):
    """A full system with selected bots detached, so one bot can be tested in isolation."""
    o = Orchestrator(cfg or make_cfg(), db_path=":memory:", dashboard=False)
    for name in mute:
        o.bus.unsubscribe(name)
    return o


def collect(o, *types):
    out = []
    for ty in types:
        o.bus.subscribe(ty, out.append, "test")
    return out


def run(o, *events):
    async def go():
        for e in events:
            await o.bus.emit(e)
    asyncio.run(go())


def candle(sym, hhmm, o, h, l, c, v=1000):
    return Candle(sym, cal.at(D, hhmm), o, h, l, c, v)


# ---------------------------------------------------------------- indicators
def test_vwap_ema_atr_and_opening_range():
    o = system()
    vals = collect(o, IndicatorValue)
    bars = [candle("QQQ", f"09:{30 + i:02d}", 100 + i, 101 + i, 99 + i, 100.5 + i, 1000 * (i + 1)) for i in range(16)]
    run(o, *[CandleClosed(b.start + timedelta(minutes=1), b) for b in bars])
    vwap = [v for v in vals if v.name == "vwap"]
    pv = sum(b.typical * b.volume for b in bars)
    assert vwap[-1].value == pytest.approx(pv / sum(b.volume for b in bars))
    atr = [v for v in vals if v.name == "atr"]
    assert atr[12].ready is False and atr[13].ready is True
    rng = [v for v in vals if v.name == "opening_range"]
    locked = [v for v in rng if v.ready]
    assert locked[0].candle.start == cal.at(D, "09:44")          # locks with the 9:44 bar
    assert locked[0].value == 115 and locked[0].low == 99          # 9:30-9:44 high/low
    assert rng[-1].value == 115                                    # 9:45 bar not included


def test_ema_seeds_with_sma_then_smooths():
    o = system()
    vals = collect(o, IndicatorValue)
    closes = list(range(1, 52))
    run(o, *[CandleClosed(cal.at(D, "09:30"), Candle("QQQ", cal.at(D, "09:30") + timedelta(minutes=i), c, c, c, c, 1))
             for i, c in enumerate(closes)])
    ema = [v for v in vals if v.name == "ema50"]
    assert ema[49].ready and ema[49].value == pytest.approx(sum(range(1, 51)) / 50)
    assert ema[50].value == pytest.approx(51 * 2 / 51 + ema[49].value * (1 - 2 / 51))


# ---------------------------------------------------------------- signals
def _vwap_val(sym, hhmm, close, vwap, backfill=False):
    c = candle(sym, hhmm, close, close, close, close)
    return IndicatorValue(c.start + timedelta(minutes=1), "vwap", sym, vwap, c, backfill)


def test_vwap_cross_fires_call_above_and_put_below():
    o = system()
    sigs = collect(o, Signal)
    run(o, _vwap_val("QQQ", "10:00", 99.0, 100.0), _vwap_val("QQQ", "10:01", 100.5, 100.0),
        _vwap_val("QQQ", "10:02", 100.6, 100.1), _vwap_val("QQQ", "10:03", 99.8, 100.1))
    assert [(s.side, s.trigger) for s in sigs] == [(Side.CALL, "vwap_cross"), (Side.PUT, "vwap_cross")]


def test_backfill_signals_are_studied_never_traded():
    from scalpcity.core.events import WorkerSignal
    o = system()
    sigs = collect(o, Signal)
    routed = collect(o, WorkerSignal)
    run(o, _vwap_val("QQQ", "10:00", 99.0, 100.0), _vwap_val("QQQ", "10:01", 101.0, 100.0, backfill=True))
    assert len(sigs) == 1 and sigs[0].backfill          # history fires, marked as history
    assert routed == []                                 # ...and no worker ever trades it


def test_orb_breaks_once_per_side():
    o = system()
    sigs = collect(o, Signal)

    def orv(hhmm, close, ready=True):
        c = candle("QQQ", hhmm, close, close, close, close)
        return IndicatorValue(c.start, "opening_range", "QQQ", 105.0, c, low=95.0, ready=ready)

    run(o, orv("09:43", 100, False), orv("09:44", 100), orv("09:45", 104), orv("09:46", 106),
        orv("09:47", 104), orv("09:48", 107), orv("09:49", 94))
    assert [s.side for s in sigs] == [Side.CALL, Side.PUT]


# ---------------------------------------------------------------- filter
def _sig(hhmm, side=Side.CALL, sym="QQQ", close=100.5, level=100.0, atr=0.5):
    return Signal(cal.at(D, hhmm), sym, "vwap_cross", side, close, level, atr, ema50=99, vwap=100)


def test_filter_window_cooldown_and_busy():
    o = system(mute=("health", "contract_selector"))
    ws = collect(o, WorkerSignal)
    skipped = collect(o, SignalSkipped)
    contract = OptionContract("QQQ", D, 100, Side.CALL)
    run(o, _sig("09:32"))                                         # too early
    run(o, _sig("10:00"))                                         # accepted -> pending
    run(o, _sig("10:01"))                                         # pending
    run(o, PositionOpened(t("10:01"), "QQQ OG", contract, 2, 1.0, None), _sig("10:02"))  # in trade
    run(o, TradeClosed(t("10:03"), "QQQ OG", contract, 2, 1.0, 1.1, 20, "target", t("10:01")), _sig("10:04"))  # cooldown
    run(o, _sig("10:06", close=100.01))                          # weak close (0.02 ATR)
    run(o, _sig("10:07"))                                         # ok
    assert [w.ts for w in ws] == [t("10:00"), t("10:07")]
    reasons = [s.reason for s in skipped]
    assert reasons[0].startswith("outside trading window")
    assert reasons[1] == "order already working"
    assert reasons[2] == "already in a trade"
    assert reasons[3].startswith("cooling down")
    assert reasons[4].startswith("weak close")


def test_filter_respects_clock_out_and_trend_filter():
    cfg = make_cfg()
    cfg.workers[0].trend_filter = True
    o = system(cfg)
    ws = collect(o, WorkerSignal)
    skipped = collect(o, SignalSkipped)
    bad = Signal(t("10:00"), "QQQ", "vwap_cross", Side.CALL, 100.5, 100.0, 0.5, ema50=101.0, vwap=100.0)
    run(o, bad, WorkerStatus(t("10:05"), "QQQ OG", True, "daily goal"), _sig("10:06"))
    assert ws == [] and skipped[0].reason.startswith("against trend") and skipped[1].reason == "clocked out for the day"


# ---------------------------------------------------------------- selector / sizer
def _q(strike, bid, ask, right=Side.CALL, delta=None):
    return OptionQuote(t("10:00"), OptionContract("QQQ", D, strike, right), bid, ask, delta)


def test_contract_pick_modes():
    from scalpcity.bots.decision_bots import ContractSelectorBot as S
    chain = [_q(k, 1, 1.1, delta=d) for k, d in [(99, .7), (100, .52), (101, .35), (102, .2)]]
    assert S.pick(chain, "atm", Side.CALL, 100.2).contract.strike == 100
    assert S.pick(chain, "otm1", Side.CALL, 100.2).contract.strike == 101
    assert S.pick(chain, "itm1", Side.CALL, 100.2).contract.strike == 99
    assert S.pick(chain, "otm1", Side.PUT, 100.2).contract.strike == 99
    assert S.pick(chain, "delta:0.35", Side.CALL, 100.2).contract.strike == 101


@pytest.mark.parametrize("mode,expected", [("fixed", 3), ("budget", 5), ("risk", 6)])
def test_position_sizer(mode, expected):
    from scalpcity.core.config import Sizing
    from scalpcity.core.events import ContractSelected
    cfg = make_cfg()
    cfg.workers[0].sizing = Sizing(mode=mode, contracts=3, budget=2000, risk=200)
    o = system(cfg)
    intents = collect(o, OrderIntent)
    q = _q(100, 3.6, 3.68)
    run(o, ContractSelected(t("10:00"), "QQQ OG", _sig("10:00"), q))
    # budget: 2000 / 368 = 5 ; risk: 200 / (368 * 10%) = 5.4 -> 5 ... with stop 10% -> 5
    assert intents[0].qty == (expected if mode != "risk" else 5)
    assert intents[0].limit == 3.68 and intents[0].purpose is Purpose.ENTRY


# ---------------------------------------------------------------- risk
def _intent(purpose=Purpose.ENTRY, qty=2, limit=3.0, worker="QQQ OG"):
    side = OrderSide.BUY if purpose is Purpose.ENTRY else OrderSide.SELL
    return OrderIntent(t("10:00"), worker, OptionContract("QQQ", D, 100, Side.CALL), side, qty, limit, purpose, "x")


def _open_session(o):
    run(o, Heartbeat(t("09:29", 59)), Heartbeat(t("10:00")))


def test_risk_blocks_entries_but_never_exits():
    o = system(mute=("health", "execution"))  # don't trade, just check the decision
    approved = collect(o, OrderApproved)
    rejected = collect(o, OrderRejected)
    _open_session(o)
    run(o, KillSwitch(t("10:00"), True, "test"), _intent(), _intent(Purpose.EXIT))
    assert rejected[0].reason == "kill switch engaged"
    assert approved[0].intent.purpose is Purpose.EXIT


def test_risk_blocks_before_open_and_after_cutoff_and_on_size():
    o = system()
    rejected = collect(o, OrderRejected)
    run(o, _intent())
    run(o, Heartbeat(t("09:29", 59)), Heartbeat(t("15:31")), _intent())
    assert "market closed" in rejected[0].reason and "past entry cutoff" in rejected[1].reason
    o2 = system()
    rej2 = collect(o2, OrderRejected)
    _open_session(o2)
    run(o2, _intent(qty=100, limit=9.0))
    assert "premium exposure" in rej2[0].reason


def test_pdt_guard():
    o = system()
    rejected = collect(o, OrderRejected)
    _open_session(o)
    broker = o.ctx.broker
    broker.cash = 10_000
    broker.day_trades.extend([D, D, D])
    run(o, _intent())
    assert "pattern-day-trader" in rejected[0].reason


# ---------------------------------------------------------------- exits
def _setup_position(o, entry=2.0):
    c = OptionContract("QQQ", D, 100, Side.CALL)
    run(o, PositionOpened(t("10:00"), "QQQ OG", c, 2, entry, None))
    return c


@pytest.mark.parametrize("bids,reason", [
    ([1.79], "stop"),                     # -10.5%
    ([2.25], "target"),                   # +12.5%
    ([2.10, 2.04], "profit_lock"),        # peak +5%, back to +2% (< 60% of 5%)
])
def test_exit_rules(bids, reason):
    o = system(mute=("health", "risk_manager"))
    intents = collect(o, OrderIntent)
    c = _setup_position(o)
    run(o, *[OptionQuote(t("10:01", i), c, b, b + 0.02) for i, b in enumerate(bids)])
    assert [i.reason for i in intents] == [reason]
    assert intents[0].side is OrderSide.SELL and intents[0].purpose is Purpose.EXIT


def test_time_stop_reversal_and_end_of_day():
    o = system(mute=("health", "risk_manager"))
    intents = collect(o, OrderIntent)
    c = _setup_position(o)
    run(o, OptionQuote(t("10:01"), c, 2.0, 2.02), Heartbeat(t("10:21")))
    assert intents[-1].reason == "time"
    o2 = system(mute=("health", "risk_manager"))
    i2 = collect(o2, OrderIntent)
    _setup_position(o2)
    run(o2, _sig("10:02", side=Side.PUT))
    assert i2[-1].reason == "reversal"
    o3 = system(mute=("health", "risk_manager"))
    i3 = collect(o3, OrderIntent)
    _setup_position(o3)
    run(o3, Heartbeat(t("09:29", 59)), Heartbeat(t("15:55")))
    assert i3[-1].reason == "end_of_day"


# ---------------------------------------------------------------- ledger / goals
def test_ledger_pnl_includes_fees_both_sides():
    o = system()
    closed = collect(o, TradeClosed)
    buy = _intent(qty=10)
    sell = _intent(Purpose.EXIT, qty=10)
    run(o, Fill(t("10:00"), buy, 10, 3.00, 0.30, "a"), Fill(t("10:05"), sell, 10, 3.25, 0.30, "b"))
    assert closed[0].pnl == pytest.approx(0.25 * 10 * 100 - 0.60)
    assert o.ctx.bots["ledger"].holdings() == {}


def test_daily_goal_clock_out_and_kill_switch():
    cfg = make_cfg()
    cfg.workers[0].daily_goal = 100
    cfg.risk.max_daily_loss = 150
    o = system(cfg)
    status = collect(o, WorkerStatus)
    kills = collect(o, KillSwitch)
    c = OptionContract("QQQ", D, 100, Side.CALL)
    run(o, TradeClosed(t("10:00"), "QQQ OG", c, 1, 1, 2, 120, "target", t("09:50")))
    assert status[-1].clocked_out and status[-1].reason == "daily goal"
    run(o, TradeClosed(t("10:10"), "SPY", c, 1, 1, 2, -300, "stop", t("10:00")))
    assert kills[-1].engaged


def test_health_gives_silent_symbols_a_grace_period_after_start():
    import asyncio as _asyncio
    from datetime import date as _date, timedelta as _td

    from scalpcity.core import calendar as _cal
    from scalpcity.core.events import HealthStatus, Heartbeat, SessionKind, Tick
    from scalpcity.orchestrator import Orchestrator
    from tests.conftest import make_cfg as _make_cfg

    o = Orchestrator(_make_cfg(), db_path=":memory:", dashboard=False)
    o.ctx.bots["clock"].done = {SessionKind.OPEN}
    seen = []
    o.bus.subscribe(HealthStatus, seen.append, "t")
    t0 = _cal.at(_date(2026, 10, 15), "11:00")

    async def go():
        await o.bus.emit(Heartbeat(t0))                       # started mid-session, nothing heard yet
        await o.bus.emit(Tick(t0 + _td(seconds=5), "QQQ", 1.0))
        await o.bus.emit(Heartbeat(t0 + _td(seconds=20)))     # SPY silent 20 s: still within grace
        assert seen == []
        await o.bus.emit(Heartbeat(t0 + _td(seconds=31)))     # SPY silent past the limit
    _asyncio.run(go())
    assert len(seen) == 1 and not seen[0].ok and "SPY" in seen[0].reason and "QQQ" not in seen[0].reason
