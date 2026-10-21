"""Stand-in history for the futures city: each micro future replayed from its ETF's real minute bars, scaled.

There is no futures history in the cloud session (Alpaca and the free Polygon plan have none), so backtests use
SPY for MES, QQQ for MNQ and GLD for MGC, multiplied by the price ratio in core/futures.py SPECS and rounded to the
future's tick. This is an approximation: the real future trades nearly 24 hours, carries a basis to its ETF that
drifts, and has its own volume. Results say how the rules behave on that price path, not what the future earned.
Live paper trading uses the real contract prices from Interactive Brokers.
"""
from __future__ import annotations

from datetime import date

from ..core.events import Candle
from ..core.futures import round_tick, spec
from .bars import BarLoader


def _scale(c: Candle, root: str, ratio: float, tick: float) -> Candle:
    return Candle(root, c.start, round_tick(c.open * ratio, tick), round_tick(c.high * ratio, tick),
                  round_tick(c.low * ratio, tick), round_tick(c.close * ratio, tick), c.volume)


class ProxyBarLoader:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.inner = BarLoader("alpaca", cfg.data.csv_dir)

    def load(self, root: str, day: date) -> list[Candle]:
        s = spec(self.cfg, root)
        return [_scale(b, root, s["ratio"], s["tick"]) for b in self.inner.load(s["proxy"], day)]


async def proxy_daily(cfg, start: date, end: date) -> dict[str, list[Candle]]:
    from .daily import load_daily
    out = {}
    for root in cfg.symbols:
        s = spec(cfg, root)
        got = await load_daily([s["proxy"]], start, end, "alpaca", cfg.data.daily_dir)
        out[root] = [_scale(b, root, s["ratio"], s["tick"]) for b in got.get(s["proxy"], [])]
    return out


async def proxy_premarket(cfg, start: date, end: date) -> dict[str, dict[str, list[float]]]:
    from .premarket import load_premarket
    out = {}
    for root in cfg.symbols:
        s = spec(cfg, root)
        got = await load_premarket([s["proxy"]], start, end, "alpaca", cfg.data.daily_dir)
        out[root] = {d: [round_tick(hi * s["ratio"], s["tick"]), round_tick(lo * s["ratio"], s["tick"])]
                     for d, (hi, lo) in got.get(s["proxy"], {}).items()}
    return out


async def futures_daily(cfg, start: date, end: date, live: bool) -> dict[str, list[Candle]]:
    """Daily candles for the futures city: the real contracts from Interactive Brokers when live, else the ETF
    stand-ins."""
    if live:
        from .ibkr_data import ib_daily
        return await ib_daily(cfg, start, end)
    if cfg.data.source == "proxy":
        return await proxy_daily(cfg, start, end)
    return {}


async def futures_premarket(cfg, start: date, end: date, live: bool) -> dict[str, dict[str, list[float]]]:
    """Pre-market (04:00-09:30 ET) high and low per day: from the real contracts live, else the ETF stand-ins."""
    if live:
        from .ibkr_data import ib_premarket
        return await ib_premarket(cfg, start, end)
    if cfg.data.source == "proxy":
        return await proxy_premarket(cfg, start, end)
    return {}
