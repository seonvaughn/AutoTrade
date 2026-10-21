"""Alpaca Trading API v2 (options) — paper or live.

Env: ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY.
The account needs options approval (level 2+ to buy calls/puts); orders are time_in_force=day,
qty in whole contracts. Only option positions count: anything else the account holds is not ours.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

import httpx

from ..core.events import Instrument, OrderSide
from .base import Account, Broker, OrderStatus

URLS = {"paper": "https://paper-api.alpaca.markets", "live": "https://api.alpaca.markets"}


class AlpacaBroker(Broker):
    def __init__(self, env: str) -> None:
        key, secret = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
        if not key or not secret:
            raise RuntimeError("ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY are not set")
        self.env = env
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
                       cash_account=str(a.get("multiplier", "1")) == "1")

    async def submit(self, contract: Instrument, side: OrderSide, qty: float, limit: Optional[float]) -> str:
        body = {"symbol": contract.order_symbol, "side": side.value, "qty": str(int(qty)),
                "time_in_force": "day", "type": "market" if limit is None else "limit"}
        if limit is not None:
            body["limit_price"] = f"{limit:.2f}"
        return (await self._req("POST", "/v2/orders", json=body)).json()["id"]

    async def status(self, order_id: str) -> OrderStatus:
        o = (await self._req("GET", f"/v2/orders/{order_id}")).json()
        filled = int(round(float(o.get("filled_qty") or 0)))
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
        return out

    async def calendar(self, start: date, end: date) -> list[str]:
        rows = (await self._req("GET", "/v2/calendar", params={"start": str(start), "end": str(end)})).json()
        return [r["date"] for r in rows]

    async def close(self) -> None:
        await self.http.aclose()
