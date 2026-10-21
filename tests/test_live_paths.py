"""Paper/live code paths, tested offline against mocked Alpaca and Polygon responses."""
import asyncio
import json
from datetime import date, datetime, timedelta

import httpx
import pytest

from scalpcity.brokers.base import Account, Broker, OrderStatus
from scalpcity.core import calendar as cal
from scalpcity.core.events import (Fill, OptionContract, OrderApproved, OrderFailed, OrderIntent, OrderSide, Purpose,
                                   Side, Tick)
from scalpcity.data.polygon import _bars_from_results, _quote_from_snapshot
from scalpcity.orchestrator import Orchestrator
from tests.conftest import make_cfg

D = date(2026, 10, 2)
C = OptionContract("QQQ", D, 752.0, Side.CALL)


# ---------------------------------------------------------------- Alpaca
def test_alpaca_requests(monkeypatch):
    from scalpcity.brokers.alpaca import AlpacaBroker
    monkeypatch.setenv("ALPACA_API_KEY_ID", "k")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "s")
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        assert req.headers["APCA-API-KEY-ID"] == "k" and req.headers["APCA-API-SECRET-KEY"] == "s"
        if req.url.path == "/v2/account":
            return httpx.Response(200, json={"equity": "31000.5", "cash": "30000", "options_buying_power": "29000",
                                             "daytrade_count": 2, "pattern_day_trader": False, "multiplier": "2"})
        if req.url.path == "/v2/orders" and req.method == "POST":
            return httpx.Response(200, json={"id": "abc"})
        if req.url.path == "/v2/orders/abc" and req.method == "GET":
            return httpx.Response(200, json={"status": "partially_filled", "filled_qty": "3", "filled_avg_price": "3.68"})
        if req.url.path == "/v2/orders/abc" and req.method == "DELETE":
            return httpx.Response(422, json={"message": "order is already filled"})
        if req.url.path == "/v2/positions":
            return httpx.Response(200, json=[{"symbol": C.occ, "qty": "5", "asset_class": "us_option"},
                                             {"symbol": "AAPL", "qty": "10", "asset_class": "us_equity"},
                                             {"symbol": "BTC/USD", "qty": "0.0029", "asset_class": "crypto"}])
        return httpx.Response(404)

    async def go():
        b = AlpacaBroker("paper")
        assert str(b.http.base_url).startswith("https://paper-api.alpaca.markets")
        b.http = httpx.AsyncClient(base_url="https://paper-api.alpaca.markets", headers=b.http.headers,
                                   transport=httpx.MockTransport(handler))
        acct = await b.account()
        oid = await b.submit(C, OrderSide.BUY, 18, 3.68)
        mkt = await b.submit(C, OrderSide.SELL, 18, None)
        st = await b.status("abc")
        await b.cancel("abc")  # 422 must be tolerated
        pos = await b.positions()
        await b.close()
        return acct, oid, mkt, st, pos

    acct, oid, mkt, st, pos = asyncio.run(go())
    assert acct == Account(31000.5, 30000.0, 29000.0, 2, False, False)
    assert oid == "abc" and mkt == "abc"
    body = json.loads(seen[1].content)
    assert body == {"symbol": "QQQ261002C00752000", "qty": "18", "side": "buy", "time_in_force": "day",
                    "type": "limit", "limit_price": "3.68"}
    assert json.loads(seen[2].content)["type"] == "market" and "limit_price" not in json.loads(seen[2].content)
    assert st == OrderStatus("partially_filled", 3, 3.68)
    assert pos == {C.occ: 5}                     # only options count: stock and coins in the account aren't ours


def test_alpaca_requires_keys(monkeypatch):
    from scalpcity.brokers.alpaca import AlpacaBroker
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    with pytest.raises(RuntimeError, match="ALPACA_API_KEY_ID"):
        AlpacaBroker("paper")


