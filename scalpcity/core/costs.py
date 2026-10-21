"""Trading costs and quantity rules for option contracts."""
from __future__ import annotations

import math

QTY_EPS = 1e-9   # quantities below this count as zero


def fees(contract, qty: float, price: float, sim) -> float:
    """Regulatory fee per contract."""
    return sim.fee_per_contract * qty


def round_qty(contract, qty: float) -> float:
    """Round an order size down to whole contracts."""
    return math.floor(qty + 1e-9)


def fmt_qty(qty: float) -> str:
    return f"{qty:g}"
