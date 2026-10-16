"""Polygon.io client: historical minute bars, real-time stream, option snapshots.

Env: POLYGON_API_KEY.  Endpoints used (Polygon REST v2/v3 + stocks WebSocket):
  GET  /v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}   stock & option minute bars
  GET  /v3/snapshot/options/{underlying}                     option chain w/ quotes + greeks
  GET  /v3/snapshot/options/{underlying}/{option_ticker}     single contract snapshot
  WSS  wss://socket.polygon.io/stocks  (A.<sym> = per-second aggregates)
Option quotes in snapshots require a Polygon Options plan that includes quotes.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime
from typing import Awaitable, Callable, Optional

import httpx

from ..core import calendar as cal
from ..core.events import Candle, OptionContract, OptionQuote, Side

log = logging.getLogger("scalpcity.polygon")

BASE = "https://api.polygon.io"
WS = {"realtime": "wss://socket.polygon.io/stocks", "delayed": "wss://delayed.polygon.io/stocks"}


def api_key() -> str:
    key = os.environ.get("POLYGON_API_KEY", "")
    if not key:
        raise RuntimeError("POLYGON_API_KEY is not set")
    return key


def _bars_from_results(symbol: str, results: list[dict], rth_only: bool = True) -> list[Candle]:
    out = []
    for r in results:
        start = datetime.fromtimestamp(r["t"] / 1000, tz=cal.ET)
        if rth_only and not (cal.session_open(start.date()) <= start < cal.session_close(start.date())):
            continue
        out.append(Candle(symbol, start, r["o"], r["h"], r["l"], r["c"], r.get("v", 0.0)))
    return out


def _quote_from_snapshot(r: dict, ts: datetime) -> Optional[OptionQuote]:
    det = r.get("details") or {}
    q = r.get("last_quote") or {}
    bid, ask = q.get("bid"), q.get("ask")
    if not det or bid is None or ask is None or ask <= 0:
        return None
    contract = OptionContract.from_occ(det["ticker"].removeprefix("O:"))
    greeks = r.get("greeks") or {}
    under = (r.get("underlying_asset") or {}).get("price")
    return OptionQuote(ts, contract, float(bid), float(ask), greeks.get("delta"), r.get("implied_volatility"), under)


class PolygonClient:
    """Async REST client (live/paper and data downloads)."""

    def __init__(self, key: Optional[str] = None) -> None:
        self.http = httpx.AsyncClient(base_url=BASE, timeout=15.0,
                                      headers={"Authorization": f"Bearer {key or api_key()}"})

    async def close(self) -> None:
        await self.http.aclose()

    async def _paged(self, path: str, params: dict) -> list[dict]:
        out: list[dict] = []
        r = await self.http.get(path, params=params)
        while True:
            r.raise_for_status()
            body = r.json()
            out.extend(body.get("results") or [])
            nxt = body.get("next_url")
            if not nxt:
                return out
            r = await self.http.get(nxt)

    async def minute_bars(self, ticker: str, day: date, rth_only: bool = True) -> list[Candle]:
        res = await self._paged(f"/v2/aggs/ticker/{ticker}/range/1/minute/{day}/{day}",
                                {"adjusted": "true", "sort": "asc", "limit": 50000})
        return _bars_from_results(ticker.removeprefix("O:"), res, rth_only)

    async def chain(self, underlying: str, expiry: date, right: Side, spot: float, width: float = 0.04) -> list[OptionQuote]:
        params = {"expiration_date": expiry.isoformat(), "contract_type": "call" if right is Side.CALL else "put",
                  "strike_price.gte": round(spot * (1 - width), 2), "strike_price.lte": round(spot * (1 + width), 2),
                  "limit": 250}
        res = await self._paged(f"/v3/snapshot/options/{underlying}", params)
        now = cal.now_et()
        return [q for q in (_quote_from_snapshot(r, now) for r in res) if q]

    async def quote(self, contract: OptionContract) -> Optional[OptionQuote]:
        r = await self.http.get(f"/v3/snapshot/options/{contract.underlying}/O:{contract.occ}")
        r.raise_for_status()
        return _quote_from_snapshot(r.json().get("results") or {}, cal.now_et())


class PolygonStream:
    """Real-time per-second aggregates -> callback(symbol, ts, o, h, l, c, v). Reconnects forever."""

    def __init__(self, symbols: list[str], on_agg: Callable[..., Awaitable[None]], feed: str = "realtime",
                 on_status: Optional[Callable[[str, str], Awaitable[None]]] = None) -> None:
        self.symbols, self.on_agg, self.url, self.on_status = symbols, on_agg, WS[feed], on_status

    async def run(self) -> None:
        import websockets

        backoff = 1.0
        while True:
            try:
                async with websockets.connect(self.url, ping_interval=20) as ws:
                    await ws.send(json.dumps({"action": "auth", "params": api_key()}))
                    await ws.send(json.dumps({"action": "subscribe",
                                              "params": ",".join(f"A.{s}" for s in self.symbols)}))
                    backoff = 1.0
                    if self.on_status:
                        await self.on_status("info", f"Polygon stream connected ({', '.join(self.symbols)})")
                    async for raw in ws:
                        for m in json.loads(raw):
                            ev = m.get("ev")
                            if ev == "A":
                                ts = datetime.fromtimestamp(m["e"] / 1000, tz=cal.ET)
                                await self.on_agg(m["sym"], ts, m["o"], m["h"], m["l"], m["c"], m.get("v", 0.0))
                            elif ev == "status" and m.get("status") in {"auth_failed", "error"}:
                                raise RuntimeError(f"Polygon: {m.get('message')}")
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                if self.on_status:
                    await self.on_status("critical", f"Polygon stream down: {exc}; retrying in {backoff:.0f}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