# ---------------------------------------------------------------- Polygon parsing
def test_polygon_snapshot_and_bars_parsing():
    snap = {"details": {"ticker": "O:QQQ261002C00752000", "strike_price": 752, "contract_type": "call",
                        "expiration_date": "2026-10-02"},
            "last_quote": {"bid": 3.6, "ask": 3.68}, "greeks": {"delta": 0.52}, "implied_volatility": 0.18,
            "underlying_asset": {"price": 752.11}}
    q = _quote_from_snapshot(snap, cal.at(D, "10:00"))
    assert q.contract == C and q.bid == 3.6 and q.ask == 3.68 and q.delta == 0.52 and q.underlying_price == 752.11
    assert _quote_from_snapshot({"details": snap["details"]}, cal.at(D, "10:00")) is None  # no quote -> skip
    ms = lambda hhmm: int(cal.at(D, hhmm).timestamp() * 1000)  # noqa: E731
    bars = _bars_from_results("QQQ", [{"t": ms("09:29"), "o": 1, "h": 1, "l": 1, "c": 1, "v": 1},
                                      {"t": ms("09:30"), "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 9},
                                      {"t": ms("16:00"), "o": 1, "h": 1, "l": 1, "c": 1, "v": 1}])
    assert [b.start for b in bars] == [cal.at(D, "09:30")]  # pre/after-hours dropped


def test_live_aggregate_becomes_ticks():
    o = Orchestrator(make_cfg(), db_path=":memory:", dashboard=False)
    ticks = []
    o.bus.subscribe(Tick, ticks.append, "t")
    ts = cal.at(D, "10:00") + timedelta(seconds=5)
    asyncio.run(o.feed._on_agg("QQQ", ts, 750.0, 751.0, 749.5, 750.5, 1200.0))
    assert [(t.price, t.size) for t in ticks] == [(751.0, 0.0), (749.5, 0.0), (750.5, 1200.0)]


# ---------------------------------------------------------------- async execution (real-broker behaviour)
class SlowBroker(Broker):
    """Behaves like a real broker: orders rest, fill partially, get cancelled."""
    synchronous_fills = False

    def __init__(self, script):
        self.script = script          # list of (status, filled_qty, avg) returned by successive status() calls per order
        self.submits = []
        self.cancels = []

    async def account(self):
        return Account(50_000, 50_000, 50_000)

    async def submit(self, contract, side, qty, limit):
        self.submits.append((side, qty, limit))
        return f"o{len(self.submits)}"

    async def status(self, oid):
        seq = self.script[int(oid[1:]) - 1]
        st = seq.pop(0) if len(seq) > 1 else seq[0]
        return OrderStatus(*st)

    async def cancel(self, oid):
        self.cancels.append(oid)
        seq = self.script[int(oid[1:]) - 1]
        last = seq[-1]
        seq[:] = [("canceled", last[1], last[2])]

    async def positions(self):
        return {}


def _exec_system(broker):
    cfg = make_cfg()
    cfg.broker.order_timeout_seconds = 0.6
    o = Orchestrator(cfg, db_path=":memory:", dashboard=False)
    o.ctx.broker = broker
    out = []
    for ty in (Fill, OrderFailed):
        o.bus.subscribe(ty, out.append, "t")
    chain = o.ctx.bots["options_chain"]
    chain.sim.spot["QQQ"] = 752.0
    chain.last_ts = cal.at(D, "10:00")
    return o, out


def _run_exec(o, intent):
    async def go():
        await o.bus.emit(OrderApproved(intent.ts, intent))
        await asyncio.gather(*o.ctx.bots["execution"]._tasks)
    asyncio.run(go())


def test_entry_partial_fill_then_timeout_cancel():
    broker = SlowBroker([[("new", 0, 0), ("partially_filled", 3, 3.68)]])
    o, out = _exec_system(broker)
    intent = OrderIntent(cal.at(D, "10:00"), "QQQ OG", C, OrderSide.BUY, 5, 3.68, Purpose.ENTRY, "vwap_cross")
    _run_exec(o, intent)
    assert broker.cancels == ["o1"]
    fill = next(e for e in out if isinstance(e, Fill))
    failed = next(e for e in out if isinstance(e, OrderFailed))
    assert fill.qty == 3 and fill.price == 3.68
    assert failed.filled_qty == 3                       # the 3 contracts we got are still tracked as a position
    assert o.ctx.bots["ledger"].holdings() == {C.occ: 3}


def test_exit_walks_price_down_then_goes_market():
    o_cfg = make_cfg()
    broker = SlowBroker([[("new", 0, 0)], [("new", 0, 0)], [("new", 0, 0)], [("filled", 5, 3.40)]])
    o, out = _exec_system(broker)
    q = o.ctx.bots["options_chain"].sim.quote(C, cal.at(D, "10:00"))
    intent = OrderIntent(cal.at(D, "10:00"), "QQQ OG", C, OrderSide.SELL, 5, q.bid, Purpose.EXIT, "stop")
    _run_exec(o, intent)
    limits = [s[2] for s in broker.submits]
    assert limits[:3] == [q.bid, round(q.bid - 0.01, 2), round(q.bid - 0.02, 2)]
    assert limits[3] is None                               # final attempt is a market order
    assert [e.qty for e in out if isinstance(e, Fill)] == [5]
    assert not [e for e in out if isinstance(e, OrderFailed)]


# ---------------------------------------------------------------- Alpaca market data
def test_alpaca_timestamp_parsing():
    from scalpcity.data.alpaca_data import parse_ts
    ts = parse_ts("2026-10-02T14:00:05.123456789Z")
    assert ts == cal.at(D, "10:00") + timedelta(seconds=5, microseconds=123456) and ts.tzinfo == cal.ET
    assert parse_ts("2026-10-02T14:00:00Z") == cal.at(D, "10:00")
    assert parse_ts("2026-10-02T10:00:00.5-04:00") == cal.at(D, "10:00") + timedelta(milliseconds=500)


def test_alpaca_data_requests(monkeypatch):
    from scalpcity.data.alpaca_data import AlpacaDataClient
    monkeypatch.setenv("ALPACA_API_KEY_ID", "k")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "s")
    seen = []
    snap = {"latestQuote": {"bp": 3.6, "ap": 3.68}, "greeks": {"delta": 0.52}, "impliedVolatility": 0.18}

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        assert req.headers["APCA-API-KEY-ID"] == "k" and req.headers["APCA-API-SECRET-KEY"] == "s"
        p = req.url.params
        if req.url.path == "/v2/stocks/QQQ/bars":
            if "page_token" not in p:
                return httpx.Response(200, json={"bars": [{"t": "2026-10-02T13:29:00Z", "o": 1, "h": 1, "l": 1,
                                                           "c": 1, "v": 1}], "next_page_token": "n1"})
            return httpx.Response(200, json={"bars": [{"t": "2026-10-02T13:30:00Z", "o": 1, "h": 2, "l": 0.5,
                                                       "c": 1.5, "v": 9}], "next_page_token": None})
        if req.url.path == "/v1beta1/options/snapshots/QQQ":
            return httpx.Response(200, json={"snapshots": {C.occ: snap, "QQQ261002C00753000": {"greeks": {}}},
                                             "next_page_token": None})
        if req.url.path == "/v1beta1/options/snapshots":
            return httpx.Response(200, json={"snapshots": {p["symbols"]: snap}})
        return httpx.Response(404, text="nope")

    async def go():
        c = AlpacaDataClient("iex", "indicative")
        c.http = httpx.AsyncClient(base_url="https://data.alpaca.markets", headers=c.http.headers,
                                   transport=httpx.MockTransport(handler))
        bars = await c.minute_bars("QQQ", D)
        chain = await c.chain("QQQ", D, Side.CALL, 752.0)
        q = await c.quote(C)
        await c.close()
        return bars, chain, q

    bars, chain, q = asyncio.run(go())
    assert [(b.start, b.close) for b in bars] == [(cal.at(D, "09:30"), 1.5)]   # pre-market dropped, page 2 followed
    assert seen[0].url.params["feed"] == "iex" and seen[0].url.params["timeframe"] == "1Min"
    cp = seen[2].url.params
    assert (cp["feed"], cp["type"], cp["expiration_date"]) == ("indicative", "call", "2026-10-02")
    assert float(cp["strike_price_gte"]) < 752 < float(cp["strike_price_lte"])
    assert len(chain) == 1                                                   # contract without a quote skipped
    assert chain[0].contract == C and chain[0].bid == 3.6 and chain[0].ask == 3.68 and chain[0].delta == 0.52
    assert chain[0].underlying_price == 752.0
    assert q.contract == C and q.ask == 3.68


