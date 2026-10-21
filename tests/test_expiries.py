"""Expiry calendar, contract costs, reconciliation, and the options-only rule."""
import asyncio
from datetime import date

import pytest

from scalpcity.bots.decision_bots import ContractSelectorBot
from scalpcity.bots.execution_bots import ReconciliationBot
from scalpcity.core import calendar as cal
from scalpcity.core.config import Sizing, WorkerConfig
from scalpcity.core.costs import fees, round_qty
from scalpcity.core.events import (ContractRejected, ContractSelected, OptionContract, Side, Signal,
                                   WorkerSignal)
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg


def test_costs_per_contract():
    sim = make_cfg().sim
    opt = OptionContract("QQQ", date(2026, 10, 2), 752.0, Side.CALL)
    assert fees(opt, 3, 3.5, sim) == 3 * sim.fee_per_contract
    assert round_qty(opt, 4.99) == 4


def test_config_rejects_non_stock_symbols():
    with pytest.raises(ValueError, match="options only"):
        make_cfg(workers=[WorkerConfig(name="BTC", symbol="BTC/USD")])


def test_modeled_expiry_calendar():
    cfg = make_cfg()
    cfg.sim.expiry_weekdays["NVDA"] = [0, 2, 4]
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    sim = o.ctx.bots["options_chain"].sim
    assert sim.listed("SPY", date(2026, 10, 13))                 # daily
    assert sim.listed("NVDA", date(2026, 10, 14)) and not sim.listed("NVDA", date(2026, 10, 15))
    assert not sim.listed("XYZ", date(2026, 10, 15)) and sim.listed("XYZ", date(2026, 10, 16))  # Fridays
    assert sim.listed("XYZ", date(2026, 4, 2))                   # Good Friday 2026-04-03 -> Thursday


def test_selector_walks_forward_to_next_listed_expiry():
    cfg = make_cfg(workers=[WorkerConfig(name="X", symbol="XYZ", sizing=Sizing(mode="fixed", contracts=1))])
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    chain = o.ctx.bots["options_chain"]
    tue = date(2026, 10, 13)
    chain.sim.spot["XYZ"] = 100.0
    chain.last_ts = cal.at(tue, "10:00")
    out = []
    o.bus.subscribe(ContractSelected, out.append, "t")
    o.bus.subscribe(ContractRejected, out.append, "t")
    sig = Signal(cal.at(tue, "10:00"), "XYZ", "vwap_cross", Side.CALL, 100.0, 99.9, 0.2)
    asyncio.run(o.bus.emit(WorkerSignal(sig.ts, "X", sig)))
    assert isinstance(out[0], ContractSelected) and out[0].quote.contract.expiry == date(2026, 10, 16)
    assert ContractSelectorBot.MAX_EXPIRY_SEARCH >= 4


def test_reconciliation_needs_an_exact_match():
    m = ReconciliationBot.matches
    assert m({"QQQ261002C00752000": 3}, {"QQQ261002C00752000": 3})
    assert not m({"QQQ261002C00752000": 3}, {"QQQ261002C00752000": 2})
    assert not m({"QQQ261002C00752000": 3}, {})
    assert m({}, {})
