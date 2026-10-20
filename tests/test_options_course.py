"""Rules from the options course (docs/options-course/README.md): mid-price entries, position delta cap, the pick's
break-even / delta / time decay note."""
from scalpcity.core import calendar as cal
from scalpcity.core.events import (Fill, OptionContract, OptionQuote, OrderIntent, OrderRejected, OrderSide, Purpose,
                                   Side, Signal)
from tests.test_bots import D, _open_session, collect, run, system, t


def _sig(close=100.0):
    return Signal(t("10:00"), "QQQ", "smc_retrace", Side.CALL, close, 99.5, 0.5, stop=99.0, target=102.0)


def _quote(con, bid=2.00, ask=2.20, delta=0.70):
    return OptionQuote(t("10:00"), con, bid, ask, delta, 0.25, 100.0)


def _stub_quote(o, q):
    async def quote(contract):
        return q
    o.ctx.bots["options_chain"].quote = quote


def test_selection_note_gives_break_even_delta_and_decay():
    o = system()
    con = OptionContract("QQQ", cal.next_trading_day(D, 1), 100, Side.CALL)
    note = o.ctx.bots["contract_selector"].explain(_quote(con), _sig())
    assert "break-even $102.20" in note and "+2.20%" in note
    assert "≈70% chance ITM" in note and "per hour" in note


def test_risk_caps_position_delta_against_equity():
    o = system(mute=("health", "execution"))
    o.cfg.risk.max_delta_leverage = 5                          # 5 × $30k equity = $150k of stock
    rejected = collect(o, OrderRejected)
    con = OptionContract("QQQ", D, 100, Side.CALL)
    _stub_quote(o, _quote(con, delta=0.70))
    _open_session(o)
    big = OrderIntent(t("10:00"), "QQQ OG", con, OrderSide.BUY, 25, 2.2, Purpose.ENTRY, "x", _sig())
    run(o, big)                                                # 0.70 × 25 × 100 × $100 = $175k
    assert "position delta" in rejected[-1].reason
    small = OrderIntent(t("10:00"), "QQQ OG", con, OrderSide.BUY, 10, 2.2, Purpose.ENTRY, "x", _sig())
    n = len(rejected)
    run(o, small)                                              # $70k: fine
    assert len(rejected) == n


def test_entry_tries_the_mid_first_and_the_simulator_still_fills_at_the_ask():
    o = system()
    fills = collect(o, Fill)
    sent = []
    broker = o.ctx.broker
    submit = broker.submit

    async def spy(contract, side, qty, limit):
        sent.append(limit)
        return await submit(contract, side, qty, limit)
    broker.submit = spy
    con = OptionContract("QQQ", D, 100, Side.CALL)
    _stub_quote(o, _quote(con))
    broker.quote_fn = lambda c: _quote(con)
    _open_session(o)
    run(o, OrderIntent(t("10:00"), "QQQ OG", con, OrderSide.BUY, 1, 2.2, Purpose.ENTRY, "x", _sig()))
    assert sent == [2.10, 2.2]                                 # mid, then the ask
    assert fills and fills[0].price == 2.20
