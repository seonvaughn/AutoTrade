"""TJR's model (docs/tjr-bootcamp): structure, liquidity, gaps, order blocks, the entry, and the gate's rules."""
import asyncio
from datetime import date, datetime, timedelta

from scalpcity.bots.smc_bots import Structure, daily_structure, find_gaps
from scalpcity.core import calendar as cal
from scalpcity.core.config import WorkerConfig
from scalpcity.core.events import (BreakOfStructure, Candle, CandleClosed, EntryVetoed, Heartbeat, LiquiditySweep,
                                   MorningPlan, SessionEvent, SessionKind,
                                   ResearchCleared, Side, Signal, SignalSkipped, WorkerSignal)
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

D = date(2026, 10, 15)


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


def system(triggers=("smc_retrace",), research=False):
    cfg = make_cfg(workers=[WorkerConfig(name="QQQ OG", symbol="QQQ", triggers=list(triggers),
                                         daily_goal=10_000, max_daily_loss=10_000)])
    cfg.research.enabled = research
    return Orchestrator(cfg, db_path=":memory:", dashboard=False)


# ---------------------------------------------------------------- pure rules (Day 6, Day 16)
def seq(bars, t0=None, step=5):
    t0 = t0 or cal.at(D, "09:30")
    return [c(t0 + timedelta(minutes=step * i), *b) for i, b in enumerate(bars)]


def test_two_candle_highs_and_lows():
    s = Structure()
    for b in seq([(100, 101, 99.8, 100.8), (100.8, 101.5, 100.6, 101.2),    # up, up
                  (101.2, 101.3, 100.5, 100.7),                              # down -> a high at 101.5
                  (100.7, 100.9, 100.2, 100.4), (100.4, 101.0, 100.3, 100.9)]):  # down, up -> a low at 100.2
        s.update(b)
    assert s.last_high == 101.5 and s.last_low == 100.2


def test_a_wick_is_not_a_break_only_a_body_close_is():
    s = Structure()
    for b in seq([(100, 101, 99.8, 100.8), (100.8, 101.5, 100.6, 101.2), (101.2, 101.3, 100.5, 100.7)]):
        s.update(b)
    assert s.update(seq([(100.7, 101.9, 100.6, 101.4)], cal.at(D, "09:45"))[0]) == []   # wick above 101.5, close below
    out = s.update(seq([(101.4, 101.8, 101.3, 101.6)], cal.at(D, "09:50"))[0])          # close above 101.5
    assert out and out[0][1] is Side.CALL and out[0][2] == 101.5 and s.trend == "bullish"
    assert s.update(seq([(101.6, 101.9, 101.5, 101.7)], cal.at(D, "09:55"))[0]) == []   # the same high breaks once


def test_only_the_most_recent_low_counts():
    s = Structure()
    for b in seq([(100, 100.2, 99.0, 99.2), (99.2, 99.9, 99.1, 99.8),       # down, up -> low 99.0
                  (99.8, 100.4, 99.7, 100.3), (100.3, 100.35, 99.6, 99.7),  # up, down -> high 100.4
                  (99.7, 99.8, 99.4, 99.5), (99.5, 100.0, 99.45, 99.9)]):   # down, up -> low 99.4 (most recent)
        s.update(b)
    out = s.update(seq([(99.9, 99.95, 99.2, 99.3)], cal.at(D, "10:00"))[0])  # below 99.4, above the older 99.0
    assert out and out[0][1] is Side.PUT and out[0][2] == 99.4


def test_fair_value_gaps():
    t = cal.at(D, "10:00")
    c1, c2, c3 = c(t, 100, 100.5, 99.8, 100.4), c(t, 100.4, 101.6, 100.3, 101.5), c(t, 101.5, 101.9, 100.9, 101.8)
    assert find_gaps(c1, c2, c3) == {"kind": "bullish", "lo": 100.5, "hi": 100.9}
    c3_overlap = c(t, 101.5, 101.9, 100.4, 101.8)              # its wick reaches back into candle 1: no gap
    assert find_gaps(c1, c2, c3_overlap) is None
    d1, d2, d3 = c(t, 101, 101.2, 100.6, 100.7), c(t, 100.7, 100.8, 99.5, 99.6), c(t, 99.6, 100.1, 99.3, 99.4)
    assert find_gaps(d1, d2, d3) == {"kind": "bearish", "lo": 100.1, "hi": 100.6}


