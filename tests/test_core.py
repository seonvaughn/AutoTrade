import asyncio
from datetime import date, datetime, timedelta

import pytest

from scalpcity.core import calendar as cal
from scalpcity.core.bus import EventBus
from scalpcity.core.config import Config, WorkerConfig, validate
from scalpcity.core.events import BotError, Heartbeat, OptionContract, Side, Tick
from scalpcity.core.options_math import bs_price


def test_occ_roundtrip():
    c = OptionContract("QQQ", date(2026, 10, 2), 752.0, Side.CALL)
    assert c.occ == "QQQ261002C00752000"
    assert OptionContract.from_occ(c.occ) == c
    p = OptionContract("SPY", date(2026, 10, 2), 772.5, Side.PUT)
    assert p.occ == "SPY261002P00772500"
    assert OptionContract.from_occ(p.occ) == p


def test_calendar_holidays_and_half_days():
    assert not cal.is_trading_day(date(2026, 11, 26))     # Thanksgiving
    assert cal.is_trading_day(date(2026, 11, 27))
    assert cal.session_close(date(2026, 11, 27)).hour == 13  # half day
    assert cal.next_trading_day(date(2026, 10, 2), 1) == date(2026, 10, 5)  # Fri -> Mon
    assert cal.next_trading_day(date(2026, 10, 2), 0) == date(2026, 10, 2)
    assert cal.prev_trading_day(date(2026, 1, 20)) == date(2026, 1, 16)    # skips MLK day


def test_minutes_to_expiry():
    t = cal.at(date(2026, 10, 2), "10:00")
    assert cal.minutes_to_expiry(t, date(2026, 10, 2)) == pytest.approx(360)
    assert cal.minutes_to_expiry(t, date(2026, 10, 5)) == pytest.approx(360 + 390)


def test_0dte_price_matches_video_scale():
    # QQQ ~752, ATM call, ~6h to close, 18% IV -> about $3-4 (the video filled at $3.68)
    px = bs_price(752.11, 752.0, 6.2 * 60, 0.18, True)
    assert 3.0 < px < 4.2


def test_bus_is_fifo_and_isolates_errors():
    bus = EventBus()
    seen = []
    t0 = datetime(2026, 10, 2, 10, tzinfo=cal.ET)

    def boom(e):
        raise RuntimeError("bad bot")

    def a(e):
        seen.append(("a", type(e).__name__))
        if isinstance(e, Tick):
            bus.publish(Heartbeat(e.ts))

    bus.subscribe(Tick, boom, "boom")
    bus.subscribe(Tick, a, "a")
    bus.subscribe(Heartbeat, lambda e: seen.append(("b", "Heartbeat")), "b")
    bus.subscribe(BotError, lambda e: seen.append(("err", e.bot)), "watch")
    asyncio.run(bus.emit(Tick(t0, "QQQ", 1.0)))
    # boom fails first, so its BotError is queued before the Heartbeat that `a` publishes
    assert seen == [("a", "Tick"), ("err", "boom"), ("b", "Heartbeat")]


def test_config_rejects_live_without_double_confirmation(monkeypatch):
    cfg = Config(mode="live", workers=[WorkerConfig("Q", "QQQ")])
    cfg.broker.name, cfg.data.source = "alpaca", "polygon"
    with pytest.raises(ValueError, match="live_trading_enabled"):
        validate(cfg)
    cfg.live_trading_enabled = True
    monkeypatch.delenv("SCALPCITY_LIVE_CONFIRM", raising=False)
    with pytest.raises(ValueError, match="SCALPCITY_LIVE_CONFIRM"):
        validate(cfg)


def test_config_rejects_unknown_trigger():
    with pytest.raises(ValueError, match="unknown triggers"):
        validate(Config(mode="backtest", workers=[WorkerConfig("Q", "QQQ", triggers=["macd"])]))


def test_replay_path_hits_every_extreme():
    from scalpcity.bots.price_feed_bot import PriceFeedBot
    from scalpcity.core.events import Candle
    c = Candle("QQQ", datetime(2026, 10, 2, 10, tzinfo=cal.ET), 100, 102, 99, 101, 1000)
    p = PriceFeedBot.path(c, 12)
    assert p[0] == 100 and p[-1] == 101 and max(p) == pytest.approx(102) and min(p) == pytest.approx(99)
    assert p.index(min(p)) < p.index(max(p))  # up bar: low before high
    flat = Candle("QQQ", c.start, 100, 100, 100, 100, 1)
    assert PriceFeedBot.path(flat, 12) == [100] * 12


def test_config_live_data_choices():
    cfg = Config(mode="paper", workers=[WorkerConfig("Q", "QQQ")])
    cfg.broker.name = "alpaca"
    validate(cfg)                                    # default: Alpaca data, free feeds
    d = cfg.data
    assert (d.live_data, d.alpaca_stock_feed, d.alpaca_options_feed) == ("alpaca", "iex", "indicative")
    cfg.data.alpaca_stock_feed = "nasdaq"
    with pytest.raises(ValueError, match="alpaca_stock_feed"):
        validate(cfg)
    cfg.data.alpaca_stock_feed, cfg.data.live_data = "iex", "yahoo"
    with pytest.raises(ValueError, match="live_data"):
        validate(cfg)
