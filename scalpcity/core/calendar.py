"""Market calendar: US equities (regular hours only) or crypto (every day, midnight to midnight ET).

US: holidays are NYSE full closures; HALF_DAYS close at 13:00 ET. Live/paper mode
also cross-checks the broker's calendar at startup and warns on mismatch, so a
missing entry here is caught before it matters.

One process trades one market; the orchestrator calls set_market() from config.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

OPEN = time(9, 30)
CLOSE = time(16, 0)
HALF_CLOSE = time(13, 0)

HOLIDAYS = {
    # 2025
    date(2025, 1, 1), date(2025, 1, 9), date(2025, 1, 20), date(2025, 2, 17), date(2025, 4, 18),
    date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 4), date(2025, 9, 1), date(2025, 11, 27),
    date(2025, 12, 25),
    # 2026
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3), date(2026, 5, 25),
    date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7), date(2026, 11, 26), date(2026, 12, 25),
    # 2027
    date(2027, 1, 1), date(2027, 1, 18), date(2027, 2, 15), date(2027, 3, 26), date(2027, 5, 31),
    date(2027, 6, 18), date(2027, 7, 5), date(2027, 9, 6), date(2027, 11, 25), date(2027, 12, 24),
}

HALF_DAYS = {
    date(2025, 7, 3), date(2025, 11, 28), date(2025, 12, 24),
    date(2026, 11, 27), date(2026, 12, 24),
    date(2027, 11, 26),
}


MARKETS = ("options", "crypto")
_market = "options"


def set_market(market: str) -> None:
    global _market
    if market not in MARKETS:
        raise ValueError(f"market must be one of {MARKETS}")
    _market = market


def market() -> str:
    return _market


def is_crypto() -> bool:
    return _market == "crypto"


def now_et() -> datetime:
    return datetime.now(ET)


def is_trading_day(d: date) -> bool:
    if is_crypto():
        return True
    return d.weekday() < 5 and d not in HOLIDAYS


def next_trading_day(d: date, n: int = 1) -> date:
    """The n-th trading day after d (n=0 returns d itself if it trades)."""
    cur = d
    if n == 0:
        while not is_trading_day(cur):
            cur += timedelta(days=1)
        return cur
    for _ in range(n):
        cur += timedelta(days=1)
        while not is_trading_day(cur):
            cur += timedelta(days=1)
    return cur


def prev_trading_day(d: date) -> date:
    cur = d - timedelta(days=1)
    while not is_trading_day(cur):
        cur -= timedelta(days=1)
    return cur


def trading_days(start: date, end: date) -> list[date]:
    out, cur = [], start
    while cur <= end:
        if is_trading_day(cur):
            out.append(cur)
        cur += timedelta(days=1)
    return out


def session_open(d: date) -> datetime:
    if is_crypto():
        return datetime.combine(d, time(0, 0), ET)
    return datetime.combine(d, OPEN, ET)


def session_close(d: date) -> datetime:
    if is_crypto():
        return datetime.combine(d + timedelta(days=1), time(0, 0), ET)
    return datetime.combine(d, HALF_CLOSE if d in HALF_DAYS else CLOSE, ET)


def close_shift(d: date) -> timedelta:
    """How much earlier than normal the session closes (negative on US half days, else zero)."""
    if is_crypto():
        return timedelta(0)
    return session_close(d) - datetime.combine(d, CLOSE, ET)


def at(d: date, hhmm: str) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(d, time(h, m), ET)


def minutes_to_expiry(now: datetime, expiry: date) -> float:
    """Remaining *trading* minutes until the expiry session closes.

    Option variance accrues mostly while the market is open, so pricing intraday
    0DTE/1DTE options on trading time matches real premiums far better than
    calendar time.
    """
    total = 0.0
    d = now.date()
    while d <= expiry:
        if is_trading_day(d):
            o, c = session_open(d), session_close(d)
            start = max(o, now) if d == now.date() else o
            if c > start:
                total += (c - start).total_seconds() / 60.0
        d += timedelta(days=1)
    return total