def test_daily_bias_is_the_last_daily_break():
    days = seq([(100, 101, 99.5, 100.8), (100.8, 102, 100.5, 101.8), (101.8, 101.9, 100.9, 101.0),   # high 102
                (101.0, 101.2, 100.2, 100.4), (100.4, 101.5, 100.3, 101.4),                         # low 100.2
                (101.4, 102.6, 101.3, 102.5)], step=24 * 60)                                       # closes above 102
    assert daily_structure(days) == "bullish"
    assert daily_structure(days[:5]) == "unknown"


# ---------------------------------------------------------------- the entry, end to end on 1-minute candles
def minutes(bars5, t0):
    """Expand 5-minute (o, h, l, c) bars into 1-minute candles along o -> extreme -> extreme -> c."""
    out, t = [], t0
    for o, h, low, cl in bars5:
        pts = [o, h, low, cl] if cl < o else [o, low, h, cl]
        pts.append(cl)
        for a, b in zip([o] + pts[:-1], pts):
            out.append(c(t, a, max(a, b), min(a, b), b))
            t += timedelta(minutes=1)
    return out


BEARISH_SETUP = [
    (100.0, 100.6, 99.9, 100.5), (100.5, 101.1, 100.4, 101.0), (101.0, 101.05, 100.5, 100.6),  # 5m high 101.1
    (100.6, 100.65, 100.2, 100.3), (100.3, 100.8, 100.25, 100.8),                                # 5m low 100.2
    (100.8, 101.4, 100.75, 101.3),                                    # takes the 101.1 highs: a sweep
    (101.3, 101.9, 101.25, 101.6), (101.6, 101.65, 100.95, 101.0),    # top of the leg at 101.9
    (101.0, 101.05, 100.05, 100.1),                                   # body closes below 100.2: bearish break
    (100.1, 100.9, 100.0, 100.9), (100.9, 101.2, 100.85, 101.15),     # retrace into premium and the 5m gap
    (101.15, 101.18, 100.6, 100.65),                                  # 1-minute break down: the entry
]


def test_sweep_break_retrace_then_lower_timeframe_break_fires_one_put():
    o = system()
    sigs, sweeps, breaks = collect(o, Signal), collect(o, LiquiditySweep), collect(o, BreakOfStructure)
    emit(o, *[CandleClosed(m.start + timedelta(minutes=1), m) for m in minutes(BEARISH_SETUP, cal.at(D, "09:30"))])
    assert any(s.tf == "5m" and s.kind == "high" and s.level == 101.1 for s in sweeps)
    assert any(b.tf == "5m" and b.side is Side.PUT and b.level == 100.2 for b in breaks)
    smc = [s for s in sigs if s.trigger == "smc_retrace"]
    assert len(smc) == 1
    s = smc[0]
    assert s.side is Side.PUT and s.setup["setup_tf"] == "5m" and s.setup["entry_tf"] == "1m"
    assert s.stop > 101.9                                    # beyond the swept extreme, plus the spread buffer
    assert s.setup["sweep"]["level"] == 101.1 and "5m fair value gap" in s.setup["poi"]
    assert s.target is not None and s.target < s.close       # the next resting lows below


def test_no_sweep_no_setup():
    o = system()
    sigs = collect(o, Signal)
    no_sweep = list(BEARISH_SETUP)
    no_sweep[5] = (100.8, 101.05, 100.75, 101.0)             # the leg never takes the 101.1 highs
    no_sweep[6] = (101.0, 101.08, 100.95, 101.05)
    no_sweep[7] = (101.05, 101.08, 100.95, 101.0)
    emit(o, *[CandleClosed(m.start + timedelta(minutes=1), m) for m in minutes(no_sweep, cal.at(D, "09:30"))])
    assert [s for s in sigs if s.trigger.startswith("smc")] == []


def test_close_beyond_the_swept_extreme_kills_the_setup():
    o = system()
    sigs = collect(o, Signal)
    bars = BEARISH_SETUP[:9] + [(100.1, 102.0, 100.0, 101.95)]   # straight back above 101.9: invalidated
    bars += BEARISH_SETUP[10:]
    emit(o, *[CandleClosed(m.start + timedelta(minutes=1), m) for m in minutes(bars, cal.at(D, "09:30"))])
    assert [s for s in sigs if s.trigger == "smc_retrace"] == []


