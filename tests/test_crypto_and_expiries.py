"""Crypto market mode, fractional quantities, and the option expiry calendar."""
import asyncio
import json
from datetime import date, timedelta

import httpx

from scalpcity.bots.decision_bots import ContractSelectorBot
from scalpcity.bots.execution_bots import ReconciliationBot
from scalpcity.core import calendar as cal
from scalpcity.core.config import Config, ExitRules, Sizing, WorkerConfig, validate
from scalpcity.core.costs import fees, round_qty
from scalpcity.core.events import (ContractRejected, ContractSelected, CryptoAsset, OptionContract, OrderSide,
                                   SessionEvent, SessionKind, Side, Signal, SignalSkipped, WorkerSignal)
from scalpcity.data.bars import fill_gaps
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

BTC = CryptoAsset("BTC/USD")


def crypto_cfg(**over) -> Config:
    workers = over.pop("workers", None) or [
        WorkerConfig(name="BTC", symbol="BTC/USD", start_time="00:20", end_time="23:30",
                     sizing=Sizing(mode="budget", budget=2000, max_contracts=1),
                     exits=ExitRules(take_profit_pct=1.0, stop_loss_pct=0.5, trail_activate_pct=0.6,
                                     trail_lock_ratio=0.5, max_hold_minutes=60),
                     daily_goal=10_000, max_daily_loss=10_000)]
    cfg = Config(mode="backtest", market="crypto", workers=workers, db_path=":memory:",
                 entry_cutoff="23:30", flatten_time="23:55", **over)
    cfg.data.source, cfg.broker.name, cfg.dashboard.enabled = "synthetic", "sim", False
    cfg.risk.max_daily_loss = 100_000
    cfg.risk.max_spread_pct = 0.5
    validate(cfg)
    return cfg


# ---------------------------------------------------------------- calendar
def test_crypto_calendar_runs_every_day_midnight_to_midnight():
    sat = date(2026, 10, 17)
    assert not cal.is_trading_day(sat)
    cal.set_market("crypto")
    assert cal.is_trading_day(sat) and cal.is_trading_day(date(2026, 12, 25))
    assert cal.session_open(sat) == cal.at(sat, "00:00")
    assert cal.session_close(sat) == cal.at(sat + timedelta(days=1), "00:00")
    assert cal.close_shift(sat) == timedelta(0)


def test_config_rejects_mixed_markets():
    import pytest
    with pytest.raises(ValueError, match="doesn't fit market"):
        validate(Config(mode="backtest", market="crypto", workers=[WorkerConfig("Q", "QQQ")]))
    with pytest.raises(ValueError, match="doesn't fit market"):
        validate(Config(mode="backtest", workers=[WorkerConfig("B", "BTC/USD")]))


# ---------------------------------------------------------------- costs
def test_costs_per_instrument():
    sim = make_cfg().sim
    opt = OptionContract("QQQ", date(2026, 10, 2), 752.0, Side.CALL)
    assert fees(opt, 3, 3.5, sim) == 3 * sim.fee_per_contract
    assert fees(BTC, 0.02, 80_000, sim) == round(0.02 * 80_000 * 0.25 / 100, 4)
    assert round_qty(opt, 4.99) == 4 and round_qty(BTC, 0.024999999999999998) == 0.025
    assert round_qty(BTC, 2000 / 81_234.5) == 0.02462


# ---------------------------------------------------------------- full crypto system
def test_crypto_week_trades_long_only_and_books_balance():
    cfg = crypto_cfg()
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    skipped = []
    o.bus.subscribe(SignalSkipped, skipped.append, "t")
    sessions = []
    o.bus.subscribe(SessionEvent, sessions.append, "t")
    days = [date(2026, 10, 10) + timedelta(days=i) for i in range(3)]   # includes a weekend
    report = asyncio.run(o.replay(days))
    assert report["days"] == 3 and [d["day"] for d in report["daily"]] == [d.isoformat() for d in days]
    assert report["trades"] > 0
    assert any(s.reason.startswith("long only") for s in skipped)
    trades = o.storage.trades()
    assert all(r[5] == "BTCUSD" and 0 < r[6] <= 1 for r in trades)        # fractional coin, capped at 1
    assert o.ctx.bots["ledger"].holdings() == {}
    trade_pnl = sum(r[9] for r in trades)
    assert abs((o.ctx.broker.cash - cfg.sim.starting_cash) - trade_pnl) < 0.05
    closes = [e for e in sessions if e.kind is SessionKind.CLOSED]
    assert [e.day for e in closes] == days                                  # each midnight closes its day once


