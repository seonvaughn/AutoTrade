"""Black-Scholes pricing used by the simulator / backtester.

Time is measured in trading minutes (252 days x 390 min per year), see
calendar.minutes_to_expiry for why.
"""
from __future__ import annotations

import math

TRADING_MINUTES_PER_YEAR = 252 * 390


def _ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_price(spot: float, strike: float, minutes: float, iv: float, is_call: bool, rate: float = 0.04) -> float:
    t = max(minutes, 1.0) / TRADING_MINUTES_PER_YEAR
    if iv <= 0:
        intrinsic = spot - strike if is_call else strike - spot
        return max(intrinsic, 0.0)
    vs = iv * math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate + 0.5 * iv * iv) * t) / vs
    d2 = d1 - vs
    disc = math.exp(-rate * t)
    if is_call:
        return spot * _ncdf(d1) - strike * disc * _ncdf(d2)
    return strike * disc * _ncdf(-d2) - spot * _ncdf(-d1)


def bs_delta(spot: float, strike: float, minutes: float, iv: float, is_call: bool, rate: float = 0.04) -> float:
    t = max(minutes, 1.0) / TRADING_MINUTES_PER_YEAR
    vs = iv * math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate + 0.5 * iv * iv) * t) / vs
    return _ncdf(d1) if is_call else _ncdf(d1) - 1.0


def round_tick(price: float) -> float:
    """Options under $3 trade in $0.01 for penny-pilot names (SPY/QQQ/IWM: all pennies)."""
    return max(0.01, round(price + 1e-9, 2))