# ---------------------------------------------------------------- the gate's TJR rules
def _signal(side=Side.PUT, close=100.65, stop=102.0, target=98.0, tf="5m", ts=None):
    return Signal(ts or cal.at(D, "10:30"), "QQQ", "smc_retrace", side, close, 100.85, 0.2, stop=stop, target=target,
                  setup={"setup_tf": tf})


def _gate(o, sig):
    ok, vetoes = collect(o, ResearchCleared), collect(o, EntryVetoed)
    emit(o, WorkerSignal(sig.ts, "QQQ OG", sig))
    return (vetoes[0].reason if vetoes else None), ok, vetoes


def _with_daily(o, trend):
    """Daily candles before D whose last break is `trend`."""
    htf = o.ctx.bots["htf_levels"]
    base = [(100, 101, 99.5, 100.8), (100.8, 102, 100.5, 101.8), (101.8, 101.9, 100.9, 101.0),
            (101.0, 101.2, 100.2, 100.4), (100.4, 101.5, 100.3, 101.4)]
    last = (101.4, 102.6, 101.3, 102.5) if trend == "bullish" else (101.4, 101.45, 99.8, 100.0)
    t0 = datetime.combine(D - timedelta(days=10), datetime.min.time(), cal.ET)
    htf.daily["QQQ"] = [c(t0 + timedelta(days=i), *b) for i, b in enumerate(base + [last])]


def _pass_edge(o):
    o.ctx.bots["edge_tracker"].stats = lambda *a: {"n": 20, "wins": 12, "losses": 8, "timeouts": 0, "win_rate": 0.6,
                                                   "avg_r": 0.5, "proven": True}
    o.ctx.bots["morning_study"].plan = lambda sym, d: MorningPlan(cal.at(d, "07:00"), sym, d, True, [], {})


def test_gate_needs_the_daily_bias_to_agree():
    o = system(research=True)
    _pass_edge(o)
    _with_daily(o, "bullish")
    reason, _, _ = _gate(o, _signal(Side.PUT))
    assert reason and "daily bias is bullish" in reason
    o = system(research=True)
    _pass_edge(o)
    reason, _, _ = _gate(o, _signal(Side.PUT))
    assert reason and "no daily bias yet" in reason            # no daily candles: no guessing, no trade
    o = system(research=True)
    _pass_edge(o)
    _with_daily(o, "bearish")
    reason, ok, _ = _gate(o, _signal(Side.PUT))
    assert reason is None and ok and ok[0].evidence["plan"]["rr"] > 1


def test_gate_refuses_poor_reward_and_news_days():
    o = system(research=True)
    _pass_edge(o)
    _with_daily(o, "bearish")
    reason, _, _ = _gate(o, _signal(Side.PUT, close=100.65, stop=102.0, target=100.0))   # 0.65 reward, 1.35 risk
    assert reason and reason.startswith("reward:risk")
    o = system(research=True)
    o.cfg.news.blackout_days = {D.isoformat(): "CPI"}
    o.ctx.bots["news_calendar"].setup()
    _pass_edge(o)
    _with_daily(o, "bearish")
    reason, _, _ = _gate(o, _signal(Side.PUT))
    assert reason == "news day (CPI): no trades"


def test_gate_wants_a_15m_setup_when_the_hourly_opposes_the_daily():
    o = system(research=True)
    _pass_edge(o)
    _with_daily(o, "bearish")
    o.ctx.bots["market_structure"].trend = lambda sym, tf: "bullish" if tf == "1h" else "unknown"
    reason, _, _ = _gate(o, _signal(Side.PUT, tf="5m"))
    assert reason and "needs a 15m setup" in reason
    reason, ok, _ = _gate(o, _signal(Side.PUT, tf="15m", ts=cal.at(D, "10:40")))
    assert reason is None and ok


def test_news_events_wait_after_the_release():
    o = system(research=True)
    o.cfg.news.events = {f"{D.isoformat()} 10:00": "Retail sales"}
    o.ctx.bots["news_calendar"].setup()
    news = o.ctx.bots["news_calendar"]
    assert news.blocked(cal.at(D, "10:10")).startswith("Retail sales at 10:00")
    assert news.blocked(cal.at(D, "10:31")) is None and news.blocked(cal.at(D, "09:50")) is None