def test_crypto_opening_range_locks_at_0015():
    cfg = crypto_cfg()
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    asyncio.run(o.replay([date(2026, 10, 10)]))
    hi, lo, locked = o.ctx.bots["opening_range"].range("BTC/USD")
    assert locked and hi > lo


def test_fill_gaps_makes_flat_bars_for_quiet_minutes():
    cal.set_market("crypto")
    from scalpcity.core.events import Candle
    d = date(2026, 10, 10)
    t0 = cal.session_open(d)
    bars = [Candle("BTC/USD", t0, 1, 2, 1, 2, 5), Candle("BTC/USD", t0 + timedelta(minutes=3), 2, 3, 2, 3, 1)]
    out = fill_gaps(bars, d)
    assert [b.start for b in out] == [t0 + timedelta(minutes=i) for i in range(4)]
    assert (out[1].open, out[1].close, out[1].volume) == (2, 2, 0.0)


# ---------------------------------------------------------------- option expiries
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


# ---------------------------------------------------------------- reconciliation + broker
def test_reconciliation_tolerates_crypto_fee_shortfall_only():
    m = ReconciliationBot.matches
    assert m({"QQQ261002C00752000": 3}, {"QQQ261002C00752000": 3})
    assert not m({"QQQ261002C00752000": 3}, {"QQQ261002C00752000": 2})
    assert m({"BTCUSD": 0.02462}, {"BTCUSD": 0.02455845})                  # 0.25% fee taken in coin
    assert not m({"BTCUSD": 0.02462}, {"BTCUSD": 0.0123})
    assert not m({"BTCUSD": 0.02462}, {})


def test_alpaca_crypto_orders(monkeypatch):
    from scalpcity.brokers.alpaca import AlpacaBroker
    monkeypatch.setenv("ALPACA_API_KEY_ID", "k")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "s")
    sent = []

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/v2/positions":
            return httpx.Response(200, json=[{"symbol": "BTCUSD", "qty": "0.024558", "asset_class": "crypto"}])
        if req.url.path == "/v2/orders" and req.method == "POST":
            sent.append(json.loads(req.content))
            return httpx.Response(200, json={"id": f"o{len(sent)}"})
        if req.url.path.startswith("/v2/orders/"):
            return httpx.Response(200, json={"status": "filled", "filled_qty": "0.024558", "filled_avg_price": "81000",
                                             "asset_class": "crypto"})
        return httpx.Response(404)

    async def go():
        b = AlpacaBroker("paper")
        b.http = httpx.AsyncClient(base_url="https://paper-api.alpaca.markets", headers=b.http.headers,
                                   transport=httpx.MockTransport(handler))
        await b.submit(BTC, OrderSide.BUY, 0.02462, 81000.5)
        oid = await b.submit(BTC, OrderSide.SELL, 0.02462, None)
        st = await b.status(oid)
        pos = await b.positions()
        await b.close()
        return st, pos

    st, pos = asyncio.run(go())
    assert sent[0] == {"symbol": "BTC/USD", "side": "buy", "qty": "0.02462", "time_in_force": "gtc",
                       "type": "limit", "limit_price": "81000.50"}
    assert sent[1]["qty"] == "0.024558" and sent[1]["type"] == "market"    # sells what is really held
    assert abs(st.filled_qty - 0.02462) < 1e-9                              # reported as the ledger's quantity
    assert pos == {"BTCUSD": 0.024558}


def test_crypto_quote_stream_dedupes_mid():
    from scalpcity.data.alpaca_data import AlpacaCryptoStream
    got = []

    async def on_trade(*a):
        got.append(a)

    s = AlpacaCryptoStream(["BTC/USD"], on_trade)
    assert s.subscription() == {"action": "subscribe", "quotes": ["BTC/USD"]}
    q = {"T": "q", "S": "BTC/USD", "bp": 81000.0, "ap": 81010.0, "t": "2026-10-17T04:00:00Z"}
    asyncio.run(s.handle(json.dumps([q, q, {**q, "ap": 81020.0}])))
    assert [g[2] for g in got] == [81005.0, 81010.0] and got[0][3] == 0.0
