"""Daily candles for the higher-timeframe study (day, week, month, year), cached as CSV.

Stocks come from Alpaca (split-adjusted, all exchanges) or Polygon; coins from Alpaca crypto.
Callers must only look at days *before* the session being traded (no look-ahead); this module
just fetches and caches.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from ..core import calendar as cal
from ..core.events import Candle, is_crypto_symbol
from .bars import read_csv, write_csv

log = logging.getLogger("scalpcity.daily")


def _path(cache_dir: str, symbol: str) -> Path:
    return Path(cache_dir) / f"{symbol.replace('/', '-')}.csv"


def _day_candle(symbol: str, d: date, o, h, low, c, v) -> Candle:
    return Candle(symbol, datetime.combine(d, datetime.min.time(), cal.ET), float(o), float(h), float(low),
                  float(c), float(v or 0))


async def _fetch_alpaca(symbol: str, start: date, end: date) -> list[Candle]:
    from .alpaca_data import AlpacaDataClient, parse_ts
    client = AlpacaDataClient(stock_feed="sip")
    try:
        params = {"timeframe": "1Day", "start": start.isoformat(), "end": (end + timedelta(days=1)).isoformat(),
                  "limit": 10000, "sort": "asc"}
        if is_crypto_symbol(symbol):
            path, key = "/v1beta3/crypto/us/bars", symbol
            params["symbols"] = symbol
        else:
            path, key = f"/v2/stocks/{symbol}/bars", None
            params.update(feed="sip", adjustment="split")
        rows: list[dict] = []
        while True:
            body = (await client._get(path, params)).json()
            page = body.get("bars") or ([] if key is None else {})
            rows += page.get(key, []) if key else page
            if not body.get("next_page_token"):
                break
            params["page_token"] = body["next_page_token"]
    finally:
        await client.close()
    return [_day_candle(symbol, parse_ts(r["t"]).date(), r["o"], r["h"], r["l"], r["c"], r.get("v")) for r in rows]


async def _fetch_polygon(symbol: str, start: date, end: date) -> list[Candle]:
    from .polygon import PolygonClient
    client = PolygonClient()
    try:
        res = await client._paged(f"/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}",
                                  {"adjusted": "true", "sort": "asc", "limit": 50000})
    finally:
        await client.close()
    return [_day_candle(symbol, datetime.fromtimestamp(r["t"] / 1000, tz=cal.ET).date(),
                        r["o"], r["h"], r["l"], r["c"], r.get("v")) for r in res]


async def load_daily(symbols: list[str], start: date, end: date, source: str, cache_dir: str) -> dict[str, list[Candle]]:
    """Daily candles for [start, end] per symbol. Empty for synthetic/csv sources (no real history)."""
    if source not in ("alpaca", "polygon"):
        return {}
    out: dict[str, list[Candle]] = {}
    for s in symbols:
        path = _path(cache_dir, s)
        bars = read_csv(path, s) if path.exists() else []
        have = (bars[0].start.date(), bars[-1].start.date()) if bars else None
        if not have or have[0] > start + timedelta(days=7) or have[1] < end - timedelta(days=4):
            try:
                fetch = _fetch_alpaca if source == "alpaca" or is_crypto_symbol(s) else _fetch_polygon
                bars = await fetch(s, start, end)
                write_csv(path, bars)
            except Exception as exc:  # noqa: BLE001 - the study degrades gracefully without daily data
                log.warning("daily candles for %s unavailable (%s); higher-timeframe study skipped", s, exc)
                bars = bars or []
        out[s] = [b for b in bars if start <= b.start.date() <= end]
    return out