def test_fading_a_daily_retrace_needs_price_in_the_daily_premium():
    o = system(research=True)
    _pass_edge(o)
    _with_daily(o, "bearish")
    o.ctx.bots["market_structure"].trend = lambda sym, tf: "bullish" if tf == "4h" else "unknown"
    eq = o.ctx.bots["daily_bias"].bias("QQQ", D)["D_range"]["eq"]
    low = _signal(Side.PUT, close=eq - 0.2, stop=eq + 1.0, target=eq - 3.0, tf="15m")
    reason, _, _ = _gate(o, low)
    assert reason and "isn't in the daily premium" in reason
    high = _signal(Side.PUT, close=eq + 0.2, stop=eq + 1.0, target=eq - 3.0, tf="15m", ts=cal.at(D, "10:45"))
    reason, ok, _ = _gate(o, high)
    assert reason is None and ok


def test_derisk_days_halve_the_size():
    o = system()
    o.cfg.news.derisk_days = {D.isoformat(): "day before a holiday"}
    o.ctx.bots["news_calendar"].setup()
    news = o.ctx.bots["news_calendar"]
    assert news.size_factor(D) == (0.5, "day before a holiday")
    assert news.size_factor(D + timedelta(days=1)) == (1.0, "")
    assert news.size_factor(date(2026, 11, 27))[0] == 0.5        # the day after Thanksgiving closes early


def test_only_setups_the_plan_would_take_count_as_evidence():
    o = system(research=True)
    _with_daily(o, "bearish")
    et = o.ctx.bots["edge_tracker"]
    assert et.in_plan(_signal(Side.PUT, ts=cal.at(D, "10:30")))          # with the bias, inside 09:35-15:30
    assert not et.in_plan(_signal(Side.CALL, ts=cal.at(D, "10:30")))     # against the daily bias
    assert not et.in_plan(_signal(Side.PUT, ts=cal.at(D, "15:45")))      # outside the trading window
    o.cfg.news.blackout_days = {D.isoformat(): "FOMC"}
    o.ctx.bots["news_calendar"].setup()
    assert not et.in_plan(_signal(Side.PUT, ts=cal.at(D, "10:30")))      # news day
    et.results[("QQQ", "smc_retrace")] = [(D, "PUT", "win", 2.0, False)] * 10   # out-of-plan wins prove nothing
    assert et.stats("QQQ", "smc_retrace", D)["n"] == 0


def test_morning_study_runs_at_seven_and_gates_the_day():
    o = system(research=True)
    _with_daily(o, "bearish")
    plans = collect(o, MorningPlan)
    emit(o, Heartbeat(cal.at(D, "06:59")))
    assert plans == []                                                  # not before 07:00
    emit(o, Heartbeat(cal.at(D, "07:00")), Heartbeat(cal.at(D, "07:01")))
    assert len(plans) == 1 and plans[0].symbol == "QQQ"                 # once a day, per ticker
    assert not plans[0].cleared and "record not proven" in plans[0].reasons[0]
    o.ctx.bots["edge_tracker"].stats = lambda *a: {"n": 20, "wins": 12, "avg_r": 0.5, "proven": True}
    reason, _, _ = _gate(o, _signal(Side.PUT))                          # a record later in the day doesn't undo it
    assert reason.startswith("stood down at the morning study")
    o2 = system(research=True)
    o2.ctx.bots["edge_tracker"].stats = lambda *a: {"n": 20, "wins": 12, "avg_r": 0.5, "proven": True}
    reason, _, _ = _gate(o2, _signal(Side.PUT))
    assert reason == "no morning study for today yet: nothing trades before it"


def test_bias_mode_against_trades_pullbacks_and_fixed_targets():
    o = system(research=True)
    o.cfg.smc.bias_mode = "against"
    _pass_edge(o)
    _with_daily(o, "bearish")
    reason, _, _ = _gate(o, _signal(Side.PUT))
    assert reason and "trades against the daily bias" in reason
    reason, ok, _ = _gate(o, _signal(Side.CALL, close=100.0, stop=99.0, target=101.0, ts=cal.at(D, "10:40")))
    assert reason is None and ok
    o.cfg.smc.target_mode = "fixed"
    assert o.ctx.bots["sig_smc"].target("QQQ", Side.CALL, 100.0, 99.0) == (101.0, "1R")


