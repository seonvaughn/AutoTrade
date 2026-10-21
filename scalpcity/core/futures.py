"""Futures contract specs and the front month: which contract month to trade on a given day.

Micro E-mini S&P (MES) and Micro E-mini Nasdaq (MNQ) list March, June, September and December and expire on the
third Friday of the month; volume moves to the next month about a week before, so the bots roll 8 days early.
Micro Gold (MGC) trades every month but the liquid ones are Feb, Apr, Jun, Aug, Oct and Dec; trading ends three
business days before the end of the month before the contract month, and traders leave before first notice, so the
bots roll on the 15th of that month. Specs can be overridden per root in config (`futures:`).
"""
from __future__ import annotations

from datetime import date, timedelta

from . import calendar as cal
from .events import FuturesContract, Side

SPECS: dict[str, dict] = {
    # multiplier $/point, tick, liquid months, fee per contract per side (IBKR tiered, approximate),
    # margin per contract (approximate; the broker's figure is what counts live), proxy ETF and price ratio for
    # backtests without futures history (an ETF move times the ratio ~ the future's move)
    "MES": {"multiplier": 5.0, "tick": 0.25, "months": "HMUZ", "fee": 0.62, "margin": 2700.0,
            "proxy": "SPY", "ratio": 10.0, "name": "Micro E-mini S&P 500"},
    "MNQ": {"multiplier": 2.0, "tick": 0.25, "months": "HMUZ", "fee": 0.62, "margin": 3500.0,
            "proxy": "QQQ", "ratio": 41.0, "name": "Micro E-mini Nasdaq-100"},
    "MGC": {"multiplier": 10.0, "tick": 0.10, "months": "GJMQVZ", "fee": 0.82, "margin": 3000.0,
            "proxy": "GLD", "ratio": 10.85, "name": "Micro Gold"},
}
CODES = "FGHJKMNQUVXZ"


def spec(cfg, root: str) -> dict:
    s = dict(SPECS.get(root, {}))
    s.update((getattr(cfg, "futures", None) or {}).get(root, {}))
    return s


def third_friday(year: int, month: int) -> date:
    d = date(year, month, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def last_trading_day(root: str, year: int, month: int) -> date:
    if root in ("MGC", "GC"):
        prev = date(year, month, 1) - timedelta(days=1)          # last day of the month before
        days = [d for d in cal.trading_days(prev.replace(day=1), prev)]
        return days[-3] if len(days) >= 3 else prev
    d = third_friday(year, month)
    while not cal.is_trading_day(d):
        d -= timedelta(days=1)
    return d


def roll_day(root: str, year: int, month: int) -> date:
    """The first day the bots trade the next contract instead of this one."""
    if root in ("MGC", "GC"):
        prev = date(year, month, 1) - timedelta(days=1)
        return prev.replace(day=15)
    return last_trading_day(root, year, month) - timedelta(days=8)


def front_month(cfg, root: str, day: date, side: Side) -> FuturesContract:
    s = spec(cfg, root)
    months = [CODES.index(c) + 1 for c in s.get("months", "HMUZ")]
    for year in (day.year, day.year + 1, day.year + 2):
        for m in months:
            if day < roll_day(root, year, m):
                return FuturesContract(root, last_trading_day(root, year, m), side, float(s["multiplier"]),
                                       float(s["tick"]), float(s["fee"]), float(s["margin"]), date(year, m, 1))
    raise ValueError(f"no contract month for {root} after {day}")


def round_tick(price: float, tick: float) -> float:
    return round(round(price / tick) * tick, 6)
