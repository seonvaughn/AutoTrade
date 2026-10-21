"""Simulated broker: fills marketable orders immediately at the modeled bid/ask.

Buys pay the ask, sells receive the bid (you always cross the spread), plus
fees per contract. Non-marketable limit
orders are cancelled (IOC behaviour). Tracks cash and the pattern-day-trader
count like a real margin account. Futures (the futures city) can be long or short: they cost no premium, set aside
margin while open, and settle the profit or loss in cash when closed.
"""
from __future__ import annotations

import itertools
from collections import deque
from datetime import date
from typing import Callable, Optional

from ..core import calendar as cal
from ..core.costs import QTY_EPS, fees
from ..core.events import Instrument, OrderSide
from .base import Account, Broker, OrderStatus


class SimBroker(Broker):
    synchronous_fills = True

    def __init__(self, starting_cash: float, sim_cfg, quote_fn: Callable, today_fn: Callable[[], date]) -> None:
        self.cash = starting_cash
        self.sim = sim_cfg
        self.quote_fn = quote_fn
        self.today_fn = today_fn
        self.pos: dict[str, float] = {}
        self.contracts: dict[str, Instrument] = {}
        self.avg: dict[str, float] = {}         # futures: average entry price of the open (signed) position
        self.opened_on: dict[str, date] = {}
        self.day_trades: deque[date] = deque()
        self.orders: dict[str, OrderStatus] = {}
        self._ids = itertools.count(1)

    async def account(self) -> Account:
        equity, margin = self.cash, 0.0
        for occ, qty in self.pos.items():
            c = self.contracts[occ]
            q = self.quote_fn(c)
            if c.kind == "future":
                margin += c.margin * abs(qty)
                if q:
                    equity += (q.mid - self.avg[occ]) * qty * c.multiplier
            elif q:
                equity += q.mid * qty * c.multiplier
        today = self.today_fn()
        window = set()
        d = today
        for _ in range(5):
            window.add(d)
            d = cal.prev_trading_day(d)
        count = sum(1 for x in self.day_trades if x in window)
        return Account(equity, self.cash, self.cash - margin, count)

    async def submit(self, contract: Instrument, side: OrderSide, qty: float, limit: Optional[float]) -> str:
        oid = f"sim-{next(self._ids)}"
        q = self.quote_fn(contract)
        if q is None:
            self.orders[oid] = OrderStatus("rejected", 0, 0.0)
            return oid
        price = q.ask if side is OrderSide.BUY else q.bid
        marketable = limit is None or (price <= limit + 1e-9 if side is OrderSide.BUY else price >= limit - 1e-9)
        if not marketable or price <= 0:
            self.orders[oid] = OrderStatus("canceled", 0, 0.0)
            return oid
        if contract.kind == "future":
            return self._future(oid, contract, side, qty, price)
        held = self.pos.get(contract.occ, 0)
        if side is OrderSide.SELL:
            qty = min(qty, held)
            if qty <= QTY_EPS:
                self.orders[oid] = OrderStatus("rejected", 0, 0.0)
                return oid
        cost = price * qty * contract.multiplier
        fee = fees(contract, qty, price, self.sim)
        if side is OrderSide.BUY:
            if cost + fee > self.cash:
                self.orders[oid] = OrderStatus("rejected", 0, 0.0)
                return oid
            self.cash -= cost + fee
            self.pos[contract.occ] = held + qty
            self.contracts[contract.occ] = contract
            self.opened_on.setdefault(contract.occ, self.today_fn())
        else:
            self.cash += cost - fee
            self.pos[contract.occ] = held - qty
            if self.pos[contract.occ] <= QTY_EPS:
                del self.pos[contract.occ]
                if self.opened_on.pop(contract.occ, None) == self.today_fn():
                    self.day_trades.append(self.today_fn())
        self.orders[oid] = OrderStatus("filled", qty, price)
        return oid

    def _future(self, oid: str, c, side: OrderSide, qty: float, price: float) -> str:
        held = self.pos.get(c.occ, 0.0)
        signed = qty if side is OrderSide.BUY else -qty
        fee = fees(c, qty, price, self.sim)
        if held == 0 or (held > 0) == (signed > 0):          # opening or adding
            used = sum(self.contracts[k].margin * abs(v) for k, v in self.pos.items()
                       if self.contracts[k].kind == "future")
            if used + c.margin * qty + fee > self.cash:
                self.orders[oid] = OrderStatus("rejected", 0, 0.0)
                return oid
            self.avg[c.occ] = (self.avg.get(c.occ, 0.0) * abs(held) + price * qty) / (abs(held) + qty)
            self.cash -= fee
            self.opened_on.setdefault(c.occ, self.today_fn())
        else:                                                   # reducing or closing
            qty = min(qty, abs(held))
            signed = qty if side is OrderSide.BUY else -qty
            way = 1 if held > 0 else -1
            self.cash += way * (price - self.avg[c.occ]) * qty * c.multiplier - fee
        self.contracts[c.occ] = c
        self.pos[c.occ] = held + signed
        if abs(self.pos[c.occ]) <= QTY_EPS:
            del self.pos[c.occ]
            self.avg.pop(c.occ, None)
            if self.opened_on.pop(c.occ, None) == self.today_fn():
                self.day_trades.append(self.today_fn())
        self.orders[oid] = OrderStatus("filled", qty, price)
        return oid

    async def status(self, order_id: str) -> OrderStatus:
        return self.orders[order_id]

    async def cancel(self, order_id: str) -> None:
        st = self.orders.get(order_id)
        if st and not st.done:
            st.status = "canceled"

    async def positions(self) -> dict[str, float]:
        return dict(self.pos)