def test_contract_scout_prefers_the_contract_that_keeps_the_plan():
    from scalpcity.core.events import OptionContract, OptionQuote
    o = system()
    sel = o.ctx.bots["contract_selector"]
    w = o.cfg.workers[0]
    ts = cal.at(D, "10:00")
    sig = Signal(ts, "QQQ", "smc_retrace", Side.CALL, 700.0, 699.5, 0.5, stop=698.0, target=702.0)

    def q(strike, days, bid, ask, delta):
        exp = cal.next_trading_day(D, days)
        return OptionQuote(ts, OptionContract("QQQ", exp, strike, Side.CALL), bid, ask, delta, 0.2, 700.0)
    lottery = q(706, 0, 0.05, 0.08, 0.10)          # far out of the money: filtered (delta < 0.30)
    wide = q(695, 2, 6.00, 8.50, 0.75)             # spread too wide to keep the move
    good = q(695, 2, 7.20, 7.30, 0.75)
    best, why = sel.scout([lottery, wide, good], sig, w)
    assert best is good and why == ""
    best, why = sel.scout([lottery, wide], sig, w)
    assert best is None and "no liquid contract" in why          # the wide one fails the 12% spread limit
    tiny = Signal(ts, "QQQ", "smc_retrace", Side.CALL, 700.0, 699.5, 0.5, stop=698.0, target=700.05)
    best, why = sel.scout([good], tiny, w)
    assert best is None and "keeps the planned move" in why      # a 5-cent target can't pay a 10-cent spread


# ---------------------------------------------------------------- learning from wins and losses
def _trade(o, side=Side.CALL, close=100.0, stop=99.0, target=101.0):
    from scalpcity.core.events import OptionContract, PositionOpened
    sig = Signal(cal.at(D, "10:00"), "QQQ", "smc_retrace", side, close, 99.5, 0.5, stop=stop, target=target,
                 setup={"setup_tf": "5m", "sweep": {"tf": "15m"}, "poi": ["5m order block"]})
    con = OptionContract("QQQ", D, 100, side)
    emit(o, PositionOpened(sig.ts, "QQQ OG", con, 1, 2.0, sig))
    return con


def test_reviews_say_what_went_right_and_what_went_wrong():
    from scalpcity.core.events import SessionEvent, SessionKind, Tick, TradeClosed, TradeReview
    o = system()
    reviews = collect(o, TradeReview)
    con = _trade(o)
    emit(o, Tick(cal.at(D, "10:20"), "QQQ", 101.1, 1),
         TradeClosed(cal.at(D, "10:21"), "QQQ OG", con, 1, 2.0, 2.6, 60.0, "target", cal.at(D, "10:00")))
    assert reviews[-1].won and reviews[-1].verdict == "target" and "What went right" in reviews[-1].text
    con = _trade(o)                                             # stopped, then the target printed: stop too tight
    emit(o, Tick(cal.at(D, "11:00"), "QQQ", 98.9, 1),
         TradeClosed(cal.at(D, "11:01"), "QQQ OG", con, 1, 2.0, 1.5, -50.0, "stop", cal.at(D, "10:00")),
         Tick(cal.at(D, "12:00"), "QQQ", 101.2, 1))
    assert reviews[-1].verdict == "stop_too_tight" and "stop was too tight" in reviews[-1].text
    con = _trade(o)                                             # stopped and never recovered: the setup failed
    emit(o, Tick(cal.at(D, "13:00"), "QQQ", 98.8, 1),
         TradeClosed(cal.at(D, "13:01"), "QQQ OG", con, 1, 2.0, 1.4, -60.0, "stop", cal.at(D, "10:00")),
         SessionEvent(cal.at(D, "16:00"), SessionKind.CLOSED, D))
    assert reviews[-1].verdict == "setup_failed" and "setup failed" in reviews[-1].text
    con = _trade(o)                                             # the stock got there, the option still lost
    emit(o, Tick(cal.at(D, "14:00"), "QQQ", 101.05, 1),
         TradeClosed(cal.at(D, "14:30"), "QQQ OG", con, 1, 2.0, 1.9, -10.0, "time", cal.at(D, "10:00")))
    assert reviews[-1].verdict == "option_costs"


