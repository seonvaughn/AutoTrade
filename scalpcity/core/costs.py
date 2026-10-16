"""Trading costs and quantity rules that depend on the instrument (option contract or coin)."""
from __future__ import annotations

import math

QTY_EPS = 1e-9   # quantities below this count as zero (fractional coin arithmetic)
CRYPTO_QTY_DECIMALS = 6


def fees(contract, qty: float, price: float, sim) -> float:
    """Options: regulatory fee per contract. Crypto: a percentage of the fill's value."""
    if contract.kind == "crypto":
        return round(qty * price * sim.crypto_fee_pct / 100.0, 4)
    return sim.fee_per_contract * qty


def round_qty(contract, qty: float) -> float:
    """Round an order size down to what the broker accepts: whole contracts, or 6 decimals of a coin."""
    if contract.kind == "crypto":
        step = 10 ** CRYPTO_QTY_DECIMALS
        return math.floor(qty * step + 1e-6) / step
    return math.floor(qty + 1e-9)


def fmt_qty(qty: float) -> str:
    return f"{qty:g}" if qty >= 1 else f"{qty:.6f}".rstrip("0").rstrip(".")
