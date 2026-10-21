"""Trading costs and quantity rules for option and futures contracts (whole contracts only)."""
from __future__ import annotations

import math

QTY_EPS = 1e-9   # quantities below this count as zero


def fees(contract, qty: float, price: float, sim) -> float:
    """Per contract: the options regulatory fee, or a future's broker + exchange fee (on the contract)."""
    if getattr(contract, "kind", "option") == "future":
        return round(contract.fee * qty, 4)
    return sim.fee_per_contract * qty


def round_qty(contract, qty: float) -> float:
    """Round an order size down to whole contracts."""
    return math.floor(qty + 1e-9)


def fmt_qty(qty: float) -> str:
    return f"{qty:g}"