def test_lessons_need_repeated_evidence_before_becoming_rules(tmp_path):
    from scalpcity.core.events import SetupScored
    o = system()
    o.cfg.research.lessons_path = str(tmp_path / "lessons.json")
    book = o.ctx.bots["lessons"]
    book.setup()
    f = {"ticker": "QQQ", "hour": "10:00-11:00", "zone": "gap", "trigger": "smc_retrace"}

    def scored(i, r, zone="gap"):
        return SetupScored(cal.at(D, "10:00") + timedelta(minutes=i), "QQQ", "smc_retrace", Side.CALL,
                           "loss" if r < 0 else "win", r, {**f, "zone": zone}, True)
    emit(o, *[scored(i, -1.0 if i % 4 else 0.5) for i in range(10)])
    assert book.check(f) is None                                # 10 cases: not enough to make a rule
    emit(o, *[scored(i, -1.0 if i % 4 else 0.5) for i in range(10, 40)])
    emit(o, *[scored(i, -1.0 if i % 4 else 0.5) for i in range(0, 5)])   # replayed history counts once
    emit(o, *[scored(100 + i, 1.0 if i % 4 else -1.0, "order block") for i in range(40)])
    assert book.stats["smc_retrace|zone=gap"][0] == 40 and book.stats["smc_retrace|ticker=QQQ"][0] == 80
    emit(o, SetupScored(cal.at(D, "11:00"), "QQQ", "vwap_cross", Side.CALL, "loss", -1.0, f, True))
    assert book.stats["smc_retrace|zone=gap"][0] == 40          # strategies no tower trades teach nothing
    rule = book.check(f)
    assert rule and "zone = gap lost" in rule                   # 40 cases, clearly negative: avoid
    assert book.check({**f, "zone": "order block"}) is None
    emit(o, SessionEvent(cal.at(D, "16:00"), SessionKind.CLOSED, D))
    again = system()
    again.cfg.research.lessons_path = o.cfg.research.lessons_path
    again.ctx.bots["lessons"].setup()
    assert again.ctx.bots["lessons"].check(f)                   # the book survives a restart


# ---------------------------------------------------------------- afternoon session (owner, 2026-10-21)
def test_afternoon_session_only_after_a_missed_morning_and_on_its_own_record():
    from scalpcity.core.config import session_of
    o = system(("smc_retrace", "orb_ntz_retest"), research=True)
    w = o.cfg.workers[0]
    w.start_time, w.end_time, w.pm_start, w.pm_end = "09:35", "11:00", "13:00", "15:00"
    assert session_of(w, cal.at(D, "10:00")) == "am" and session_of(w, cal.at(D, "13:30")) == "pm"
    assert session_of(w, cal.at(D, "12:00")) is None
    et = o.ctx.bots["edge_tracker"]
    am = [(D - timedelta(days=1), "PUT", "win", 1.0, True, "am")] * 10
    pm = [(D - timedelta(days=1), "PUT", "loss", -1.0, True, "pm")] * 10
    et.results[("QQQ", "smc_retrace")] = am + pm
    assert et.stats("QQQ", "smc_retrace", D)["proven"]                         # the morning stands on its own
    assert not et.stats("QQQ", "smc_retrace", D, "pm")["proven"]               # the afternoon lost: no edge
    _with_daily(o, "bullish")
    o.cfg.smc.bias_mode = "against"
    plans = collect(o, MorningPlan)
    emit(o, Heartbeat(cal.at(D, "07:00")))
    assert plans[0].cleared                                    # one proven strategy is enough to open the tower
    assert any("orb_ntz_retest" in u for u in plans[0].details["unproven"])
    reason, _, _ = _gate(o, _signal(Side.PUT, ts=cal.at(D, "13:30")))
    assert reason.startswith("no edge in the afternoon session")
    skipped = collect(o, SignalSkipped)
    o.ctx.bots["risk_manager"].entries_today = 1                # the account traded this morning
    emit(o, _signal(Side.PUT, ts=cal.at(D, "13:31")))
    assert any("only for a missed morning" in s.reason for s in skipped)