def test_alpaca_stream_messages():
    from scalpcity.data.alpaca_data import AlpacaStream
    got = []

    async def on_trade(*a):
        got.append(a)

    s = AlpacaStream(["QQQ"], on_trade, "iex")
    assert s.url == "wss://stream.data.alpaca.markets/v2/iex"
    asyncio.run(s.handle(json.dumps([{"T": "success", "msg": "authenticated"},
                                     {"T": "t", "S": "QQQ", "p": 750.5, "s": 100, "t": "2026-10-02T14:00:05Z"}])))
    assert got == [("QQQ", cal.at(D, "10:00") + timedelta(seconds=5), 750.5, 100.0)]
    with pytest.raises(RuntimeError, match="402"):
        asyncio.run(s.handle(json.dumps([{"T": "error", "code": 402, "msg": "auth failed"}])))


def test_live_trade_becomes_tick():
    o = Orchestrator(make_cfg(), db_path=":memory:", dashboard=False)
    ticks = []
    o.bus.subscribe(Tick, ticks.append, "t")
    asyncio.run(o.feed._on_trade("QQQ", cal.at(D, "10:00"), 750.5, 100.0))
    assert [(t.symbol, t.price, t.size) for t in ticks] == [("QQQ", 750.5, 100.0)]


def test_live_client_follows_config(monkeypatch):
    from scalpcity.data.alpaca_data import AlpacaDataClient
    from scalpcity.data.live import live_client
    from scalpcity.data.polygon import PolygonClient
    monkeypatch.setenv("ALPACA_API_KEY_ID", "k")
    monkeypatch.setenv("ALPACA_API_SECRET_KEY", "s")
    monkeypatch.setenv("POLYGON_API_KEY", "p")
    cfg = make_cfg()
    cfg.data.alpaca_options_feed = "opra"
    c = live_client(cfg)
    assert isinstance(c, AlpacaDataClient) and c.options_feed == "opra" and c.stock_feed == "iex"
    cfg.data.live_data = "polygon"
    assert isinstance(live_client(cfg), PolygonClient)


def test_sip_requests_end_at_least_15_minutes_ago():
    from scalpcity.data.alpaca_data import sip_end
    now = cal.now_et()
    assert sip_end(now + timedelta(days=1)) <= now - timedelta(minutes=15)       # free plan: no recent SIP data
    old = now - timedelta(days=3)
    assert sip_end(old) == old
