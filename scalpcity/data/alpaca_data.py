"""Alpaca Market Data: minute bars, real-time trades, option snapshots (paper/live).

Env: ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY (the same keys the broker uses; paper keys work).
Endpoints used (Market Data API v2 / v1beta1):
  GET  /v2/stocks/{symbol}/bars?timeframe=1Min              stock minute bars (backfill)
  GET  /v1beta1/options/snapshots/{underlying}              option chain w/ quotes + greeks
  GET  /v1beta1/options/snapshots?symbols=...               single contract snapshot
  WSS  wss://stream.data.alpaca.markets/v2/{feed}           real-time trades (T=t)

Feeds: stocks "iex" (free, real-time, IEX exchange only) or "sip" (paid, all exchanges);
options "indicative" (free, derived from OPRA) or "opra" (paid, the real exchange quotes).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Awaitable, Callable, Optional

import httpx

from ..core import calendar as cal
from ..core.events import Candle, OptionContract, OptionQuote, Side

BASE = "https://data.alpaca.markets"
WS = "wss://stream.data.alpaca.markets/v2/{feed}"


def tls_context():
    """Certificates from certifi: python.org builds on macOS ship without trusted roots for the ssl module."""
    import ssl

    import certifi
    return ssl.create_default_context(cafile=certifi.where())


def keys() -> tuple[str, str]:
    key, secret = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY are not set")
    return key, secret


_TS = re.compile(r"^(.*?T\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)$")


def parse_ts(s: str) -> datetime:
    """RFC 3339 with up to nanosecond precision (Python 3.9's fromisoformat takes neither 'Z' nor 9 digits)."""
    m = _TS.match(s)
    if not m:
        raise ValueError(f"bad timestamp {s!r}")
    base, frac, tz = m.groups()
    ts = datetime.fromisoformat(base + ("." + (frac + "000000")[:6] if frac else "")
                                + ("+00:00" if tz == "Z" else tz))
    return ts.astimezone(cal.ET)


def _bars_from_results(symbol: str, results: list[dict], rth_only: bool = True) -> list[Candle]:
    out = []
    for r in results:
        start = parse_ts(r["t"])
        if rth_only and not (cal.session_open(start.date()) <= start < cal.session_close(start.date())):
            continue
        out.append(Candle(symbol, start, r["o"], r["h"], r["l"], r["c"], float(r.get("v", 0.0))))
    return out


def _quote_from_snapshot(occ: str, r: dict, ts: datetime, under: Optional[float] = None) -> Optional[OptionQuote]:
    q = r.get("latestQuote") or {}
    bid, ask = q.get("bp"), q.get("ap")
    if bid is None or ask is None or ask <= 0:
        return None
    contract = OptionContract.from_occ(occ)
    greeks = r.get("greeks") or {}
    return OptionQuote(ts, contract, float(bid), float(ask), greeks.get("delta"), r.get("impliedVolatility"), under)


class AlpacaDataClient:
    """Async REST client for paper/live. Same methods as PolygonClient."""

    def __init__(self, stock_feed: str = "iex", options_feed: str = "indicative") -> None:
        key, secret = keys()
        self.stock_feed, self.options_feed = stock_feed, options_feed
        self.http = httpx.AsyncClient(base_url=BASE, timeout=15.0,
                                      headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret})

    async def close(self) -> None:
        await self.http.aclose()

    async def _get(self, path: str, params: dict) -> httpx.Response:
        """GET with retry on 429 (the free plan allows ~200 requests a minute)."""
        for attempt in range(6):
            r = await self.http.get(path, params=params)
            if r.status_code != 429:
                break
            await asyncio.sleep(min(2 ** attempt, 30))
        if r.status_code >= 400:
            raise RuntimeError(f"Alpaca data GET {path} -> {r.status_code}: {r.text[:300]}")
        return r

    async def _paged(self, path: str, params: dict, key: str) -> list:
        """Follow next_page_token; returns the concatenated list (bars) or dict items (snapshots)."""
        out: list = []
        params = dict(params)
        while True:
            body = (await self._get(path, params)).json()
            page = body.get(key) or ([] if key == "bars" else {})
            out.extend(page if isinstance(page, list) else page.items())
            token = body.get("next_page_token")
            if not token:
                return out
            params["page_token"] = token

    async def minute_bars(self, ticker: str, day: date, rth_only: bool = True) -> list[Candle]:
        start = datetime.combine(day, datetime.min.time(), cal.ET)
        params = {"timeframe": "1Min", "start": start.isoformat(), "end": (start + timedelta(days=1)).isoformat(),
                  "feed": self.stock_feed, "adjustment": "raw", "sort": "asc", "limit": 10000}
        res = await self._paged(f"/v2/stocks/{ticker}/bars", params, "bars")
        return _bars_from_results(ticker, res, rth_only)

    async def chain(self, underlying: str, expiry: date, right: Side, spot: float, width: float = 0.04) -> list[OptionQuote]:
        params = {"feed": self.options_feed, "type": "call" if right is Side.CALL else "put",
                  "expiration_date": expiry.isoformat(),
                  "strike_price_gte": round(spot * (1 - width), 2), "strike_price_lte": round(spot * (1 + width), 2),
                  "limit": 1000}
        res = await self._paged(f"/v1beta1/options/snapshots/{underlying}", params, "snapshots")
        now = cal.now_et()
        return [q for q in (_quote_from_snapshot(occ, r, now, spot) for occ, r in res) if q]

    async def quote(self, contract) -> Optional[OptionQuote]:
        res = await self._paged("/v1beta1/options/snapshots", {"symbols": contract.occ, "feed": self.options_feed},
                                "snapshots")
        snap = dict(res).get(contract.occ)
        return _quote_from_snapshot(contract.occ, snap, cal.now_et()) if snap else None


class AlpacaStream:
    """Real-time trades -> callback(symbol, ts, price, size). Reconnects forever.

    The free plan allows one stream connection per account: don't run two copies of the bots at once."""

    def __init__(self, symbols: list[str], on_trade: Callable[..., Awaitable[None]], feed: str = "iex",
                 on_status: Optional[Callable[[str, str], Awaitable[None]]] = None) -> None:
        self.symbols, self.on_trade, self.feed, self.on_status = symbols, on_trade, feed, on_status
        self.url = WS.format(feed=feed)

    def subscription(self) -> dict:
        return {"action": "subscribe", "trades": self.symbols}

    async def handle(self, raw: str) -> None:
        for m in json.loads(raw):
            t = m.get("T")
            if t == "t":
                await self.on_trade(m["S"], parse_ts(m["t"]), float(m["p"]), float(m.get("s", 0)))
            elif t == "error":
                raise RuntimeError(f"Alpaca stream error {m.get('code')}: {m.get('msg')}")

    async def run(self) -> None:
        import websockets

        key, secret = keys()
        backoff = 1.0
        while True:
            try:
                async with websockets.connect(self.url, ping_interval=20, ssl=tls_context()) as ws:
                    await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
                    await ws.send(json.dumps(self.subscription()))
                    backoff = 1.0
                    if self.on_status:
                        await self.on_status("info", f"Alpaca {self.feed} stream connected ({', '.join(self.symbols)})")
                    async for raw in ws:
                        await self.handle(raw)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                if self.on_status:
                    await self.on_status("critical", f"Alpaca stream down: {exc}; retrying in {backoff:.0f}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
