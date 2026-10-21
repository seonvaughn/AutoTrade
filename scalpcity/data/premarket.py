"""Pre-market high and low per day (04:00-09:30 ET), from Alpaca 5-minute bars, cached as JSON per symbol.

Used by the no-trading zone (docs/videos/boring-orb-ntz.md). Only known once the session opens, so a day's range is
never used before 09:30 of that day.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from ..core import calendar as cal

log = logging.getLogger("scalpcity.premarket")


def _path(cache_dir: str, symbol: str) -> Path:
    return Path(cache_dir) / f"premarket-{symbol.replace('/', '-')}.json"


async def _fetch(symbol: str, start: date, end: date) -> dict[str, list[float]]:
    from .alpaca_data import AlpacaDataClient, parse_ts, sip_end
    client = AlpacaDataClient(stock_feed="sip")
    out: dict[str, list[float]] = {}
    try:
        params = {"timeframe": "5Min", "start": datetime.combine(start, datetime.min.time(), cal.ET).isoformat(),
                  "end": sip_end(datetime.combine(end + timedelta(days=1), datetime.min.time(), cal.ET)).isoformat(),
                  "limit": 10000, "sort": "asc", "feed": "sip", "adjustment": "split"}
        while True:
            body = (await client._get(f"/v2/stocks/{symbol}/bars", params)).json()
            for r in body.get("bars") or []:
                ts = parse_ts(r["t"])
                if ts >= cal.session_open(ts.date()):
                    continue
                d = ts.date().isoformat()
                hi_lo = out.setdefault(d, [r["h"], r["l"]])
                hi_lo[0], hi_lo[1] = max(hi_lo[0], r["h"]), min(hi_lo[1], r["l"])
            if not body.get("next_page_token"):
                break
            params["page_token"] = body["next_page_token"]
    finally:
        await client.close()
    return out


async def load_premarket(symbols: list[str], start: date, end: date, source: str,
                         cache_dir: str) -> dict[str, dict[str, list[float]]]:
    """{symbol: {"YYYY-MM-DD": [high, low]}} for [start, end]. Empty for synthetic/csv sources."""
    if source not in ("alpaca", "polygon"):
        return {}
    out: dict[str, dict[str, list[float]]] = {}
    for s in symbols:
        path = _path(cache_dir, s)
        have = json.loads(path.read_text()) if path.exists() else {}
        days = [d.isoformat() for d in cal.trading_days(start, end)]
        missing = [d for d in days if d not in have]
        if missing:
            try:
                have.update(await _fetch(s, date.fromisoformat(missing[0]), date.fromisoformat(missing[-1])))
                for d in missing:
                    have.setdefault(d, None)   # fetched but no pre-market trading: don't ask again
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(have))
            except Exception as exc:  # noqa: BLE001 - the NTZ trigger stands down without pre-market data
                log.warning("pre-market %s: %s", s, exc)
        out[s] = {d: v for d, v in have.items() if v}
    return out
