"""The futures city: front-month selection, long AND short trades, margin, sizing in points, IBKR paper-only."""
import asyncio
from datetime import date, timedelta

import pytest

from scalpcity.brokers.ibkr_conn import paper_only
from scalpcity.brokers.sim import SimBroker
from scalpcity.core import calendar as cal
from scalpcity.core.config import Config, ExitRules, Sizing, WorkerConfig, validate
from scalpcity.core.events import (Heartbeat, OrderSide, Side, Signal, Tick, TradeClosed, OrderIntent, WorkerSignal)
from scalpcity.core.futures import front_month
from scalpcity.orchestrator import Orchestrator

D = date(2026, 10, 21)


def fut_cfg(**over) -> Config:
    w = WorkerConfig(name="MES", symbol="MES", triggers=["smc_retrace"], sizing=Sizing(mode="risk", risk=300,
                     max_contracts=10), exits=ExitRules(measure="structure", max_hold_minutes=390),
                     daily_goal=10_000, max_daily_loss=10_000)
    cfg = Config(mode="backtest", market="futures", workers=[w], db_path=":memory:", **over)
    cfg.data.source, cfg.broker.name, cfg.dashboard.enabled = "synthetic", "sim", False
    cfg.research.enabled, cfg.research.lessons_path = False, ""
    cfg.risk.max_daily_loss = 100_000
    validate(cfg)
    return cfg


def test_front_month_rolls_a_week_before_expiry():
    cfg = fut_cfg()
    c = front_month(cfg, "MES", D, Side.CALL)
    assert c.occ == "MESZ6" and c.expiry == date(2026, 12, 18) and c.multiplier == 5 and c.label == "MESZ6 LONG"
    assert front_month(cfg, "MES", date(2026, 12, 11), Side.PUT).occ == "MESH7"   # rolled 8 days before expiry
    assert front_month(cfg, "MGC", D, Side.CALL).occ == "MGCZ6"
    assert front_month(cfg, "MGC", date(2026, 11, 16), Side.CALL).occ == "MGCG7"  # gold rolls mid-month before


def test_sim_short_future_settles_profit_in_cash_and_margin_is_set_aside():
    cfg = fut_cfg()
    short = front_month(cfg, "MES", D, Side.PUT)
    from scalpcity.core.events import OptionQuote
    px = {"bid": 6000.0, "ask": 6000.25}
    sim = SimBroker(30_000, cfg.sim, lambda c: OptionQuote(cal.at(D, "10:00"), c, px["bid"], px["ask"], -1.0),
                    lambda: D)

    async def go():
        await sim.submit(short, OrderSide.SELL, 2, None)                 # short 2 at the bid
        acct = await sim.account()
        assert sim.pos["MESZ6"] == -2 and acct.options_buying_power == pytest.approx(30_000 - 2 * 0.62 - 2 * 2700)
        px.update(bid=5989.75, ask=5990.0)
        await sim.submit(short, OrderSide.BUY, 2, None)                  # cover 2 at the ask, 10 points lower
        return await sim.account()
    asyncio.run(go())
    assert "MESZ6" not in sim.pos
    assert sim.cash == pytest.approx(30_000 + 2 * 10 * 5 - 4 * 0.62)    # +$100 less four fills of fees


def test_a_bearish_setup_sells_the_future_short_sized_from_the_chart_stop():
    cfg = fut_cfg()
    cfg.risk.max_premium_exposure = 30_000       # room for 10 contracts of margin (the default $8,000 allows 2)
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    closed, intents = [], []
    o.bus.subscribe(TradeClosed, closed.append, "t")
    o.bus.subscribe(OrderIntent, intents.append, "t")
    t0 = cal.at(D, "10:00")

    async def go():
        await o.bus.emit(Heartbeat(cal.at(D, "09:29") + timedelta(seconds=59)))
        await o.bus.emit(Heartbeat(t0))
        await o.bus.emit(Tick(t0, "MES", 6000.0, 1))
        sig = Signal(t0, "MES", "smc_retrace", Side.PUT, 6000.0, 6001.0, 2.0, stop=6006.0, target=5994.0)
        await o.bus.emit(WorkerSignal(t0, "MES", sig))
        await o.bus.emit(Tick(t0 + timedelta(minutes=5), "MES", 5993.75, 1))   # through the target
    asyncio.run(go())
    entry = intents[0]
    assert entry.side is OrderSide.SELL and entry.contract.occ == "MESZ6" and entry.contract.way == -1
    assert entry.qty == 10                       # $300 / (6 points x $5) = 10 contracts
    assert intents[1].side is OrderSide.BUY      # the exit buys it back
    assert closed and closed[0].reason == "target" and closed[0].pnl > 0


def test_one_contract_too_big_for_the_risk_is_refused_not_rounded_up():
    from scalpcity.core.events import ContractRejected
    o = Orchestrator(fut_cfg(), db_path=":memory:", dashboard=False)
    rej = []
    o.bus.subscribe(ContractRejected, rej.append, "t")
    t0 = cal.at(D, "10:00")

    async def go():
        await o.bus.emit(Heartbeat(cal.at(D, "09:29") + timedelta(seconds=59)))
        await o.bus.emit(Tick(t0, "MES", 6000.0, 1))
        sig = Signal(t0, "MES", "smc_retrace", Side.CALL, 6000.0, 5999.0, 5.0, stop=5920.0, target=6080.0)
        await o.bus.emit(WorkerSignal(t0, "MES", sig))                    # 80-point stop = $400 for one contract
    asyncio.run(go())
    assert rej and "would risk $400" in rej[0].reason


def test_futures_city_is_paper_only():
    paper_only(["DU1234567"])
    with pytest.raises(RuntimeError, match="not a paper account"):
        paper_only(["U1234567"])
    cfg = fut_cfg()
    cfg.mode, cfg.broker.name = "paper", "ibkr"
    validate(cfg)
    cfg.broker.ib_port = 4001
    with pytest.raises(ValueError, match="LIVE ports"):
        validate(cfg)
    cfg.broker.ib_port, cfg.mode = 4002, "live"
    with pytest.raises(ValueError):
        validate(cfg)


def test_ibkr_broker_reports_signed_futures_positions_only():
    from types import SimpleNamespace as NS

    from scalpcity.brokers import ibkr_conn
    from scalpcity.brokers.ibkr import IBKRBroker
    fake = NS(isConnected=lambda: True, managedAccounts=lambda: ["DU1"], positions=lambda: [
        NS(contract=NS(secType="FUT", localSymbol="MESZ6"), position=-3),
        NS(contract=NS(secType="STK", localSymbol="SPY"), position=10)])
    ibkr_conn.use(fake)
    cfg = fut_cfg()
    cfg.broker.name = "ibkr"
    b = IBKRBroker(cfg)
    try:
        assert asyncio.run(b.positions()) == {"MESZ6": -3}
        b.trades["7"] = NS(orderStatus=NS(status="Submitted", filled=1, avgFillPrice=6000.25), order=None)
        st = asyncio.run(b.status("7"))
        assert st.status == "partially_filled" and st.filled_qty == 1
    finally:
        ibkr_conn.use(None)


def test_options_config_refuses_futures_settings():
    from tests.conftest import make_cfg
    cfg = make_cfg()
    cfg.broker.name = "ibkr"
    with pytest.raises(ValueError, match="futures city"):
        validate(cfg)
