"""Alpaca Trading API v2 (options and crypto) — paper or live.

Env: ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY.
Options: the account needs options approval (level 2+ to buy calls/puts); orders are
time_in_force=day, qty in whole contracts.
Crypto: orders are time_in_force=gtc, qty fractional. Alpaca takes the trading fee out of
the coin you receive, so a sell of the whole position sells what the account really holds.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

import httpx

from ..core.costs import fmt_qty
from ..core.events import Instrument, OrderSide
from .base import Account, Broker, OrderStatus

URLS = {"paper": "https://paper-api.alpaca.markets", "live": "https://api.alpaca.markets"}


class AlpacaBroker(Broker):
    def __init__(self, env: str) -> None:
        key, secret = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
        if not key or not secret:
            raise RuntimeError("ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY are not set")
        self.env = env
        self.scale: dict[str, float] = {}  # order id -> reported qty / sent qty (crypto full-position sells)
        self.http = httpx.AsyncClient(base_url=URLS[env], timeout=10.0,
                                      headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret})

    async def _req(self, method: str, path: str, **kw) -> httpx.Response:
        r = await self.http.request(method, path, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"Alpaca {method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    async def account(self) -> Account:
        a = (await self._req("GET", "/v2/account")).json()
        bp = a.get("options_buying_power") or a.get("buying_power") or a.get("cash")
        return Account(equity=float(a["equity"]), cash=float(a["cash"]), options_buying_power=float(bp),
                       daytrade_count=int(a.get("daytrade_count", 0)),
                       pattern_day_trader=bool(a.get("pattern_day_trader")),
                       cash_account=str(a.get("multiplier", "1")) == "1",
                       non_marginable_buying_power=float(a.get("non_marginable_buying_power") or a["cash"]))

    async def submit(self, contract: Instrument, side: OrderSide, qty: float, limit: Optional[float]) -> str:
        crypto = contract.kind == "crypto"
        sent = qty
        if crypto and side is OrderSide.SELL:
            held = (await self.positions()).get(contract.occ, 0.0)
            if held > 0 and held < qty * 1.02:  # selling the whole position: sell what is really there
                sent = held
        body = {"symbol": contract.order_symbol, "side": side.value,
                "qty": fmt_qty(sent) if crypto else str(int(sent)),
                "time_in_force": "gtc" if crypto else "day", "type": "market" if limit is None else "limit"}
        if limit is not None:
            body["limit_price"] = _price(limit) if crypto else f"{limit:.2f}"
        oid = (await self._req("POST", "/v2/orders", json=body)).json()["id"]
        if sent != qty:
            self.scale[oid] = qty / sent
        return oid

    async def status(self, order_id: str) -> OrderStatus:
        o = (await self._req("GET", f"/v2/orders/{order_id}")).json()
        filled = float(o.get("filled_qty") or 0) * self.scale.get(order_id, 1.0)
        if o.get("asset_class", "us_option") != "crypto":
            filled = int(round(filled))
        return OrderStatus(o["status"], filled, float(o.get("filled_avg_price") or 0))

    async def cancel(self, order_id: str) -> None:
        r = await self.http.delete(f"/v2/orders/{order_id}")
        if r.status_code not in (200, 204, 404, 422):  # 422: already filled/cancelled
            raise RuntimeError(f"Alpaca cancel {order_id} -> {r.status_code}: {r.text[:200]}")

    async def positions(self) -> dict[str, float]:
        rows = (await self._req("GET", "/v2/positions")).json()
        out: dict[str, float] = {}
        for p in rows:
            if p.get("asset_class") == "us_option":
                out[p["symbol"]] = int(float(p["qty"]))
            elif p.get("asset_class") == "crypto":
                out[p["symbol"].replace("/", "")] = float(p["qty"])
        return out

    async def calendar(self, start: date, end: date) -> list[str]:
        rows = (await self._req("GET", "/v2/calendar", params={"start": str(start), "end": str(end)})).json()
        return [r["date"] for r in rows]

    async def close(self) -> None:
        await self.http.aclose()


def _price(x: float) -> str:
    """Crypto limit price: cents above $1, more precision for cheap coins."""
    return f"{x:.2f}" if x >= 1 else f"{x:.6f}"
