"""Interactive Brokers broker for the futures city (PAPER only): day orders on the front-month micro futures.

Positions are reported signed (short = negative) by exchange symbol (MESZ6), the same keys the ledger uses, so the
reconciliation bot compares like with like. Only futures positions count: anything else in the account isn't ours.
"""
from __future__ import annotations

from typing import Optional

from ..core.events import OrderSide
from ..core.futures import round_tick
from .base import Account, Broker, OrderStatus
from .ibkr_conn import connect, ib_contract

STATUS = {"Filled": "filled", "Cancelled": "canceled", "ApiCancelled": "canceled", "Inactive": "rejected",
          "PendingCancel": "open", "PreSubmitted": "open", "Submitted": "open", "PendingSubmit": "open",
          "ApiPending": "open"}


class IBKRBroker(Broker):
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.trades: dict[str, object] = {}
        self.qualified: dict[str, object] = {}

    async def _ib(self):
        return await connect(self.cfg)

    async def _contract(self, c):
        if c.occ not in self.qualified:
            ib = await self._ib()
            got = await ib.qualifyContractsAsync(ib_contract(c))
            if not got or got[0] is None:
                raise RuntimeError(f"Interactive Brokers doesn't know {c.occ}")
            self.qualified[c.occ] = got[0]
        return self.qualified[c.occ]

    async def account(self) -> Account:
        ib = await self._ib()
        vals = {v.tag: v.value for v in await ib.accountSummaryAsync() if v.currency in ("USD", "")}

        def num(tag, default=0.0):
            try:
                return float(vals.get(tag, default))
            except (TypeError, ValueError):
                return default
        equity = num("NetLiquidation")
        # options_buying_power carries what the account can still commit: IB's available funds
        return Account(equity=equity, cash=num("TotalCashValue", equity),
                       options_buying_power=num("AvailableFunds", equity), daytrade_count=0)

    async def submit(self, contract, side: OrderSide, qty: float, limit: Optional[float]) -> str:
        from ib_async import LimitOrder, MarketOrder
        ib = await self._ib()
        ibc = await self._contract(contract)
        action = "BUY" if side is OrderSide.BUY else "SELL"
        order = MarketOrder(action, int(qty)) if limit is None else \
            LimitOrder(action, int(qty), round_tick(limit, contract.tick))
        order.tif = "DAY"
        trade = ib.placeOrder(ibc, order)
        oid = str(trade.order.orderId)
        self.trades[oid] = trade
        return oid

    async def status(self, order_id: str) -> OrderStatus:
        t = self.trades[order_id]
        s = t.orderStatus
        st = STATUS.get(s.status, "open")
        filled = int(round(float(s.filled or 0)))
        if st == "open" and filled:
            st = "partially_filled"
        return OrderStatus(st, filled, float(s.avgFillPrice or 0))

    async def cancel(self, order_id: str) -> None:
        t = self.trades.get(order_id)
        if t is not None and STATUS.get(t.orderStatus.status, "open") == "open":
            (await self._ib()).cancelOrder(t.order)

    async def positions(self) -> dict[str, float]:
        ib = await self._ib()
        out: dict[str, float] = {}
        for p in ib.positions():
            if p.contract.secType == "FUT" and p.position:
                out[p.contract.localSymbol] = out.get(p.contract.localSymbol, 0) + int(p.position)
        return out

    async def close(self) -> None:
        return None              # the shared connection stays up for the data feed; it closes with the process
