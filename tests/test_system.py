"""End-to-end: whole system replaying synthetic days through the simulator."""
import asyncio
from datetime import date

from scalpcity.core import calendar as cal
from scalpcity.core.events import Fill, OptionQuote, PositionOpened, TradeClosed
from scalpcity.core.config import Sizing, WorkerConfig
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

DAYS = cal.trading_days(date(2026, 9, 28), date(2026, 10, 2))


def replay(cfg, days=DAYS):
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    report = asyncio.run(o.replay(days))
    return o, report


def test_full_week_runs_flat_and_books_balance():
    cfg = make_cfg()
    o, report = replay(cfg)
    assert report["days"] == len(DAYS)
    assert report["trades"] > 10
    assert o.ctx.bots["ledger"].holdings() == {}            # flat every night
    assert asyncio.run(o.ctx.broker.positions()) == {}
    trade_pnl = sum(r[9] for r in o.storage.trades())
    assert abs((o.ctx.broker.cash - cfg.sim.starting_cash) - trade_pnl) < 0.05   # broker cash == ledger P&L
    fills = o.storage.db.execute("SELECT count(*) FROM fills").fetchone()[0]
    assert fills == 2 * len(o.storage.trades())             # every entry has exactly one exit


def test_replay_is_deterministic():
    _, a = replay(make_cfg(), DAYS[:2])
    _, b = replay(make_cfg(), DAYS[:2])
    assert a == b


def test_no_entries_outside_window_and_flat_by_flatten_time():
    o, _ = replay(make_cfg(), DAYS[:3])
    for row in o.storage.trades():
        closed, opened = row[0], row[1]
        assert "09:35" <= opened[11:16] < "15:31"
        assert closed[11:16] <= "15:56"


def test_shared_contract_keeps_streaming_quotes_for_remaining_holder():
    workers = [WorkerConfig(name=n, symbol="QQQ", triggers=["vwap_cross"], sizing=Sizing(mode="fixed", contracts=1),
                            daily_goal=1e9, max_daily_loss=1e9) for n in ("A", "B")]
    workers[1].exits.take_profit_pct = 1000  # B holds longer than A
    workers[1].exits.stop_loss_pct = 1000
    workers[1].exits.trail_activate_pct = 1000
    cfg = make_cfg(workers=workers)
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    quotes_after_a_closed = []
    state = {"a_closed": None}

    def on_closed(e):
        if e.worker == "A" and "B" in o.ctx.bots["ledger"].pos:
            state["a_closed"] = o.ctx.bots["ledger"].pos["B"]["contract"]

    def on_quote(q):
        if state["a_closed"] is not None and q.contract == state["a_closed"]:
            quotes_after_a_closed.append(q)

    o.bus.subscribe(TradeClosed, on_closed, "t")
    o.bus.subscribe(OptionQuote, on_quote, "t")
    asyncio.run(o.replay(DAYS[:1]))
    assert state["a_closed"] is not None
    assert quotes_after_a_closed, "B stopped receiving quotes when A closed the same contract"


def test_daily_goal_stops_worker_for_rest_of_day():
    cfg = make_cfg()
    for w in cfg.workers:
        w.daily_goal = 1.0   # first winning trade clocks the worker out
    o, _ = replay(cfg, DAYS[:2])
    rows = o.storage.trades()
    for worker in ("QQQ OG", "SPY"):
        for day in ("2026-09-28", "2026-09-29"):
            day_trades = [r for r in rows if r[4] == worker and r[0].startswith(day)]
            pnl, after = 0.0, False
            for r in day_trades:
                assert not after, f"{worker} traded after reaching its goal on {day}"
                pnl += r[9]
                after = pnl >= 1.0
